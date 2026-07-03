import os
import asyncio
from pathlib import Path

from google import genai
from google.genai import types

from apps.settings import get_auth_settings

import logging

logger = logging.getLogger(__name__)

# create genai client to be reused 
client = None
initial_delay_seconds = 5
max_attempts = 3

model_name = "gemini-3.1-flash-lite" # "gemini-2.5-flash"
system_instruction = """
You are a strict code-review agent. Analyze user snippets for efficiency and security.
Always respond using the following XML structure:
<thought>
Your internal reasoning about the code's flaws.
</thought>
<review>
Your bulleted feedback or refactored suggestion.
</review>
"""
# literal for end of the input when enetered through the console
end_of_code = "END"
# maximum number of lines for the input - prevents infinite loop
max_lines = 1000

async def agent_result(user_input: str) -> str:
    """
    Review code provided by user and suggest improvements

    Args:
        user_input: code or file path provided by user along with instruction for reviewing
    """

    # Marker to indicate if agent is ready with the final response or need additional requests
    agent_not_done = True
    
    messages = []

    functions = {
        "read_local_file": read_local_file,
        "save_local_file": save_local_file,
    }

    add_message("user", user_input, messages)

    while agent_not_done:

        logger.info(telemetry(messages))

        # Initial request to model
        try:
            response = get_client().models.generate_content(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    tools=[read_local_file, save_local_file],
                    # automatic function calling is disabled to keep control over the workflow
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
                contents=messages
            )
        except Exception as e:
            err_msg = f"Error by generate_content: {str(e)}"
            logger.error(err_msg)
            return err_msg

        # Check if the model wants to call a function
        if response.function_calls:
            
            # append the model's call to history
            messages.append(response.candidates[0].content)
            logger.debug(f"Model's call: {response.candidates[0].content}")

            for call in response.function_calls:
                logger.info(f"Model wants to call tool: {call.name} with args: {call.args}")

                if call.name in functions:

                    # call function with the arguments provided by the model                
                    if call.name in functions:
                        try:
                            logger.debug(f"Invoking {call.name} dynamically...")
                            tool_result = functions[call.name](**call.args)
                        except TypeError as e:
                            tool_result = f"Error: Invalid tool arguments passed by model. {str(e)}"

                    if tool_result[:5] == "Error":
                        logger.error(tool_result)
                    elif call.name == "read_local_file":
                        logger.debug(f"Successfully read local file. Length: {len(tool_result)} chars.")
                    elif call.name == "save_local_file":
                        logger.debug(tool_result)
                    
                    # Append the tool results to history under the "user" role
                    messages.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part(
                                    function_response=types.FunctionResponse(
                                        name=call.name,
                                        response={"result": tool_result}
                                    )
                                )
                            ]
                        )
                    )
                    logger.info("Tool result added to history. Re-routing turn back to agent...")
                else:
                    logger.error(f"Called function {call.name} does not exist.")
                    
        else:
            # No more function calls! The model is finally ready to return text to the user.
            logger.debug(f"Model response: {response.text}")
            add_message("model", response.text, messages)

            logger.debug(f"Last telemetry: {telemetry(messages)}")
            # Break the requests loop
            agent_not_done = False

    return messages[-1].parts[0].text

# helper functions

def get_client():
    """
    Returns global client or a new one if it doesn't exist
    """
    global client

    if client is None:
        client = genai.Client(
            http_options=types.HttpOptions(
                retry_options=types.HttpRetryOptions(
                    initial_delay=initial_delay_seconds,
                    attempts=max_attempts,
                )
            ),
            api_key=get_auth_settings().gemini_api_key.get_secret_value(),
        )
    return client

def get_project_root() -> Path:
    """
    Returns base path of the project
    """
    project_path = get_auth_settings().project_path.get_secret_value()

    if not project_path:
        raise RuntimeError("PROJECT_PATH environment variable is not configured")

    return Path(project_path).resolve()

