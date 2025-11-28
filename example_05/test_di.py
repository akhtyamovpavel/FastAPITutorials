"""
Tests demonstrating dependency injection benefits.

This module shows how DI makes testing easier by allowing
us to override dependencies with mocks/stubs.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from typing import AsyncGenerator

from main import (
    app, Base, User, UserCreate, UserUpdate,
    get_db, get_user_repository, get_user_service,
    UserRepository, UserService
)


# =============================================================================
# TEST DATABASE SETUP
# =============================================================================

# Create in-memory database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
test_session_maker = async_sessionmaker(test_engine, expire_on_commit=False)


async def get_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Override for get_db dependency.

    This is the KEY benefit of DI for testing:
    - We can replace the real database with a test database
    - No need to modify application code
    - Tests are isolated from production database
    """
    async with test_session_maker() as session:
        yield session


# Override the dependency
app.dependency_overrides[get_db] = get_test_db


@pytest.fixture
async def setup_database():
    """Create tables before each test, drop after"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# =============================================================================
# INTEGRATION TESTS (Using real dependencies with test database)
# =============================================================================

@pytest.mark.asyncio
async def test_create_user_integration(setup_database):
    """
    Integration test using real dependencies.

    WHAT HAPPENS:
    1. TestClient makes request to /users/
    2. FastAPI resolves dependencies:
       - get_db is overridden to use test database
       - UserRepository is created with test session
       - UserService is created with test repository
    3. User is created in test database
    4. Test database is cleaned up after test
    """
    client = TestClient(app)

    response = client.post(
        "/users/",
        json={
            "username": "test_user",
            "email": "test@example.com",
            "full_name": "Test User"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "test_user"
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_user_integration(setup_database):
    """Test getting a user through the full stack"""
    client = TestClient(app)

    # Create user first
    create_response = client.post(
        "/users/",
        json={
            "username": "test_user",
            "email": "test@example.com"
        }
    )
    user_id = create_response.json()["id"]

    # Get user
    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["username"] == "test_user"


@pytest.mark.asyncio
async def test_duplicate_username_integration(setup_database):
    """Test business logic: duplicate usernames are rejected"""
    client = TestClient(app)

    # Create first user
    client.post(
        "/users/",
        json={"username": "duplicate", "email": "first@example.com"}
    )

    # Try to create user with same username
    response = client.post(
        "/users/",
        json={"username": "duplicate", "email": "second@example.com"}
    )

    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


# =============================================================================
# UNIT TESTS (Using mocked dependencies)
# =============================================================================

class MockUserRepository:
    """
    Mock repository for unit testing.

    This demonstrates another DI benefit:
    - We can test service layer WITHOUT database
    - Tests are faster (no I/O)
    - Tests are more focused (only business logic)
    """

    def __init__(self):
        self.users = {}
        self.next_id = 1

    async def create(self, user_data: UserCreate) -> User:
        user = User(
            id=self.next_id,
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name
        )
        self.users[self.next_id] = user
        self.next_id += 1
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    async def get_by_username(self, username: str) -> User | None:
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        return list(self.users.values())[skip:skip + limit]

    async def update(self, user: User, user_data: UserUpdate) -> User:
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        return user

    async def delete(self, user: User) -> None:
        if user.id in self.users:
            del self.users[user.id]


@pytest.mark.asyncio
async def test_service_create_user_unit():
    """
    Unit test for UserService.create_user().

    BENEFITS OF MOCKING:
    - No database needed
    - Faster execution
    - Isolated test (only tests service logic)
    - Easy to control repository behavior
    """
    mock_repo = MockUserRepository()
    service = UserService(mock_repo)

    user_data = UserCreate(
        username="unit_test",
        email="unit@test.com",
        full_name="Unit Test"
    )

    user = await service.create_user(user_data)

    assert user.username == "unit_test"
    assert user.email == "unit@test.com"
    assert user.id == 1


@pytest.mark.asyncio
async def test_service_duplicate_username_unit():
    """
    Unit test for business rule: no duplicate usernames.

    This test focuses ONLY on the business logic,
    not on database behavior.
    """
    mock_repo = MockUserRepository()
    service = UserService(mock_repo)

    # Create first user
    await service.create_user(UserCreate(username="duplicate", email="first@test.com"))

    # Try to create duplicate
    with pytest.raises(Exception) as exc_info:
        await service.create_user(UserCreate(username="duplicate", email="second@test.com"))

    assert "already exists" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_service_get_user_not_found_unit():
    """Test service error handling when user not found"""
    mock_repo = MockUserRepository()
    service = UserService(mock_repo)

    with pytest.raises(Exception) as exc_info:
        await service.get_user(999)

    assert exc_info.value.status_code == 404


# =============================================================================
# DEPENDENCY OVERRIDE TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_dependency_override():
    """
    Demonstrates how to override specific dependencies for testing.

    This is useful when you want to:
    - Test with mock services
    - Inject specific test data
    - Test error conditions
    """

    class MockService:
        async def get_user(self, user_id: int):
            return User(
                id=user_id,
                username="mocked",
                email="mock@test.com",
                full_name="Mocked User"
            )

    def get_mock_service():
        return MockService()

    # Override service dependency
    app.dependency_overrides[get_user_service] = get_mock_service

    try:
        client = TestClient(app)
        response = client.get("/users/1")

        assert response.status_code == 200
        assert response.json()["username"] == "mocked"
    finally:
        # Clean up override
        del app.dependency_overrides[get_user_service]


# =============================================================================
# REPOSITORY UNIT TESTS
# =============================================================================

@pytest.mark.asyncio
async def test_repository_create(setup_database):
    """Test repository create method directly"""
    async with test_session_maker() as session:
        repo = UserRepository(session)
        user_data = UserCreate(
            username="repo_test",
            email="repo@test.com"
        )

        user = await repo.create(user_data)

        assert user.id is not None
        assert user.username == "repo_test"


@pytest.mark.asyncio
async def test_repository_get_by_username(setup_database):
    """Test repository query methods"""
    async with test_session_maker() as session:
        repo = UserRepository(session)

        # Create user
        await repo.create(UserCreate(username="find_me", email="find@test.com"))

        # Find user
        user = await repo.get_by_username("find_me")
        assert user is not None
        assert user.email == "find@test.com"


"""
RUNNING TESTS:

