"""
Test script for Community Vulnerability Submission and Management Endpoints

Tests POST, PUT, and DELETE operations for community vulnerabilities.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_community_vuln_endpoints():
    """Test community vulnerability submission and management endpoints"""

    print("=" * 70)
    print("Testing Community Vulnerability Management Endpoints")
    print("=" * 70)
    print()

    # Step 1: Register regular user
    print("1. Registering regular user...")
    register_data = {
        "username": "commvulntest",
        "email": "commvuln@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)

    if response.status_code == 201:
        token = response.json()["access_token"]
        print(f"   ✓ Regular user registered successfully")
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"   ⚠ User exists, logging in...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": register_data["username"], "password": register_data["password"]}
        )
        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"   ✓ Logged in successfully")
        else:
            print(f"   ✗ Login failed: {response.text}")
            return False
    else:
        print(f"   ✗ Registration failed: {response.text}")
        return False
    print()

    headers = {"Authorization": f"Bearer {token}"}

    # Step 2: Register admin user
    print("2. Registering admin user...")
    admin_register = {
        "username": "adminuser",
        "email": "admin@test.com",
        "password": "adminpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=admin_register)

    if response.status_code == 201:
        admin_token = response.json()["access_token"]
        print(f"   ✓ Admin user registered successfully")
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"   ⚠ Admin exists, logging in...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": admin_register["username"], "password": admin_register["password"]}
        )
        if response.status_code == 200:
            admin_token = response.json()["access_token"]
            print(f"   ✓ Admin logged in successfully")
        else:
            print(f"   ✗ Admin login failed: {response.text}")
            return False
    else:
        print(f"   ✗ Admin registration failed: {response.text}")
        return False

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print()

    # Step 3: Submit community vulnerability (auto-generated ID)
    print("3. Submitting community vulnerability (auto-generated ID)...")
    vuln_data = {
        "description": "Critical buffer overflow in authentication module allowing remote code execution",
        "cvss_impact": 9.5,
        "cvss_exploitability": 8.7,
        "affected_subsystem_type": "authentication",
        "exploit_present": True,
        "patch_cost_estimate": 15.5
    }
    response = requests.post(f"{BASE_URL}/api/vulnerabilities/community", json=vuln_data, headers=headers)

    if response.status_code == 201:
        vuln = response.json()
        comm_id = vuln["comm_id"]
        print(f"   ✓ Vulnerability submitted successfully")
        print(f"   Generated ID: {comm_id}")
        print(f"   Status: {vuln['status']}")
        print(f"   Reporter: {vuln['reporter_username']}")
        print(f"   CVSS Impact: {vuln['cvss_impact']}")
    else:
        print(f"   ✗ Submission failed: {response.text}")
        return False
    print()

    # Step 4: Submit with custom ID
    print("4. Submitting vulnerability with custom ID...")
    vuln_data2 = {
        "comm_id": "COMM-TEST-9999",
        "description": "SQL injection vulnerability in user profile update endpoint",
        "cvss_impact": 7.5,
        "cvss_exploitability": 6.8
    }
    response = requests.post(f"{BASE_URL}/api/vulnerabilities/community", json=vuln_data2, headers=headers)

    if response.status_code == 201:
        vuln2 = response.json()
        comm_id2 = vuln2["comm_id"]
        print(f"   ✓ Vulnerability submitted with custom ID")
        print(f"   Custom ID: {comm_id2}")
        print(f"   Status: {vuln2['status']}")
    else:
        print(f"   ✗ Submission failed: {response.text}")
        return False
    print()

    # Step 5: Try to submit duplicate comm_id
    print("5. Testing duplicate comm_id rejection...")
    response = requests.post(f"{BASE_URL}/api/vulnerabilities/community", json=vuln_data2, headers=headers)

    if response.status_code == 400:
        print(f"   ✓ Correctly rejected duplicate comm_id (400)")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"   ✗ Should have rejected duplicate (got {response.status_code})")
    print()

    # Step 6: List community vulnerabilities (should see 2)
    print("6. Listing community vulnerabilities...")
    response = requests.get(f"{BASE_URL}/api/vulnerabilities/community")

    if response.status_code == 200:
        vulns = response.json()
        print(f"   ✓ Retrieved {len(vulns)} vulnerability(ies)")
        for v in vulns[:3]:
            print(f"      - {v['comm_id']}: Status={v['status']}, Score={v['vote_score']}")
    else:
        print(f"   ✗ Failed to list: {response.text}")
    print()

    # Step 7: Try to verify as regular user (should fail)
    print("7. Testing verify as regular user (should fail)...")
    response = requests.put(f"{BASE_URL}/api/vulnerabilities/community/{comm_id}/verify", headers=headers)

    if response.status_code == 403:
        print(f"   ✓ Correctly rejected non-admin verification (403)")
    else:
        print(f"   ✗ Should have rejected non-admin (got {response.status_code})")
    print()

    # Step 8: Verify as admin
    print("8. Verifying vulnerability as admin...")
    response = requests.put(f"{BASE_URL}/api/vulnerabilities/community/{comm_id}/verify", headers=admin_headers)

    if response.status_code == 200:
        verified_vuln = response.json()
        print(f"   ✓ Vulnerability verified successfully")
        print(f"   ID: {verified_vuln['comm_id']}")
        print(f"   New Status: {verified_vuln['status']}")
    else:
        print(f"   ✗ Verification failed: {response.text}")
    print()

    # Step 9: Verify non-existent vulnerability
    print("9. Testing verify non-existent vulnerability...")
    response = requests.put(f"{BASE_URL}/api/vulnerabilities/community/NONEXISTENT/verify", headers=admin_headers)

    if response.status_code == 404:
        print(f"   ✓ Correctly returned 404 for non-existent vulnerability")
    else:
        print(f"   ✗ Should have returned 404 (got {response.status_code})")
    print()

    # Step 10: Register second user
    print("10. Registering second user...")
    user2_register = {
        "username": "user2test",
        "email": "user2@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user2_register)

    if response.status_code == 201:
        user2_token = response.json()["access_token"]
        print(f"   ✓ Second user registered")
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"   ⚠ User exists, logging in...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": user2_register["username"], "password": user2_register["password"]}
        )
        if response.status_code == 200:
            user2_token = response.json()["access_token"]
            print(f"   ✓ User2 logged in")
        else:
            print(f"   ✗ User2 login failed")
            return False
    else:
        print(f"   ✗ User2 registration failed")
        return False

    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    print()

    # Step 11: Try to deprecate another user's vulnerability (should fail)
    print("11. Testing deprecate as non-reporter (should fail)...")
    response = requests.delete(f"{BASE_URL}/api/vulnerabilities/community/{comm_id}", headers=user2_headers)

    if response.status_code == 403:
        print(f"   ✓ Correctly rejected non-reporter deprecation (403)")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"   ✗ Should have rejected non-reporter (got {response.status_code})")
    print()

    # Step 12: Deprecate own vulnerability
    print("12. Deprecating own vulnerability as reporter...")
    response = requests.delete(f"{BASE_URL}/api/vulnerabilities/community/{comm_id2}", headers=headers)

    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Vulnerability deprecated successfully")
        print(f"   ID: {result['comm_id']}")
        print(f"   New Status: {result['status']}")
    else:
        print(f"   ✗ Deprecation failed: {response.text}")
    print()

    # Step 13: Deprecate as admin
    print("13. Deprecating vulnerability as admin...")
    response = requests.delete(f"{BASE_URL}/api/vulnerabilities/community/{comm_id}", headers=admin_headers)

    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ Admin deprecated vulnerability successfully")
        print(f"   ID: {result['comm_id']}")
        print(f"   New Status: {result['status']}")
    else:
        print(f"   ✗ Admin deprecation failed: {response.text}")
    print()

    # Step 14: Deprecate non-existent vulnerability
    print("14. Testing deprecate non-existent vulnerability...")
    response = requests.delete(f"{BASE_URL}/api/vulnerabilities/community/NONEXISTENT", headers=headers)

    if response.status_code == 404:
        print(f"   ✓ Correctly returned 404 for non-existent vulnerability")
    else:
        print(f"   ✗ Should have returned 404 (got {response.status_code})")
    print()

    # Step 15: Submit without authentication (should fail)
    print("15. Testing submit without authentication (should fail)...")
    response = requests.post(f"{BASE_URL}/api/vulnerabilities/community", json=vuln_data)

    if response.status_code == 401:
        print(f"   ✓ Correctly rejected unauthenticated submission (401)")
    else:
        print(f"   ✗ Should have rejected unauthenticated (got {response.status_code})")
    print()

    # Step 16: Submit with invalid CVSS score
    print("16. Testing submit with invalid CVSS score...")
    invalid_data = {
        "description": "Test vulnerability with invalid score",
        "cvss_impact": 15.0,  # Invalid - should be 0-10
        "cvss_exploitability": 8.0
    }
    response = requests.post(f"{BASE_URL}/api/vulnerabilities/community", json=invalid_data, headers=headers)

    if response.status_code == 422:
        print(f"   ✓ Correctly rejected invalid CVSS score (422)")
    else:
        print(f"   ✗ Should have rejected invalid score (got {response.status_code})")
    print()

    print("=" * 70)
    print("All community vulnerability management tests completed!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    import sys

    try:
        success = test_community_vuln_endpoints()
        sys.exit(0 if success else 1)
    except requests.ConnectionError:
        print("✗ Error: Could not connect to server. Is it running on http://localhost:8000?")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
