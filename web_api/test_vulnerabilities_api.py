"""
Test script for Vulnerabilities API endpoints

Tests NVD integration, community vulnerabilities, and caching.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_vulnerabilities_api():
    """Test the vulnerabilities API endpoints"""

    print("=" * 70)
    print("Testing Vulnerabilities API Endpoints")
    print("=" * 70)
    print()

    # Step 1: Test NVD query endpoint
    print("1. Testing NVD CVE query (Log4j vulnerability)...")
    cve_id = "CVE-2021-44228"  # Famous Log4Shell vulnerability
    response = requests.get(f"{BASE_URL}/api/vulnerabilities/nvd", params={"cve_id": cve_id})

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Successfully fetched {cve_id}")
        print(f"   Description: {data['description'][:100]}...")
        print(f"   CVSS Impact: {data['cvss_impact']}")
        print(f"   CVSS Exploitability: {data['cvss_exploitability']}")
        print(f"   Exploit Present: {data['exploit_present']}")
        print(f"   Cached: {data['cached']}")
        print(f"   Cache Timestamp: {data['cache_timestamp']}")
    elif response.status_code == 503:
        print(f"   ⚠ NVD API unavailable (503) - this is expected if network issues")
        print(f"   Error: {response.json()['detail']}")
    elif response.status_code == 404:
        print(f"   ✗ CVE not found: {response.json()['detail']}")
    else:
        print(f"   ✗ Request failed with status {response.status_code}")
        print(f"   Error: {response.text}")
    print()

    # Step 2: Test cache by querying same CVE again
    print("2. Testing cache (querying same CVE again)...")
    response2 = requests.get(f"{BASE_URL}/api/vulnerabilities/nvd", params={"cve_id": cve_id})

    if response2.status_code == 200:
        data2 = response2.json()
        if data2['cached']:
            print(f"   ✓ Result served from cache")
            print(f"   Cache age: {data2['cache_timestamp']}")
        else:
            print(f"   ⚠ Expected cached result but got fresh data")
    else:
        print(f"   ⚠ Second request failed (expected if first request failed)")
    print()

    # Step 3: Test cache stats endpoint
    print("3. Testing cache stats endpoint...")
    response = requests.get(f"{BASE_URL}/api/vulnerabilities/cache/stats")

    if response.status_code == 200:
        stats = response.json()
        print(f"   ✓ Cache stats retrieved")
        print(f"   Total entries: {stats['total_entries']}")
        print(f"   TTL: {stats['ttl_hours']} hours")
        if stats['entries']:
            print(f"   Cached CVEs:")
            for entry in stats['entries']:
                print(f"      - {entry['cve_id']} (age: {entry['age_hours']:.2f} hours)")
    else:
        print(f"   ✗ Failed to get cache stats: {response.status_code}")
    print()

    # Step 4: Test invalid CVE ID format
    print("4. Testing invalid CVE ID format...")
    invalid_cve = "INVALID-CVE"
    response = requests.get(f"{BASE_URL}/api/vulnerabilities/nvd", params={"cve_id": invalid_cve})

    if response.status_code == 422:
        print(f"   ✓ Correctly rejected invalid CVE format (422)")
        print(f"   Error: {response.json()['detail'][0]['msg']}")
    else:
        print(f"   ✗ Should have rejected invalid format (got {response.status_code})")
    print()

    # Step 5: Register a user for community vulnerability tests
    print("5. Registering test user...")
    register_data = {
        "username": "vulntest",
        "email": "vuln@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)

    if response.status_code == 201:
        token = response.json()["access_token"]
        print(f"   ✓ User registered successfully")
        print(f"   Token: {token[:50]}...")
    elif response.status_code == 400 and "already registered" in response.text:
        # User exists, login instead
        print(f"   ⚠ User already exists, logging in...")
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

    # Step 6: Test listing community vulnerabilities (empty at first)
    print("6. Testing list community vulnerabilities...")
    response = requests.get(f"{BASE_URL}/api/vulnerabilities/community")

    if response.status_code == 200:
        vulnerabilities = response.json()
        print(f"   ✓ Retrieved {len(vulnerabilities)} community vulnerability(ies)")
        for vuln in vulnerabilities[:3]:  # Show first 3
            print(f"      - {vuln['comm_id']}: {vuln['description'][:50]}...")
    else:
        print(f"   ✗ Failed to list vulnerabilities: {response.text}")
    print()

    # Step 7: Test pagination
    print("7. Testing pagination (skip=0, limit=5)...")
    response = requests.get(
        f"{BASE_URL}/api/vulnerabilities/community",
        params={"skip": 0, "limit": 5}
    )

    if response.status_code == 200:
        vulnerabilities = response.json()
        print(f"   ✓ Retrieved {len(vulnerabilities)} vulnerability(ies) with limit=5")
    else:
        print(f"   ✗ Pagination failed: {response.text}")
    print()

    # Step 8: Test status filter
    print("8. Testing status filter (status=pending)...")
    response = requests.get(
        f"{BASE_URL}/api/vulnerabilities/community",
        params={"status_filter": "pending"}
    )

    if response.status_code == 200:
        vulnerabilities = response.json()
        print(f"   ✓ Retrieved {len(vulnerabilities)} pending vulnerability(ies)")
    else:
        print(f"   ✗ Status filter failed: {response.text}")
    print()

    # Step 9: Test invalid status filter
    print("9. Testing invalid status filter...")
    response = requests.get(
        f"{BASE_URL}/api/vulnerabilities/community",
        params={"status_filter": "invalid"}
    )

    if response.status_code == 400:
        print(f"   ✓ Correctly rejected invalid status filter (400)")
        print(f"   Error: {response.json()['detail']}")
    else:
        print(f"   ✗ Should have rejected invalid filter (got {response.status_code})")
    print()

    # Step 10: Test getting non-existent community vulnerability
    print("10. Testing get non-existent community vulnerability...")
    response = requests.get(f"{BASE_URL}/api/vulnerabilities/community/NONEXISTENT")

    if response.status_code == 404:
        print(f"   ✓ Correctly returned 404 for non-existent vulnerability")
    else:
        print(f"   ✗ Should have returned 404 (got {response.status_code})")
    print()

    # Step 11: Test clearing cache (requires auth)
    print("11. Testing cache clear endpoint (authenticated)...")
    response = requests.delete(f"{BASE_URL}/api/vulnerabilities/cache", headers=headers)

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Cache cleared successfully")
        print(f"   Entries cleared: {data['entries_cleared']}")
    else:
        print(f"   ✗ Failed to clear cache: {response.text}")
    print()

    # Step 12: Test cache clear without auth
    print("12. Testing cache clear without authentication...")
    response = requests.delete(f"{BASE_URL}/api/vulnerabilities/cache")

    if response.status_code == 401:
        print(f"   ✓ Correctly rejected unauthenticated request (401)")
    else:
        print(f"   ✗ Should have rejected unauthenticated request (got {response.status_code})")
    print()

    # Step 13: Test another CVE (optional, only if network available)
    print("13. Testing another CVE (Heartbleed)...")
    cve_id2 = "CVE-2014-0160"  # Heartbleed
    response = requests.get(f"{BASE_URL}/api/vulnerabilities/nvd", params={"cve_id": cve_id2})

    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Successfully fetched {cve_id2}")
        print(f"   Description: {data['description'][:100]}...")
        print(f"   Cached: {data['cached']}")
    elif response.status_code == 503:
        print(f"   ⚠ NVD API unavailable - skipping")
    else:
        print(f"   ⚠ Request failed: {response.status_code}")
    print()

    print("=" * 70)
    print("Vulnerabilities API tests completed!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    import sys

    try:
        success = test_vulnerabilities_api()
        sys.exit(0 if success else 1)
    except requests.ConnectionError:
        print("✗ Error: Could not connect to server. Is it running on http://localhost:8000?")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
