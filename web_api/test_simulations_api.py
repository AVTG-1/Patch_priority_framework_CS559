"""
Test script for Simulation Management Endpoints

Tests POST, GET (by ID), and GET (list) operations for simulations.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_simulation_endpoints():
    """Test simulation management endpoints"""

    print("=" * 70)
    print("Testing Simulation Management Endpoints")
    print("=" * 70)
    print()

    # Step 1: Register and login user
    print("1. Registering test user...")
    register_data = {
        "username": "simtest",
        "email": "simtest@test.com",
        "password": "testpass123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)

    if response.status_code == 201:
        token = response.json()["access_token"]
        print(f"   ✓ User registered successfully")
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

    # Step 2: Create a system configuration
    print("2. Creating system configuration...")
    system_config = {
        "name": "Test SCADA System",
        "config_json": json.dumps({
            "system_name": "Test SCADA System",
            "system_class": "Industrial Control System",
            "subsystems": [
                {
                    "id": "hmi_001",
                    "name": "Human Machine Interface",
                    "connected_to": ["plc_001"],
                    "functional_dependencies": ["plc_001"]
                },
                {
                    "id": "plc_001",
                    "name": "Programmable Logic Controller",
                    "connected_to": [],
                    "functional_dependencies": []
                }
            ],
            "vulnerabilities": [
                {
                    "cve_id": "CVE-2024-0001",
                    "description": "SQL Injection vulnerability",
                    "subsystem_id": "hmi_001",
                    "cvss_impact": 8.5,
                    "cvss_exploitability": 7.8,
                    "exploit_present": True,
                    "patch_cost": 15.0,
                    "dependencies": []
                },
                {
                    "cve_id": "CVE-2024-0002",
                    "description": "Buffer overflow vulnerability",
                    "subsystem_id": "plc_001",
                    "cvss_impact": 7.2,
                    "cvss_exploitability": 6.5,
                    "exploit_present": False,
                    "patch_cost": 10.0,
                    "dependencies": []
                }
            ],
            "weights": {
                "functional_weight": 0.6,
                "topological_weight": 0.4
            }
        })
    }
    response = requests.post(f"{BASE_URL}/api/systems", json=system_config, headers=headers)

    if response.status_code == 201:
        system = response.json()
        system_id = system["id"]
        print(f"   ✓ System created successfully")
        print(f"   System ID: {system_id}")
        print(f"   System Name: {system['name']}")
    else:
        print(f"   ✗ System creation failed: {response.text}")
        return False
    print()

    # Step 3: Run simulation with default parameters
    print("3. Running simulation with default parameters...")
    sim_data = {
        "system_id": system_id,
        "rounds": 5
    }
    response = requests.post(f"{BASE_URL}/api/simulations", json=sim_data, headers=headers)

    if response.status_code == 201:
        sim_result = response.json()
        simulation_id = sim_result["simulation_id"]
        print(f"   ✓ Simulation started successfully")
        print(f"   Simulation ID: {simulation_id}")
        print(f"   System: {sim_result['system_name']}")
        print(f"   Rounds: {sim_result['rounds']}")
    else:
        print(f"   ✗ Simulation failed: {response.text}")
        return False
    print()

    # Step 4: Wait for simulation to complete
    print("4. Waiting for simulation to complete (5 seconds)...")
    time.sleep(5)
    print(f"   ✓ Wait completed")
    print()

    # Step 5: Get simulation results
    print("5. Retrieving simulation results...")
    response = requests.get(f"{BASE_URL}/api/simulations/{simulation_id}", headers=headers)

    if response.status_code == 200:
        sim_details = response.json()
        print(f"   ✓ Simulation results retrieved")
        print(f"   ID: {sim_details['id']}")
        print(f"   System: {sim_details['system_name']}")

        # Check if simulation completed
        if "error" in sim_details["results"]:
            print(f"   ⚠ Simulation error: {sim_details['results']['error_message']}")
        elif "status" in sim_details["results"] and sim_details["results"]["status"] == "pending":
            print(f"   ⚠ Simulation still pending")
        else:
            print(f"   Status: Completed")
            if "simulation_metrics" in sim_details["results"]:
                metrics = sim_details["results"]["simulation_metrics"]
                print(f"   Initial RIS: {metrics.get('initial_ris', 'N/A')}")
                print(f"   Final RIS: {metrics.get('final_ris', 'N/A')}")
                print(f"   RIS Reduction: {metrics.get('ris_reduction_percentage', 'N/A'):.2f}%")
    else:
        print(f"   ✗ Failed to retrieve results: {response.text}")
    print()

    # Step 6: Run simulation with custom budgets
    print("6. Running simulation with custom budgets...")
    sim_data2 = {
        "system_id": system_id,
        "rounds": 10,
        "defender_budget": 100.0,
        "attacker_budget": 50.0,
        "patch_grouping_method": "subsystem"
    }
    response = requests.post(f"{BASE_URL}/api/simulations", json=sim_data2, headers=headers)

    if response.status_code == 201:
        sim_result2 = response.json()
        simulation_id2 = sim_result2["simulation_id"]
        print(f"   ✓ Simulation with custom parameters started")
        print(f"   Simulation ID: {simulation_id2}")
        print(f"   Rounds: {sim_result2['rounds']}")
    else:
        print(f"   ✗ Simulation failed: {response.text}")
        return False
    print()

    # Step 7: List all simulations for the system
    print("7. Listing all simulations for the system...")
    response = requests.get(f"{BASE_URL}/api/simulations?system_id={system_id}", headers=headers)

    if response.status_code == 200:
        simulations = response.json()
        print(f"   ✓ Retrieved {len(simulations)} simulation(s)")
        for sim in simulations:
            print(f"      - Simulation {sim['id']}: Created {sim['created_at']}")
    else:
        print(f"   ✗ Failed to list simulations: {response.text}")
    print()

    # Step 8: List all simulations (no filter)
    print("8. Listing all simulations for user...")
    response = requests.get(f"{BASE_URL}/api/simulations", headers=headers)

    if response.status_code == 200:
        simulations = response.json()
        print(f"   ✓ Retrieved {len(simulations)} simulation(s)")
    else:
        print(f"   ✗ Failed to list simulations: {response.text}")
    print()

    # Step 9: Try to access simulation without authentication (should fail)
    print("9. Testing access without authentication (should fail)...")
    response = requests.get(f"{BASE_URL}/api/simulations/{simulation_id}")

    if response.status_code == 401:
        print(f"   ✓ Correctly rejected unauthenticated access (401)")
    else:
        print(f"   ✗ Should have rejected unauthenticated (got {response.status_code})")
    print()

    # Step 10: Register second user
    print("10. Registering second user...")
    user2_register = {
        "username": "simuser2",
        "email": "simuser2@test.com",
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

    # Step 11: Try to access another user's simulation (should fail)
    print("11. Testing access to another user's simulation (should fail)...")
    response = requests.get(f"{BASE_URL}/api/simulations/{simulation_id}", headers=user2_headers)

    if response.status_code == 403:
        print(f"   ✓ Correctly rejected unauthorized access (403)")
    else:
        print(f"   ✗ Should have rejected unauthorized access (got {response.status_code})")
    print()

    # Step 12: Try to run simulation on another user's system (should fail)
    print("12. Testing simulation on another user's system (should fail)...")
    sim_data3 = {
        "system_id": system_id,
        "rounds": 5
    }
    response = requests.post(f"{BASE_URL}/api/simulations", json=sim_data3, headers=user2_headers)

    if response.status_code == 403:
        print(f"   ✓ Correctly rejected unauthorized simulation (403)")
    else:
        print(f"   ✗ Should have rejected unauthorized (got {response.status_code})")
    print()

    # Step 13: Try to run simulation on non-existent system (should fail)
    print("13. Testing simulation on non-existent system...")
    sim_data4 = {
        "system_id": 999999,
        "rounds": 5
    }
    response = requests.post(f"{BASE_URL}/api/simulations", json=sim_data4, headers=headers)

    if response.status_code == 404:
        print(f"   ✓ Correctly returned 404 for non-existent system")
    else:
        print(f"   ✗ Should have returned 404 (got {response.status_code})")
    print()

    # Step 14: Test invalid rounds parameter
    print("14. Testing invalid rounds parameter...")
    sim_data5 = {
        "system_id": system_id,
        "rounds": 150  # Should be max 100
    }
    response = requests.post(f"{BASE_URL}/api/simulations", json=sim_data5, headers=headers)

    if response.status_code == 422:
        print(f"   ✓ Correctly rejected invalid rounds (422)")
    else:
        print(f"   ✗ Should have rejected invalid rounds (got {response.status_code})")
    print()

    # Step 15: Test invalid patch grouping method
    print("15. Testing invalid patch grouping method...")
    sim_data6 = {
        "system_id": system_id,
        "rounds": 5,
        "patch_grouping_method": "invalid_method"
    }
    response = requests.post(f"{BASE_URL}/api/simulations", json=sim_data6, headers=headers)

    if response.status_code == 422:
        print(f"   ✓ Correctly rejected invalid grouping method (422)")
    else:
        print(f"   ✗ Should have rejected invalid method (got {response.status_code})")
    print()

    print("=" * 70)
    print("All simulation management tests completed!")
    print("=" * 70)

    return True


if __name__ == "__main__":
    import sys

    try:
        success = test_simulation_endpoints()
        sys.exit(0 if success else 1)
    except requests.ConnectionError:
        print("✗ Error: Could not connect to server. Is it running on http://localhost:8000?")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
