#!/usr/bin/env python3
"""
Test script to verify forgot password endpoint works with database
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Get backend URL from environment or use default
BACKEND_URL = os.getenv("BACKEND_URL", "https://exam-portal-backend-jklu-solomaze.onrender.com")

def test_forgot_password(email: str):
    """Test forgot password endpoint"""
    print(f"\n{'='*60}")
    print("TESTING FORGOT PASSWORD ENDPOINT")
    print(f"{'='*60}\n")
    print(f"Backend URL: {BACKEND_URL}")
    print(f"Testing with email: {email}\n")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/forgot-password",
            json={"email": email},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}\n")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success") or data.get("message"):
                print("✅ SUCCESS! Endpoint is working and connected to database")
                print(f"Message: {data.get('message', 'N/A')}")
                return True
            else:
                print("⚠️  Response received but format unexpected")
                return False
        else:
            print(f"❌ FAILED! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CONNECTION ERROR!")
        print(f"Error: {e}")
        print(f"\nPossible issues:")
        print(f"  1. Backend URL is wrong: {BACKEND_URL}")
        print(f"  2. Backend service is down")
        print(f"  3. Network connection issue")
        return False

if __name__ == "__main__":
    # Test with the email from the screenshot
    test_email = "amanpratapsingh@jklu.edu.in"
    test_forgot_password(test_email)
    
    print("\n" + "="*60)
    print("NOTE: The endpoint should return success even if email doesn't exist")
    print("(for security - doesn't reveal if email is registered)")
    print("="*60)

