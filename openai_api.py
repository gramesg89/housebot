
# 0) Install / upgrade
%pip install --quiet --upgrade openai

# 1) Imports & client
import os, json, pprint
from openai import OpenAI

client = OpenAI()   # reads OPENAI_API_KEY from env

# 2) Your function schema
functions = [{
    "name": "summarize_expenses",
    "description": "Summarize household expenses, highlight large categories, and suggest cost reductions.",
    "parameters": {
        "type": "object",
        "properties": {
            "data": {
                "type": "object",
                "properties": {
                    "month":       {"type": "string"},
                    "bills": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ID":        {"type": "integer"},
                                "category":  {"type": "string"},
                                "amount":    {"type": "number"},
                                "breakdown": {"type": "object","additionalProperties":{"type":"number"}}
                            },
                            "required": ["ID","category","amount","breakdown"]
                        }
                    },
                    "total":       {"type": "number"},
                    "proportions": {"type":"object","additionalProperties":{"type":"number"}},
                    "owed":        {"type":"object","additionalProperties":{"type":"number"}}
                },
                "required": ["month","bills","total","proportions","owed"]
            }
        },
        "required": ["data"]
    }
}]

# 3) Build messages: system → user → your real data
messages = [
    {"role":"system",  "content":"You are a helpful financial assistant."},
    {"role":"user",    "content":"Please analyze our expense data."},
    {
        "role":    "function",
        "name":    "summarize_expenses",
        "content": json.dumps(result)
    }
]

# 4) Call the model but disallow function calls
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    functions=functions,
    function_call="none"            # ← prevent any function_call
)

# 5) Now content will be the summary
print(response.choices[0].message.content)
