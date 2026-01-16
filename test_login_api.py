#!/usr/bin/env python3
"""
Test the actual login API to verify UserResponse includes admin_role and is_sub_admin
"""
import requests
import json

API_URL = "http://localhost:8000"

def test_login_response():
    """Test login with coding_ta user and check response"""
    
    # Test credentials for coding_ta1
    login_data = {
        "email": "coding_ta1@jklu.edu.in",
        "password": "ta1_password"
    }
    
    print("=" * 70)
    print("Testing Login API for coding_ta user")
    print("=" * 70)
    print(f"\n1. Attempting login with: {login_data['email']}")
    
    try:
        # Step 1: Login
        response = requests.post(f"{API_URL}/login", json=login_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Login failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            print("❌ No access token in response")
            return False
        
        print(f"✅ Login successful, got token: {access_token[:20]}...")
        
        # Step 2: Get user info with /me endpoint
        print(f"\n2. Fetching user info from /me endpoint...")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        me_response = requests.get(f"{API_URL}/me", headers=headers, timeout=10)
        
        if me_response.status_code != 200:
            print(f"❌ /me endpoint failed with status {me_response.status_code}")
            print(f"Response: {me_response.text}")
            return False
        
        user_data = me_response.json()
        
        print(f"✅ Got user data from /me endpoint\n")
        print("=" * 70)
        print("USER RESPONSE DATA:")
        print("=" * 70)
        print(json.dumps(user_data, indent=2))
        print("=" * 70)
        
        # Step 3: Verify critical fields
        print("\n3. Verifying critical fields for coding_ta redirection:")
        print()
        
        checks = [
            ("email", "coding_ta1@jklu.edu.in", user_data.get("email")),
            ("is_admin", True, user_data.get("is_admin")),
            ("admin_role", "coding_ta", user_data.get("admin_role")),
            ("is_sub_admin", True, user_data.get("is_sub_admin")),
        ]
        
        all_passed = True
        for field, expected, actual in checks:
            status = "✅" if actual == expected else "❌"
            print(f"  {status} {field}: {actual} (expected: {expected})")
            if actual != expected:
                all_passed = False
        
        print()
        print("=" * 70)
        
        if all_passed:
            print("✅ ALL CHECKS PASSED!")
            print("\nBackend is correctly sending:")
            print("  - admin_role: 'coding_ta'")
            print("  - is_sub_admin: true")
            print("\nFrontend should redirect to: /admin/coding-hour")
        else:
            print("❌ SOME CHECKS FAILED!")
            print("\nThe backend is NOT sending the correct role data.")
        
        print("=" * 70)
        
        return all_passed
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend at", API_URL)
        print("\nIs the backend running?")
        print("Start it with: cd ExamPaperPortal && source coding/bin/activate && uvicorn main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_login_response()