1. Install pytest and pytest-asyncio:
   pip install pytest pytest-asyncio

2. Run all tests:
   pytest test_di.py -v

3. Run specific test:
   pytest test_di.py::test_create_user_integration -v

4. Run with coverage:
   pytest test_di.py --cov=main --cov-report=html

KEY TESTING CONCEPTS DEMONSTRATED:

1. DEPENDENCY OVERRIDE:
   - app.dependency_overrides allows replacing dependencies
   - Useful for injecting test databases, mocks, stubs
   - No need to modify application code

2. INTEGRATION TESTS:
   - Test full stack with real dependencies
   - Use test database instead of production
   - Verify components work together

3. UNIT TESTS:
   - Test single component in isolation
   - Use mocks for dependencies
   - Faster, more focused tests

4. REPOSITORY TESTS:
   - Test data access layer directly
   - Verify database operations
   - Use test database

BENEFITS OF DI FOR TESTING:

1. ISOLATION: Test components independently
2. SPEED: Unit tests don't need database
3. CONTROL: Easily inject test data or error conditions
4. MAINTAINABILITY: Tests don't break when changing implementations
5. CLARITY: Dependencies are explicit in test setup

TESTING PYRAMID WITH DI:

        /\
       /  \      Few integration tests (slow, comprehensive)
      /____\
     /      \    More unit tests (fast, focused)
    /________\   Many repository tests (medium speed)

DI makes it easy to write tests at all levels!
"""
