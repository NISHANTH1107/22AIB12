import requests

url = "http://20.244.56.144/evaluation-service/register"
payload = {
    "email": "nishanth_22aib12@kgkite.ac.in",
    "name": "NISHANTH",
    "mobileNo": "8098259659",
    "githubUsername": "NISHANTH1107",
    "rollNo": "22AIB12",
    "accessCode": "dqXuwZ"
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)