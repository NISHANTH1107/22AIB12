import requests
import time

BASE_URL = "http://localhost:8000"

def test_create_shorturl():
    print("Testing short URL creation...")
    payload = {
        "url": "https://www.google.com",
        "validity": 2,  
        "shortcode": "test123"
    }
    
    response = requests.post(f"{BASE_URL}/shorturls", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.json()["shortlink"].split("/")[-1]  
def test_redirect(shortcode):
    print(f"\nTesting redirect for {shortcode}...")
    response = requests.get(f"{BASE_URL}/{shortcode}", allow_redirects=False)
    print(f"Redirect status: {response.status_code}")
    print(f"Redirect location: {response.headers.get('Location')}")

def test_stats(shortcode):
    print(f"\nTesting stats for {shortcode}...")
    response = requests.get(f"{BASE_URL}/shorturls/{shortcode}")
    print(f"Status: {response.status_code}")
    print(f"Stats: {response.json()}")

def test_errors():
    print("\nTesting error cases...")
    
    
    response = requests.get(f"{BASE_URL}/nonexistent")
    print(f"Non-existent shortcode: {response.status_code}")
    
    payload = {"url": "https://example.com", "shortcode": "test123"}
    response = requests.post(f"{BASE_URL}/shorturls", json=payload)
    print(f"Duplicate shortcode: {response.status_code}")

if __name__ == "__main__":
    shortcode = test_create_shorturl()
    test_redirect(shortcode)
    test_stats(shortcode)
    test_errors()