def add_message(msg_from: str, msg_content: str, msg_container: list):
    """
    Appends a new message with explicit types to the container.
    Gemini expects a list of types.Content objects or specifically structured dicts:
    [{"role": "user", "parts": [{type: "..."}]}, {"role": "model", "parts": [{type: "..."}]}]

    
    Args:
        msg_from: message producer, either "user" or "model"
        msg_content: content of the message
        msg_container: a list to store all messages
    """

    msg_container.append(
        types.Content(
            role=msg_from,
            parts=[types.Part.from_text(text=msg_content)]
        )
    )

def multiline_input(agent: str, end_literal: str, max_num_lines: int) -> str:
    """
    Captures multiple lines of user input from console and 
    
    Args:
        agent: indicates which agent is the user instruction for, either "review" or "generate"
        end_literal: the literal to mark end of multiline input, should be on it's own row
        max_num_lines: maximum number of lines to be read
    
    Returns: 
        A string of lines concatenated with '\n'
    """
    if agent == "reviewer":
        user_instruction = "Enter your code or file path and instructions for the agent." \
        "\nAgent can review your code and can save revised code in new or existing file."
    else:
        user_instruction = "Enter your request for code generation"
    user_instruction += f"\nType '{end_of_code}' on a line by itself when finished. Maximum number of lines: {max_num_lines}."
    print(user_instruction)

    lines = []
    for _ in range(max_num_lines):
        line = input()
        if line == end_literal:
            break
        lines.append(line)
    return "\n".join(lines)

def read_local_file(file_path: str) -> str:
    """
    Reads the content of a local file within the project directory.
    
    Args:
        file_path: The path to the file to be read.
    """
    # restricting to current project folder
    project_root = get_project_root()
    target = (project_root / file_path).resolve()
    if not target.is_relative_to(project_root):
        return "Error: Path escapes the allowed project directory."

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            logging.debug(f"file {file_path} opened")
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def save_local_file(file_path: str, content: str) -> str:
    """
    Writes or overwrites content to a local file within the project directory.
    
    Args:
        file_path: The path of the file to save.
        content: The text content to write into the file.
    """

    # restricting file types for safety reasons
    if not file_path.endswith('.py') and not file_path.endswith('.txt'):
        return "Error: Security policy only allows writing to .py or .txt files."

    # restricting to current project folder
    project_root = get_project_root()
    target = (project_root / file_path).resolve()
    if not target.is_relative_to(project_root):
        return "Error: Path escapes the allowed project directory."
        
    loc = "written in new"
    # if file exists append to end if it
    if os.path.exists(file_path):
        content = '"""\nRefactored code by model:\n' + content + '\n"""' 
        loc = "appended to"

    try:
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Success: Refactored code {loc} file {file_path}."
    except Exception as e:
        return f"Error writing file: {str(e)}"

def telemetry(msg_container: list) -> str:
    """
    Returned structured telemetry output

    Args:
        msg_container: telemetry container
    """
    result = "\n" + "="*40 + "\n" + "TELEMETRY: Message Stack Depth: " + str(len(msg_container))
    for idx, msg in enumerate(msg_container):
        # Determine if it's a dict or a types.Content object from your helpers
        role = msg.role if hasattr(msg, 'role') else msg.get('role')
        parts = msg.parts if hasattr(msg, 'parts') else msg.get('parts')
        
        # Peek at the content type inside the parts
        part_preview = ""
        if parts:
            first_part = parts[0]
            if hasattr(first_part, 'text') and first_part.text is not None:
                part_preview = "Text Content"
            elif hasattr(first_part, 'function_call') and first_part.function_call is not None:
                part_preview = "Tool Request [f_call]"
            elif hasattr(first_part, 'function_response') and first_part.function_response is not None:
                part_preview = "Tool Output [f_res]"
        result += "\n[" + str(idx) + "] Role: " + role + "| Data Type: " + part_preview
    result += "\n" + "="*40
    return result

if __name__ == "__main__":
    user_input = multiline_input("review", end_of_code, max_lines)
    print(asyncio.run(agent_result(user_input)))