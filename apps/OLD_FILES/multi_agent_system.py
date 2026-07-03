from google import genai
from google.genai import types

from copy import deepcopy
import json

from pydantic import BaseModel, Field
from typing import List

from apps.settings import get_auth_settings

import logging

logger = logging.getLogger(__name__)

class AuditReport(BaseModel):
    status: str = Field(description="Must be exactly 'PASSED' or 'FAILED'")
    severity: str = Field(description="CRITICAL, HIGH, MEDIUM, LOW, or NONE if passed")
    flaws: List[str] = Field(description="A list of specific code flaws found, empty if passed")
    recommended_improvements: List[str] = Field(description="Actionable refactoring recommendations")
    refactored_code: str = Field(description="The fully corrected Python code block, empty if passed")

# create genai client to be reused 
client = None
initial_delay_seconds = 5
max_attempts = 3

PROMPT_CODER = """
You are an expert Python Developer. Your sole job is to write clean, functional, 
performant Python code based on the user request or feedback from the Auditor.
Output ONLY your code inside a valid markdown code block. Do not write introductory prose.
"""
PROMPT_AUDITOR = """
You are a ruthless Security & QA Auditor. Your sole job is to inspect Python code 
for edge-case failures, bugs, or security flaws. Be exceptionally critical. 
Inspect the provided code against your schema fields. 
If the code is perfect, state that in status field. 
Otherwise, list the flaws clearly. 
"""

prompts = [PROMPT_CODER, PROMPT_AUDITOR]
role_name = ["coder", "auditor"]
role_signature = ["[CDR]", "[AUD]", "[USR]"]
response_schema = [None, AuditReport]
model_name = "gemini-3.1-flash-lite"

async def agents_result(user_input: str, rounds: int) -> str:
    """
    Executes the actual agents loop between coder and auditor.

    Args
        user_input: text request for code generation
        rounds: maximum number of rounds to be executed

    Returns:
        Last response from model
    """

    specialist_in_turn = 0 # for coder, = 1 for auditor
    # the shared ledger to record message history
    shared_ledger = []

    add_text_message(2, "user", user_input, shared_ledger)

    # loop flags
    code_passed = False
    loop_end = False
    loop_count = 1

    while not loop_end:
        logger.info(f"\nloop {loop_count}")
        log_roles(shared_ledger, "shared")
        adjusted_ledger = prepare_history_for_specialist(role_name[specialist_in_turn], shared_ledger)
        log_roles(adjusted_ledger, "adjusted")
        
        model_response = call_specialist(
            role_name[specialist_in_turn], 
            prompts[specialist_in_turn],
            adjusted_ledger,
            response_schema[specialist_in_turn]
        )

        if specialist_in_turn == 1: # auditor
            logger.debug(f"raw model response: {model_response}")
            audit_data = json.loads(model_response)
            logger.debug(f"audit_data: {audit_data}")

            # if auditor says code has passed exit the loop
            if audit_data['status'] == "PASSED":
                logger.info("auditor PASSED the code!")
                code_passed = True
                break

        log_response(specialist_in_turn, model_response)
        add_text_message(specialist_in_turn, "model", model_response, shared_ledger)

        specialist_in_turn = change_turn(specialist_in_turn)
        # up to 3 rounds
        if loop_count == rounds * 2:
            logger.info(f"loop END after {rounds} rounds!")
            loop_end = True
        loop_count += 1

    if code_passed:
        return shared_ledger[-1].parts[0].text
    else:
        return "Code not passed checks within 3 rounds."

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

def call_specialist(role_name: str, system_instruction: str, history: list, resp_schema=None) -> str:
    """
    Invokes a specific model persona using the shared conversation history.
    
    Args:
        role_name: role of the specialist to be called, either "coder" or "auditor"
        system_instruction: appropriate system instruction for the role
        history: list of previous messages within current conversation
        resp_schema: structured response schema (for the auditor) or None

    Returns:
        response from model
    """
    logger.info(f"Activating Specialist: {role_name}...")
    
    gen_con_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.2, # Lower temperature for more deterministic engineering outputs
    )

    # If a schema is passed, we force JSON format and attach the structure
    if resp_schema:
        gen_con_config.response_mime_type = "application/json"
        gen_con_config.response_schema = resp_schema

    response = get_client().models.generate_content(
        model=model_name,
        config=gen_con_config,
        contents=history
    )
    return response.text

def add_text_message(msg_from: int, msg_role: str, msg_content: str, msg_container: list):
    """
    Appends a new message with explicit types to the container.
    
    Args:
        msg_from: message producer specialist, 0 for coder and 1 for auditor  
        msg_role: message role, either "user" or "model"
        msg_content: content of the message
        msg_container: a list to store all messages
    """
    # each role has unique signature added in the beggining of each message
    spec_sig = role_signature[msg_from] + "\n"
    msg_container.append(
        types.Content(
            role=msg_role,
            parts=[types.Part.from_text(text=spec_sig + msg_content)]
        )
    )

def change_turn(spec: int) -> int:
    """
    Changes specialist_in_turn from 0 to 1 or from 1 to 0.

    Args:
        spec: specialist number
        0 = coder
        1 = auditor

    Returns:
        Changed spec
    """
    return 1 if spec == 0 else 0

def log_roles(container: list, cont_name: str) -> str:
    """
    Prints a list of the roles from Content objects in the container

    Args
        container: list of Content objects
        cont_name: name of the container

    Returns:
        String with name of the container and items in it.
    """
    return f"roles in {cont_name} ledger: {[c.role for c in container]}"

def log_response(specialist: int, response: str):
    """
    Prints summary of specialist's response

    Args
        specialist: 0 for coder, 1 for auditor
        response: specialist's response

    Returns:
        Response from specialist: number of lines if coder and status if auditor
    """
    if specialist == 0:
        lines_num = response.count('\n') - 2
        return f"coder returned {lines_num} lines of code"
    else:
        if "PASSED" in response:
            return "auditor status: PASSED"
        elif "FAILED" in response:
            return "auditor status: FAILED"
        else:
            return "auditor status: UNKNOWN"

def prepare_history_for_specialist(target_role: str, ledger: list) -> list:
    """
    Dynamically transforms the global ledger so it alternates roles perfectly
    for the specific agent being called.

    Args:
        target_role: the role of the model we are preparing the ledger for; 
            either "coder" or "auditor"
        ledger: the original ledger

    Returns:
        Transformed ledger in a list
    """
    transformed_history = deepcopy(ledger)

    logger.info(f"target_role: {target_role}")
    
    for idx, entry in enumerate(transformed_history):
        first_part = entry.parts[0]

        # flag wether current message is from coder or not
        is_coder_msg = False
        if hasattr(first_part, 'text') and first_part.text:
            is_coder_msg = first_part.text.startswith(role_signature[0])
        logger.info(f"Is message from coder? {is_coder_msg}")

        # initial role is always "user"
        # if request is to coder and current message is from auditor or if
        # request is to auditor and current message is from coder role should be "user"
        if idx == 0 or target_role == "coder" and not is_coder_msg or target_role == "auditor" and is_coder_msg:
            entry.role = "user"
            logger.info(f"role of message at index {idx} set to user")
        
        # if request is to coder and current message is from coder or if
        # request is to auditor and current message is from auditor role should be "model"
        # all messages but the initial user request are recorded with "model" by default, so
        # no need to change these
        #elif target_role == "coder" and coder_msg or target_role == "auditor" and not coder_msg:
        #    entry.role = "model"
        
    return transformed_history