
from openai import OpenAI


qwen9b_url = "http://:8000/v1"
qwen27b_url = "http://g202:8001/v1"
qwen35b_url = "http://g012:8002/v1"

qwen9b = "qwen9b"
qwen27b = 'qwen27b'
qwen35b = 'qwen35b'

client = OpenAI(
    base_url=qwen35b_url,
    api_key="EMPTY"
)

response = client.chat.completions.create(
    model=qwen35b,
    messages=[
        {
            "role": "user",
            "content": "Can you tell me what is the cedar language(policy language for access control policy)? simply explain your thought."
        }
    ],
    temperature=0,
    max_tokens=1024,
    extra_body={
        "chat_template_kwargs": {
            "enable_thinking": False,
        }
    },
)

print(response.choices[0].message.content.strip())

