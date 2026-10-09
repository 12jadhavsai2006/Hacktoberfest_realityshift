import requests
import json

url = "http://127.0.0.1:8000/api/v1/analyze-shift"

files = {
    "file_a": ("before.jpg", open("before.jpg", "rb"), "image/jpeg"),
    "file_b": ("after.jpg", open("after.jpg", "rb"), "image/jpeg"),
}

data = {
    "user_change_description": "I moved the object on the desk."
}

print("Sending reality states to Gemma 4... this might take 10-15 seconds...")
response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    print("\nSUCCESS! Here is Gemma's Counterfactual Reasoning:\n")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"\nERROR: {response.status_code}")
    print(response.text)