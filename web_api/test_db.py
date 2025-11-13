"""
Test script to verify database initialization

Run this to test database setup and models.
"""

import sys
from pathlib import Path

# Ensure we can import from web_api
sys.path.insert(0, str(Path(__file__).parent))

from database import init_db, get_db_session
from models import User, SystemConfig, SimulationRun, CommunityVulnerability, VulnerabilityStatus


def test_database_initialization():
    """Test database initialization and basic CRUD operations"""

    print("=" * 70)
    print("Testing Database Initialization")
    print("=" * 70)
    print()

    # Initialize database
    print("1. Initializing database...")
    init_db()
    print("   ✓ Database initialized")
    print()

    # Get database session
    db = get_db_session()

    try:
        # Test User creation
        print("2. Testing User model...")
        test_user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="$2b$12$dummy_hashed_password_for_testing",  # Dummy hash for testing
            is_admin=False
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"   ✓ Created user: {test_user}")
        print(f"   User dict: {test_user.to_dict()}")
        print()

        # Test SystemConfig creation
        print("3. Testing SystemConfig model...")
        test_config = SystemConfig(
            user_id=test_user.id,
            name="Test SCADA System",
            config_json='{"system_name": "Test System", "subsystems": []}'
        )
        db.add(test_config)
        db.commit()
        db.refresh(test_config)
        print(f"   ✓ Created system config: {test_config}")
        print(f"   Config dict: {test_config.to_dict()}")
        print()

        # Test SimulationRun creation
        print("4. Testing SimulationRun model...")
        test_run = SimulationRun(
            system_config_id=test_config.id,
            parameters_json='{"rounds": 5, "patch_grouping_method": "dependencies"}',
            results_json='{"patch_priority_list": ["CVE-2024-0001"], "ris_summary": [10.0, 5.0]}'
        )
        db.add(test_run)
        db.commit()
        db.refresh(test_run)
        print(f"   ✓ Created simulation run: {test_run}")
        print(f"   Run dict: {test_run.to_dict()}")
        print()

        # Test CommunityVulnerability creation
        print("5. Testing CommunityVulnerability model...")
        test_vuln = CommunityVulnerability(
            comm_id="COMM-CVE-2024-001",
            reporter_id=test_user.id,
            description="Test vulnerability for SQL injection",
            cvss_impact=8.5,
            cvss_exploitability=7.8,
            status=VulnerabilityStatus.UNVERIFIED,
            affected_subsystem_type="web_server",
            exploit_present=True,
            patch_cost_estimate=15.0,
            upvotes=5,
            downvotes=1
        )
        db.add(test_vuln)
        db.commit()
        db.refresh(test_vuln)
        print(f"   ✓ Created community vulnerability: {test_vuln}")
        print(f"   Vuln dict: {test_vuln.to_dict()}")
        print(f"   Vote score: {test_vuln.get_vote_score()}")
        print()

        # Test relationships
        print("6. Testing relationships...")
        # User -> SystemConfigs
        user_configs = db.query(SystemConfig).filter(SystemConfig.user_id == test_user.id).all()
        print(f"   ✓ User has {len(user_configs)} system config(s)")

        # SystemConfig -> SimulationRuns
        config_runs = db.query(SimulationRun).filter(SimulationRun.system_config_id == test_config.id).all()
        print(f"   ✓ System config has {len(config_runs)} simulation run(s)")

        # User -> CommunityVulnerabilities
        user_vulns = db.query(CommunityVulnerability).filter(CommunityVulnerability.reporter_id == test_user.id).all()
        print(f"   ✓ User has reported {len(user_vulns)} vulnerability(ies)")
        print()

        # Test queries
        print("7. Testing queries...")
        # Query all users
        all_users = db.query(User).all()
        print(f"   ✓ Total users: {len(all_users)}")

        # Query unverified vulnerabilities
        unverified = db.query(CommunityVulnerability).filter(
            CommunityVulnerability.status == VulnerabilityStatus.UNVERIFIED
        ).all()
        print(f"   ✓ Unverified vulnerabilities: {len(unverified)}")
        print()

        print("=" * 70)
        print("All database tests passed! ✓")
        print("=" * 70)
        print()
        print(f"Database location: {Path(__file__).parent / 'patch_priority.db'}")

    except Exception as e:
        print(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

    return True


if __name__ == "__main__":
    success = test_database_initialization()
    sys.exit(0 if success else 1)
