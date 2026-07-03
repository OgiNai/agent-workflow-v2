import requests
import json
import os

from apps.agent_with_tools import multiline_input
from apps.settings import get_auth_settings


def send_request(endpoint: str, content: str, rounds: int = 3, ) -> str:
    """
    Send POST request to the endpoint

    Args:
        endpoint: generate for two-agent system, review for agent with tools
        content: post request content
        rounds: max number of rounds for two-agent system; default is 3

    Returns:
        Status code, response and response headers in string
    """
    data_dict = {f"{endpoint}_content": content}
    if endpoint == "generate":
        data_dict["generate_rounds"] = rounds

    api_token = get_auth_settings().api_token.get_secret_value()

    response = requests.post(
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_token}"},
        url=f"http://localhost:8000/code/{endpoint}", 
        data=json.dumps(data_dict)
    )
    try:
        body = response.json()
    except requests.exceptions.JSONDecodeError:
        body = response.text
    return f"Status Code: {response.status_code}\nResponse: {body}\nFull Response Headers: {response.headers}"

# start server before running 

# alternatively use
# curl -X POST -H "Content-Type: application/json" -H "Authorization: Bearer [insert API_TOKEN]" -d '{"generate_rounds": 3, "generate_content": "Create Python function to merge overlapping intervals."}' http://localhost:8000/code/generate


if __name__ == "__main__":
    end_inp = ["R", "G"]
    while True:
        endpoint = input("Enter 'R' for code review or 'G' for code generation: ")
        if endpoint in end_inp:
            endpoint = ["review", "generate"][end_inp.index(endpoint)]
            break
    req_cont = multiline_input(endpoint, "END", 1000)
    print(send_request(endpoint, req_cont))