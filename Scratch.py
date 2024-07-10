import requests

response = requests.post("http://127.0.0.1:8000/record", json={"engine_temperature": 0.3})

print(response.status_code)
print(response.text)