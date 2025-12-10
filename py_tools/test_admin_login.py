#!/usr/bin/env python3
"""
Test script to verify admin login works
"""

import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Get backend URL from environment or use default
BACKEND_URL = os.getenv("BACKEND_URL", "https://exam-portal-backend-jklu-solomaze.onrender.com")

def test_admin_login():
    """Test admin login endpoint"""
    print(f"\n{'='*60}")
    print("TESTING ADMIN LOGIN")
    print(f"{'='*60}\n")
    print(f"Backend URL: {BACKEND_URL}\n")
    
    email = "examportaljklu@jklu.edu.in"
    password = "Aexamadmin@123"
    
    try:
        # Test admin login
        response = requests.post(
            f"{BACKEND_URL}/admin-login",
            data={
                "username": email,
                "password": password
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS! Login works!")
            print(f"Token received: {data.get('access_token', '')[:50]}...")
            print(f"Token type: {data.get('token_type', '')}")
            return True
        else:
            print(f"❌ FAILED!")
            print(f"Response: {response.text}")
            print(f"\nPossible issues:")
            print(f"  1. Password is incorrect")
            print(f"  2. User doesn't exist in database")
            print(f"  3. User exists but is_admin is False")
            print(f"  4. Backend connection issue")
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
    test_admin_login()

