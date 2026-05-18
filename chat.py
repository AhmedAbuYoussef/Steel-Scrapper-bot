from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic


def openapi_to_anthropic_tool(openapi_doc, path, method="get"):
    operation = openapi_doc["paths"][path][method]
    properties = {}
    required = []
    for param in operation.get("parameters", []):
        if param.get("in") != "query":
            continue
        name = param["name"]
        properties[name] = {"type": param["schema"]["type"]}
        if param.get("required", False):
            required.append(name)
    return {
        "name": path.lstrip("/"),
        "description": operation["description"],
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def route_once(user_message, tools, system_prompt, model="claude-haiku-4-5-20251001", max_tokens=1024):
    client = Anthropic()
    return client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        tools=tools,
        messages=[{"role": "user", "content": user_message}],
    )
