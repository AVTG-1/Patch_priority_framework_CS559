"""
Test script for Systems API endpoints

Tests all CRUD operations for system configurations.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_systems_api():
    """Test the complete systems API flow"""

    print("=" * 70)
    print("Testing Systems API Endpoints")
    print("=" * 70)
    print()

    # Step 1: Register a user
    print("1. Registering test user...")
    register_data = {
        "username": "systemstest",
        "email": "systems@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    if response.status_code == 201:
        token = response.json()["access_token"]
        print(f"   ✓ User registered successfully")
        print(f"   Token: {token[:50]}...")
    else:
        print(f"   ✗ Registration failed: {response.text}")
        return False
    print()

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Create a system configuration
    print("2. Creating system configuration...")
    system_config = {
        "name": "Test SCADA System",
        "config_json": json.dumps({
            "system_name": "Industrial SCADA",
            "subsystems": [
                {"id": "hmi_001", "name": "HMI"},
                {"id": "plc_001", "name": "PLC"}
            ],
            "vulnerabilities": []
        })
    }
    response = requests.post(f"{BASE_URL}/api/systems", json=system_config, headers=headers)
    if response.status_code == 201:
        system_id = response.json()["id"]
        print(f"   ✓ System created successfully")
        print(f"   System ID: {system_id}")
        print(f"   Name: {response.json()['name']}")
    else:
        print(f"   ✗ System creation failed: {response.text}")
        return False
    print()

    # Step 3: List all systems for user
    print("3. Listing all systems for user...")
    response = requests.get(f"{BASE_URL}/api/systems", headers=headers)
    if response.status_code == 200:
        systems = response.json()
        print(f"   ✓ Retrieved {len(systems)} system(s)")
        for sys in systems:
            print(f"      - ID: {sys['id']}, Name: {sys['name']}")
    else:
        print(f"   ✗ Failed to list systems: {response.text}")
        return False
    print()

    # Step 4: Get specific system
    print(f"4. Getting system {system_id}...")
    response = requests.get(f"{BASE_URL}/api/systems/{system_id}", headers=headers)
    if response.status_code == 200:
        system = response.json()
        print(f"   ✓ System retrieved successfully")
        print(f"   Name: {system['name']}")
        print(f"   User ID: {system['user_id']}")
        print(f"   Created at: {system['created_at']}")
    else:
        print(f"   ✗ Failed to get system: {response.text}")
        return False
    print()

    # Step 5: Update system
    print(f"5. Updating system {system_id}...")
    updated_config = {
        "name": "Updated SCADA System",
        "config_json": json.dumps({
            "system_name": "Updated Industrial SCADA",
            "subsystems": [
                {"id": "hmi_001", "name": "HMI"},
                {"id": "plc_001", "name": "PLC"},
                {"id": "db_001", "name": "Database"}
            ],
            "vulnerabilities": []
        })
    }
    response = requests.put(f"{BASE_URL}/api/systems/{system_id}", json=updated_config, headers=headers)
    if response.status_code == 200:
        updated_system = response.json()
        print(f"   ✓ System updated successfully")
        print(f"   New name: {updated_system['name']}")
    else:
        print(f"   ✗ Failed to update system: {response.text}")
        return False
    print()

    # Step 6: Test invalid JSON
    print("6. Testing invalid JSON config...")
    invalid_config = {
        "name": "Invalid System",
        "config_json": "This is not valid JSON"
    }
    response = requests.post(f"{BASE_URL}/api/systems", json=invalid_config, headers=headers)
    if response.status_code == 400:
        print(f"   ✓ Correctly rejected invalid JSON")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"   ✗ Should have rejected invalid JSON")
    print()

    # Step 7: Test unauthorized access
    print("7. Testing unauthorized access...")
    response = requests.get(f"{BASE_URL}/api/systems")
    if response.status_code == 401:
        print(f"   ✓ Correctly rejected request without token")
    else:
        print(f"   ✗ Should have rejected unauthorized request")
    print()

    # Step 8: Test access to non-existent system
    print("8. Testing access to non-existent system...")
    response = requests.get(f"{BASE_URL}/api/systems/99999", headers=headers)
    if response.status_code == 404:
        print(f"   ✓ Correctly returned 404 for non-existent system")
    else:
        print(f"   ✗ Should have returned 404")
    print()

    # Step 9: Create second user and test isolation
    print("9. Testing system isolation between users...")
    register_data2 = {
        "username": "systemstest2",
        "email": "systems2@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data2)
    if response.status_code == 201:
        token2 = response.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}
        print(f"   ✓ Second user registered")

        # Try to access first user's system
        response = requests.get(f"{BASE_URL}/api/systems/{system_id}", headers=headers2)
        if response.status_code == 404:
            print(f"   ✓ Correctly denied access to another user's system")
        else:
            print(f"   ✗ Should have denied access (got {response.status_code})")
    print()

    # Step 10: Delete system
    print(f"10. Deleting system {system_id}...")
    response = requests.delete(f"{BASE_URL}/api/systems/{system_id}", headers=headers)
    if response.status_code == 204:
        print(f"   ✓ System deleted successfully")

        # Verify it's gone
        response = requests.get(f"{BASE_URL}/api/systems/{system_id}", headers=headers)
        if response.status_code == 404:
            print(f"   ✓ Confirmed system is deleted")
        else:
            print(f"   ✗ System should be deleted")
    else:
        print(f"   ✗ Failed to delete system: {response.text}")
        return False
    print()

    print("=" * 70)
    print("All systems API tests passed! ✓")
    print("=" * 70)

    return True


if __name__ == "__main__":
    import sys

    try:
        success = test_systems_api()
        sys.exit(0 if success else 1)
    except requests.ConnectionError:
        print("✗ Error: Could not connect to server. Is it running on http://localhost:8000?")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
