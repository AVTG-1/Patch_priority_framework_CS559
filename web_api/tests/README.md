# Phase 1 Tests - Backend API Foundation

This directory contains comprehensive tests for Phase 1 of the Patch Priority Framework Web API.

## What is Tested

### Phase 1 Components
- FastAPI app initialization with health endpoint
- Backend integration bridge (load_system_from_config, run_simulation)
- SQLAlchemy database setup with SQLite
- Database models (User, SystemConfig, SimulationRun, CommunityVulnerability)
- JWT authentication system (register, login, token validation)

### Test Coverage

**43 total tests** covering:

1. **Basic Application Endpoints** (2 tests)
   - Health check endpoint
   - Root API information endpoint

2. **User Registration** (10 tests)
   - Successful registration
   - Duplicate username/email validation
   - Invalid data validation (short username, invalid email, weak password, special characters)
   - Missing required fields

3. **User Login** (4 tests)
   - Successful login
   - Wrong password rejection
   - Non-existent user handling
   - Missing credentials validation

4. **Protected Routes** (4 tests)
   - Access with valid token
   - Access without token (401)
   - Access with invalid token (401)
   - Malformed authorization header

5. **Simulation Endpoint** (1 test)
   - Test simulation with example system

6. **Database Models** (8 tests)
   - User model creation and to_dict()
   - SystemConfig with foreign key relationships
   - SimulationRun with relationships
   - CommunityVulnerability with all fields
   - Vulnerability status enum values
   - Cascade delete on user removal

7. **Authentication Utilities** (3 tests)
   - Password hashing and verification
   - JWT token creation and validation
   - Invalid token handling

8. **Backend Bridge** (1 test)
   - System summary extraction

9. **Edge Cases** (5 tests)
   - Very long username
   - Empty credentials
   - Vote score edge cases (zero, negative, large values)
   - CVSS boundary values (0.0, 5.0, 10.0)
   - Concurrent user registration

10. **Database Queries** (4 tests)
    - Query by username
    - Query by email
    - Filter vulnerabilities by status
    - Query configs by user

11. **Data Validation** (1 test)
    - Schema validation with invalid inputs

## Running the Tests

### Prerequisites

Make sure you're in the `web_api` directory and have installed all dependencies:

```bash
cd web_api
pip install -r requirements.txt
```

### Run All Tests

```bash
# Standard run
python -m pytest tests/test_phase1.py -v

# With verbose output
python -m pytest tests/test_phase1.py -vv

# Stop on first failure
python -m pytest tests/test_phase1.py -x
```

### Run Specific Test Classes

```bash
# Test only authentication
python -m pytest tests/test_phase1.py::TestUserRegistration -v
python -m pytest tests/test_phase1.py::TestUserLogin -v

# Test only database models
python -m pytest tests/test_phase1.py::TestDatabaseModels -v

# Test edge cases
python -m pytest tests/test_phase1.py::TestEdgeCases -v
```

### Run with Coverage

```bash
# Terminal coverage report
python -m pytest tests/test_phase1.py --cov=. --cov-report=term-missing

# HTML coverage report (creates htmlcov/ directory)
python -m pytest tests/test_phase1.py --cov=. --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Tests

```bash
# Run single test by name
python -m pytest tests/test_phase1.py::TestUserRegistration::test_register_new_user_success -v

# Run tests matching pattern
python -m pytest tests/test_phase1.py -k "login" -v
python -m pytest tests/test_phase1.py -k "register" -v
python -m pytest tests/test_phase1.py -k "database" -v
```

## Test Results

All 43 tests pass successfully:

```
============================= test session starts ==============================
collected 43 items

tests/test_phase1.py::TestBasicEndpoints::test_health_endpoint PASSED    [  2%]
tests/test_phase1.py::TestBasicEndpoints::test_root_endpoint PASSED      [  4%]
...
======================== 43 passed, 7 warnings in 8.44s ========================
```

## Code Coverage

Current coverage for Phase 1 modules:

| Module           | Coverage | Missing Lines |
|------------------|----------|---------------|
| auth.py          | 92%      | Minor edge cases |
| backend_bridge.py| 100%     | Fully covered |
| schemas.py       | 100%     | Fully covered |
| models.py        | 90%      | Minor methods |
| main.py          | 87%      | Error handlers |
| database.py      | 70%      | Utility functions |
| **Overall**      | **74%**  | **>80% for tested modules** |

## Fixtures

The test suite uses pytest fixtures defined in `conftest.py`:

- `db_session`: Fresh in-memory SQLite database for each test
- `client`: FastAPI TestClient with database override
- `sample_user_data`: Sample user registration data
- `sample_user`: Pre-created user in database
- `admin_user`: Pre-created admin user
- `auth_token`: JWT token for sample user
- `auth_headers`: Authorization headers with bearer token
- `sample_system_config`: Sample system configuration
- `sample_simulation_run`: Sample simulation run
- `sample_community_vulnerability`: Sample vulnerability

## Test Independence

All tests are independent and can run in any order:
- Each test uses fresh database (in-memory SQLite)
- Database is created before test and destroyed after
- No shared state between tests
- Tests use fixtures for setup/teardown

## Parametrized Tests

Several tests use `@pytest.mark.parametrize` for data-driven testing:

```python
@pytest.mark.parametrize("invalid_data,expected_error", [
    ({"username": "ab", ...}, "at least 3 characters"),
    ({"username": "test", "email": "invalid", ...}, "valid email"),
    ...
])
def test_register_invalid_data(self, client, invalid_data, expected_error):
    # Test runs once for each parameter combination
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd web_api
    pip install -r requirements.txt
    python -m pytest tests/test_phase1.py -v --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Adding New Tests

When adding new functionality to Phase 1:

1. Add test fixtures to `conftest.py` if needed
2. Create test methods in appropriate test class
3. Use descriptive docstrings
4. Test both success and failure cases
5. Run coverage to ensure >80% coverage
6. Ensure tests are independent

Example:

```python
class TestNewFeature:
    """Test new feature XYZ"""

    def test_new_feature_success(self, client, sample_user):
        """
        Test successful operation of new feature.

        Validates:
        - Status code 200
        - Correct response structure
        """
        response = client.get("/api/new-feature")
        assert response.status_code == 200
```

## Troubleshooting

### ImportError: No module named 'fastapi'

Make sure you're running tests from the `web_api` directory:

```bash
cd web_api
python -m pytest tests/test_phase1.py -v
```

### Database errors

Tests use in-memory SQLite, no cleanup needed. If you see database errors:

```bash
# Delete any test database files
rm -f patch_priority.db test.db
```

### Fixture not found

Make sure `conftest.py` is in the `tests/` directory and pytest can find it.

## Contact

For questions about the test suite, refer to the test docstrings or main project documentation.
