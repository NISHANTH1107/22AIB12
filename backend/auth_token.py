import requests

url = "http://20.244.56.144/evaluation-service/auth"
payload = {
    "email": "nishanth_22aib12@kgkite.ac.in",
    "name": "NISHANTH",
    "rollNo": "22AIB12",
    "accessCode": "dqXuwZ",
    "clientID": "2e4a0602-753a-4762-ad6d-ec901b5afef3",
    "clientSecret": "XuDTyAJUssThrEbE"
}

try:
    response = requests.post(url, json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.json())
except Exception as e:
    print("Error:", e)