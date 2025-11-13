"""
Test script for authentication endpoints

Tests the complete authentication flow:
1. Register a new user
2. Login and get JWT token
3. Access protected endpoint with token
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_auth_flow():
    """Test the complete authentication flow"""

    print("=" * 70)
    print("Testing Authentication Endpoints")
    print("=" * 70)
    print()

    # Test 1: Register a new user
    print("1. Testing POST /api/auth/register")
    register_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "testpass123"
    }

    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"   Status Code: {response.status_code}")

    if response.status_code == 201:
        data = response.json()
        print(f"   ✓ User registered successfully")
        print(f"   Username: {data['user']['username']}")
        print(f"   Email: {data['user']['email']}")
        print(f"   Token Type: {data['token_type']}")
        print(f"   Token expires in: {data['expires_in']} seconds")
        access_token = data['access_token']
    else:
        print(f"   ✗ Registration failed: {response.text}")
        return False
    print()

    # Test 2: Try to register with same username (should fail)
    print("2. Testing duplicate username (should fail with 400)")
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"   Status Code: {response.status_code}")

    if response.status_code == 400:
        print(f"   ✓ Correctly rejected duplicate username")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"   ✗ Should have returned 400")
    print()

    # Test 3: Login with credentials
    print("3. Testing POST /api/auth/login")
    login_data = {
        "username": "testuser123",
        "password": "testpass123"
    }

    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        data=login_data  # OAuth2 uses form data, not JSON
    )
    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Login successful")
        print(f"   Token Type: {data['token_type']}")
        access_token = data['access_token']
        print(f"   Access Token (first 50 chars): {access_token[:50]}...")
    else:
        print(f"   ✗ Login failed: {response.text}")
        return False
    print()

    # Test 4: Login with wrong password (should fail)
    print("4. Testing login with wrong password (should fail with 401)")
    wrong_login_data = {
        "username": "testuser123",
        "password": "wrongpassword"
    }

    response = requests.post(f"{BASE_URL}/api/auth/login", data=wrong_login_data)
    print(f"   Status Code: {response.status_code}")

    if response.status_code == 401:
        print(f"   ✓ Correctly rejected wrong password")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"   ✗ Should have returned 401")
    print()

    # Test 5: Access protected endpoint without token (should fail)
    print("5. Testing GET /api/auth/me without token (should fail with 401)")
    response = requests.get(f"{BASE_URL}/api/auth/me")
    print(f"   Status Code: {response.status_code}")

    if response.status_code == 401:
        print(f"   ✓ Correctly rejected request without token")
    else:
        print(f"   ✗ Should have returned 401")
    print()

    # Test 6: Access protected endpoint with valid token
    print("6. Testing GET /api/auth/me with valid token")
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"   Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Successfully accessed protected endpoint")
        print(f"   User ID: {data['id']}")
        print(f"   Username: {data['username']}")
        print(f"   Email: {data['email']}")
        print(f"   Is Admin: {data['is_admin']}")
    else:
        print(f"   ✗ Failed to access protected endpoint: {response.text}")
        return False
    print()

    # Test 7: Access protected endpoint with invalid token (should fail)
    print("7. Testing GET /api/auth/me with invalid token (should fail with 401)")
    headers = {
        "Authorization": "Bearer invalid_token_12345"
    }

    response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    print(f"   Status Code: {response.status_code}")

    if response.status_code == 401:
        print(f"   ✓ Correctly rejected invalid token")
    else:
        print(f"   ✗ Should have returned 401")
    print()

    print("=" * 70)
    print("All authentication tests passed! ✓")
    print("=" * 70)

    return True


if __name__ == "__main__":
    import sys

    try:
        success = test_auth_flow()
        sys.exit(0 if success else 1)
    except requests.ConnectionError:
        print("✗ Error: Could not connect to server. Is it running on http://localhost:8000?")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
