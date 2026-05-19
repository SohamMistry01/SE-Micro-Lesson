import requests

url = "http://127.0.0.1:8000/microlesson/generate"

payload = {
    "category": "practical",
    "template_path": "default",
    "priority_llm": None,
    "filename": "microlesson_export",
}

try:
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Success!")
        print(response.json())
    else:
        print(f"Failed with status code {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("Could not connect to the server. Is your FastAPI app running?")
