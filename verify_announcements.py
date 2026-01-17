
import requests
import os

# Configuration
BASE_URL = "http://localhost:8000"
# Use a coding_ta token if possible, but for verification script we might need to login first
# or simulate. For simplicity, we'll try to login as coding_ta1

def login_as_coding_ta():
    url = f"{BASE_URL}/login"
    data = {
        "email": "coding_ta1@jklu.edu.in",
        "password": "ta1_password"
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to login: {response.status_code} {response.text}")
        return None

def verify_announcements():
    print("--- Verifying Announcements Feature ---")
    token = login_as_coding_ta()
    if not token:
        print("Skipping due to login failure")
        return

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Announcement
    print("\n1. Creating Announcement...")
    data = {"title": "Test Announcement", "content": "This is a test content."}
    # Optional: Test file upload manually if needed, but basic text first
    response = requests.post(f"{BASE_URL}/admin/coding-announcements", data=data, headers=headers)
    if response.status_code == 200:
        ann = response.json()
        print(f"✅ Created announcement ID: {ann['id']}")
        ann_id = ann['id']
    else:
        print(f"❌ Failed to create announcement: {response.status_code} {response.text}")
        return

    # 2. List Announcements
    print("\n2. Listing Announcements...")
    response = requests.get(f"{BASE_URL}/coding-announcements", headers=headers)
    if response.status_code == 200:
        anns = response.json()
        found = False
        for a in anns:
            if a["id"] == ann_id:
                found = True
                print(f"✅ Found announcement ID: {a['id']}")
                break
        if not found:
             print("❌ Announcement not found in list")
    else:
        print(f"❌ Failed to list announcements: {response.status_code} {response.text}")

    # 3. Delete Announcement
    print("\n3. Deleting Announcement...")
    response = requests.delete(f"{BASE_URL}/admin/coding-announcements/{ann_id}", headers=headers)
    if response.status_code == 200:
        print("✅ Deleted announcement successfully")
    else:
        print(f"❌ Failed to delete announcement: {response.status_code} {response.text}")

if __name__ == "__main__":
    verify_announcements()
