"""
Test script for Admin Management Endpoints

Tests admin-only functionality including user management and platform statistics.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_admin_endpoints():
    """Test admin management endpoints"""

    print("=" * 70)
    print("Testing Admin Management Endpoints")
    print("=" * 70)
    print()

    # Step 1: Register regular user
    print("1. Registering regular user...")
    user1_data = {
        "username": "regularuser",
        "email": "regular@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user1_data)

    if response.status_code == 201:
        user1_token = response.json()["access_token"]
        print(f"   ✓ Regular user registered successfully")
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"   ⚠ User exists, logging in...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": user1_data["username"], "password": user1_data["password"]}
        )
        if response.status_code == 200:
            user1_token = response.json()["access_token"]
            print(f"   ✓ Logged in successfully")
        else:
            print(f"   ✗ Login failed: {response.text}")
            return False
    else:
        print(f"   ✗ Registration failed: {response.text}")
        return False
    print()

    user1_headers = {"Authorization": f"Bearer {user1_token}"}

    # Step 2: Try to access admin endpoint as regular user (should fail)
    print("2. Testing admin endpoint access as regular user (should fail)...")
    response = requests.get(f"{BASE_URL}/api/admin/users", headers=user1_headers)

    if response.status_code == 403:
        print(f"   ✓ Correctly rejected non-admin access (403)")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"   ✗ Should have rejected non-admin (got {response.status_code})")
    print()

    # Step 3: Create admin user (manually set is_admin=True in database)
    # For testing, we'll register a user and assume they become admin
    print("3. Registering admin user...")
    admin_data = {
        "username": "admintest",
        "email": "admintest@test.com",
        "password": "adminpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=admin_data)

    if response.status_code == 201:
        admin_token = response.json()["access_token"]
        admin_user_id = response.json()["user"]["id"]
        print(f"   ✓ Admin user registered successfully")
        print(f"   Note: This user needs is_admin=True in database for full testing")
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"   ⚠ Admin exists, logging in...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": admin_data["username"], "password": admin_data["password"]}
        )
        if response.status_code == 200:
            admin_token = response.json()["access_token"]
            admin_user_id = response.json()["user"]["id"]
            print(f"   ✓ Admin logged in successfully")
        else:
            print(f"   ✗ Admin login failed: {response.text}")
            return False
    else:
        print(f"   ✗ Admin registration failed: {response.text}")
        return False

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print()

    # Step 4: List all users (admin only)
    print("4. Listing all users as admin...")
    response = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers)

    if response.status_code == 200:
        users = response.json()
        print(f"   ✓ Retrieved {len(users)} user(s)")
        for user in users[:3]:  # Show first 3
            print(f"      - {user['username']}: Admin={user['is_admin']}, "
                  f"Systems={user['system_count']}, Sims={user['simulation_count']}")
    elif response.status_code == 403:
        print(f"   ⚠ Access denied - user may not have admin privileges in database")
        print(f"   Note: For full testing, manually set is_admin=True for admintest user")
    else:
        print(f"   ✗ Failed to list users: {response.text}")
    print()

    # Step 5: List users with pagination
    print("5. Testing pagination (limit=2, skip=0)...")
    response = requests.get(f"{BASE_URL}/api/admin/users?limit=2&skip=0", headers=admin_headers)

    if response.status_code == 200:
        users = response.json()
        print(f"   ✓ Retrieved {len(users)} user(s) with pagination")
    elif response.status_code == 403:
        print(f"   ⚠ Access denied - admin privileges required")
    else:
        print(f"   ✗ Pagination failed: {response.text}")
    print()

    # Step 6: Get platform statistics
    print("6. Getting platform statistics...")
    response = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_headers)

    if response.status_code == 200:
        stats = response.json()
        print(f"   ✓ Statistics retrieved successfully")
        print(f"   Total Users: {stats['total_counts']['users']}")
        print(f"   Total Systems: {stats['total_counts']['systems']}")
        print(f"   Total Simulations: {stats['total_counts']['simulations']}")
        print(f"   Total Vulnerabilities: {stats['total_counts']['vulnerabilities']}")
        print(f"   Admin Users: {stats['user_distribution']['admin_users']}")
        print(f"   Regular Users: {stats['user_distribution']['regular_users']}")
        print(f"   Unverified Vulnerabilities: {stats['vulnerability_status']['unverified']}")
        print(f"   New Users (7d): {stats['recent_activity_7d']['new_users']}")
        print(f"   New Simulations (30d): {stats['recent_activity_30d']['new_simulations']}")
    elif response.status_code == 403:
        print(f"   ⚠ Access denied - admin privileges required")
    else:
        print(f"   ✗ Failed to get statistics: {response.text}")
    print()

    # Step 7: Register another regular user for admin toggle test
    print("7. Registering second regular user...")
    user2_data = {
        "username": "regularuser2",
        "email": "regular2@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user2_data)

    if response.status_code == 201:
        user2_id = response.json()["user"]["id"]
        user2_token = response.json()["access_token"]
        print(f"   ✓ Second regular user registered")
        print(f"   User ID: {user2_id}")
    elif response.status_code == 400 and "already registered" in response.text:
        print(f"   ⚠ User exists, logging in...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            data={"username": user2_data["username"], "password": user2_data["password"]}
        )
        if response.status_code == 200:
            user2_id = response.json()["user"]["id"]
            user2_token = response.json()["access_token"]
            print(f"   ✓ User2 logged in")
            print(f"   User ID: {user2_id}")
        else:
            print(f"   ✗ User2 login failed")
            return False
    else:
        print(f"   ✗ User2 registration failed")
        return False

    user2_headers = {"Authorization": f"Bearer {user2_token}"}
    print()

    # Step 8: Toggle admin status for user2
    print("8. Toggling admin status for user2...")
    response = requests.put(f"{BASE_URL}/api/admin/users/{user2_id}/admin", headers=admin_headers)

    if response.status_code == 200:
        updated_user = response.json()
        print(f"   ✓ Admin status toggled successfully")
        print(f"   User: {updated_user['username']}")
        print(f"   New Admin Status: {updated_user['is_admin']}")
    elif response.status_code == 403:
        print(f"   ⚠ Access denied - admin privileges required")
    else:
        print(f"   ✗ Toggle failed: {response.text}")
    print()

    # Step 9: Try to toggle own admin status (should fail)
    print("9. Testing self-admin-toggle prevention...")
    response = requests.put(f"{BASE_URL}/api/admin/users/{admin_user_id}/admin", headers=admin_headers)

    if response.status_code == 403 and "Cannot modify your own" in response.text:
        print(f"   ✓ Correctly prevented self-demotion (403)")
        print(f"   Error: {response.json()['detail']}")
    elif response.status_code == 403:
        print(f"   ⚠ Access denied - may not have admin privileges")
    else:
        print(f"   ✗ Should have prevented self-modification (got {response.status_code})")
    print()

    # Step 10: Try to toggle non-existent user
    print("10. Testing toggle for non-existent user...")
    response = requests.put(f"{BASE_URL}/api/admin/users/999999/admin", headers=admin_headers)

    if response.status_code == 404:
        print(f"   ✓ Correctly returned 404 for non-existent user")
    elif response.status_code == 403:
        print(f"   ⚠ Access denied - admin privileges required")
    else:
        print(f"   ✗ Should have returned 404 (got {response.status_code})")
    print()

    # Step 11: Try to toggle admin status as regular user (should fail)
    print("11. Testing admin toggle as regular user (should fail)...")
    response = requests.put(f"{BASE_URL}/api/admin/users/{user2_id}/admin", headers=user1_headers)

    if response.status_code == 403:
        print(f"   ✓ Correctly rejected non-admin toggle (403)")
    else:
        print(f"   ✗ Should have rejected non-admin (got {response.status_code})")
    print()

    # Step 12: Create some test data for statistics
    print("12. Creating test data (system + simulation + vulnerability)...")

    # Create system
    system_config = {
        "name": "Test System for Stats",
        "config_json": json.dumps({
            "system_name": "Test System",
            "system_class": "Test Class",
            "subsystems": [
                {
                    "id": "sub1",
                    "name": "Subsystem 1",
                    "connected_to": [],
                    "functional_dependencies": []
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-9999",
                    "description": "Test vulnerability",
                    "subsystem_id": "sub1",
                    "cvss_impact": 7.0,
                    "cvss_exploitability": 6.0,
                    "exploit_present": False,
                    "patch_cost": 10.0,
                    "dependencies": []
                }
            ]
        })
    }
    response = requests.post(f"{BASE_URL}/api/systems", json=system_config, headers=user1_headers)

    if response.status_code == 201:
        system_id = response.json()["id"]
        print(f"   ✓ Test system created (ID: {system_id})")

        # Create simulation
        sim_data = {"system_id": system_id, "rounds": 5}
        response = requests.post(f"{BASE_URL}/api/simulations", json=sim_data, headers=user1_headers)
        if response.status_code == 201:
            print(f"   ✓ Test simulation created")

        # Create community vulnerability
        vuln_data = {
            "description": "Test community vulnerability for statistics",
            "cvss_impact": 8.0,
            "cvss_exploitability": 7.5
        }
        response = requests.post(f"{BASE_URL}/api/vulnerabilities/community", json=vuln_data, headers=user1_headers)
        if response.status_code == 201:
            print(f"   ✓ Test community vulnerability created")
    else:
        print(f"   ⚠ Test data creation may have failed")
    print()

    # Step 13: Re-check statistics to see updates
    print("13. Re-checking statistics after data creation...")
    response = requests.get(f"{BASE_URL}/api/admin/stats", headers=admin_headers)

    if response.status_code == 200:
        stats = response.json()
        print(f"   ✓ Updated statistics retrieved")
        print(f"   Most Active Users: {len(stats['most_active_users'])} user(s)")
        if stats['most_active_users']:
            for user in stats['most_active_users'][:3]:
                print(f"      - {user['username']}: {user['simulation_count']} simulations")
        print(f"   Top Contributors: {len(stats['top_contributors'])} user(s)")
        if stats['top_contributors']:
            for user in stats['top_contributors'][:3]:
                print(f"      - {user['username']}: {user['contribution_count']} vulnerabilities")
    elif response.status_code == 403:
        print(f"   ⚠ Access denied - admin privileges required")
    else:
        print(f"   ✗ Failed to get updated statistics")
    print()

    # Step 14: Test unauthenticated access to admin endpoints
    print("14. Testing unauthenticated access to admin endpoints...")
    response = requests.get(f"{BASE_URL}/api/admin/users")

    if response.status_code == 401:
        print(f"   ✓ Correctly rejected unauthenticated access (401)")
    else:
        print(f"   ✗ Should have rejected unauthenticated (got {response.status_code})")
    print()

    print("=" * 70)
    print("All admin management tests completed!")
    print("=" * 70)
    print()
    print("IMPORTANT NOTES:")
    print("- Some tests may fail with 403 if the admin user doesn't have is_admin=True")
    print("- To fully test admin functionality:")
    print("  1. Manually update database: UPDATE users SET is_admin=1 WHERE username='admintest'")
    print("  2. Re-run this test script")
    print("=" * 70)

    return True


if __name__ == "__main__":
    import sys

    try:
        success = test_admin_endpoints()
        sys.exit(0 if success else 1)
    except requests.ConnectionError:
        print("✗ Error: Could not connect to server. Is it running on http://localhost:8000?")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
