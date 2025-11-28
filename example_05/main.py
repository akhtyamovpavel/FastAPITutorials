"""
FastAPI Dependency Injection Example

This example demonstrates:
1. How FastAPI's Depends() mechanism works internally
2. Multi-level dependency chains
3. Service layer pattern with DI
4. Repository pattern with DI
5. Database session management via DI
6. Benefits for testing and maintainability

Key DI Concepts:
- Dependencies are functions/callables that FastAPI calls automatically
- Results are cached per request (same dependency called multiple times = same instance)
- Dependencies can depend on other dependencies (dependency chain)
- FastAPI handles cleanup (e.g., closing database sessions) automatically
"""

from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, select
from typing import AsyncGenerator, Optional
from pydantic import BaseModel, ConfigDict
from contextlib import asynccontextmanager

# =============================================================================
# DATABASE SETUP
# =============================================================================

DATABASE_URL = "sqlite+aiosqlite:///./example_05.db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    """User database model"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class UserCreate(BaseModel):
    """Schema for creating a user"""
    username: str
    email: str
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    """Schema for user response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: str
    full_name: Optional[str]


# =============================================================================
# DEPENDENCY: DATABASE SESSION
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency.

    HOW IT WORKS:
    1. FastAPI calls this function when a route needs a database session
    2. The function creates a new session using async_session_maker()
    3. The session is yielded to the route handler
    4. After the route handler completes, FastAPI continues execution
    5. The finally block ensures the session is closed (cleanup)

    BENEFITS:
    - Automatic session lifecycle management
    - No need to manually close sessions
    - Each request gets its own session
    - Sessions are properly cleaned up even if errors occur

    CACHING:
    - If multiple dependencies in the same request need get_db(),
      FastAPI calls it only ONCE and reuses the result
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


# =============================================================================
# REPOSITORY LAYER (DATA ACCESS)
# =============================================================================

class UserRepository:
    """
    Repository Pattern: Separates data access logic from business logic

    This class handles all database operations for User entity.
    It receives the database session via dependency injection.

    BENEFITS:
    - Centralized data access logic
    - Easy to test (mock the repository)
    - Database operations abstracted from business logic
    """

    def __init__(self, db: AsyncSession):
        """
        Constructor receives database session via DI.

        When FastAPI creates this class as a dependency, it:
        1. Resolves the db parameter (calls get_db())
        2. Passes the session to this constructor
        3. Creates and caches the UserRepository instance
        """
        self.db = db

    async def create(self, user_data: UserCreate) -> User:
        """Create a new user in the database"""
        user = User(
            username=user_data.username,
            email=user_data.email,
            full_name=user_data.full_name
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination"""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, user: User, user_data: UserUpdate) -> User:
        """Update user with new data"""
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.full_name is not None:
            user.full_name = user_data.full_name

        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def delete(self, user: User) -> None:
        """Delete user from database"""
        await self.db.delete(user)
        await self.db.commit()


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Dependency factory for UserRepository.

    HOW DEPENDENCY CHAIN WORKS:
    1. Route handler requests UserRepository (via Depends(get_user_repository))
    2. FastAPI sees that get_user_repository needs db: AsyncSession
    3. FastAPI calls get_db() to get the session (or reuses cached one)
    4. FastAPI calls get_user_repository(db=session)
    5. Returns UserRepository instance to the route handler

    BENEFITS:
    - Declarative dependency specification
    - Automatic resolution of dependency chains
    - Easy to swap implementations for testing
    """
    return UserRepository(db)


# =============================================================================
# SERVICE LAYER (BUSINESS LOGIC)
# =============================================================================

class UserService:
    """
    Service Layer: Contains business logic and orchestrates repository operations

    This layer sits between routes and data access:
    - Routes handle HTTP concerns (parsing, validation, responses)
    - Services handle business logic (validation, orchestration)
    - Repositories handle data access (database operations)

    BENEFITS:
    - Business logic separated from HTTP and data layers
    - Reusable across different interfaces (API, CLI, etc.)
    - Easy to test business rules independently
    """

    def __init__(self, repository: UserRepository):
        """
        Constructor receives repository via DI.

        DEPENDENCY CHAIN:
        Route → UserService → UserRepository → Database Session
        """
        self.repository = repository

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Business logic for creating a user.

        This method adds business rules like:
        - Checking if username already exists
        - Validating email format (could be added)
        - Additional business validations
        """
        # Business rule: Username must be unique
        existing_user = await self.repository.get_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username '{user_data.username}' already exists"
            )

        return await self.repository.create(user_data)

    async def get_user(self, user_id: int) -> User:
        """Get user by ID with error handling"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {user_id} not found"
            )
        return user

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """List all users with pagination"""
        return await self.repository.get_all(skip, limit)

    async def update_user(self, user_id: int, user_data: UserUpdate) -> User:
        """Update user with business logic validation"""
        user = await self.get_user(user_id)  # Reuses business logic
        return await self.repository.update(user, user_data)

    async def delete_user(self, user_id: int) -> None:
        """Delete user with validation"""
        user = await self.get_user(user_id)
        await self.repository.delete(user)


def get_user_service(
    repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    """
    Dependency factory for UserService.

    FULL DEPENDENCY CHAIN:
    1. Route needs UserService
    2. UserService needs UserRepository
    3. UserRepository needs AsyncSession
    4. AsyncSession is created by get_db()

    FastAPI resolves this automatically:
    get_db() → UserRepository → UserService → Route Handler

    CACHING:
    All dependencies are cached per request:
    - get_db() called once → same session for all dependencies
    - get_user_repository() called once → same repository instance
    - get_user_service() called once → same service instance
    """
    return UserService(repository)


# =============================================================================
# APPLICATION SETUP
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Creates database tables on startup, cleans up on shutdown.
    """
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown: Close engine
    await engine.dispose()


app = FastAPI(
    title="Dependency Injection Example",
    description="Demonstrates FastAPI DI with Repository and Service patterns",
    lifespan=lifespan
)


# =============================================================================
# ROUTES (API ENDPOINTS)
# =============================================================================

@app.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """
    Create a new user.

    DEPENDENCY INJECTION IN ACTION:
    1. FastAPI parses request body into UserCreate
    2. FastAPI sees service: UserService = Depends(get_user_service)
    3. FastAPI calls get_user_service():
       a. Which needs UserRepository
       b. Which needs AsyncSession
       c. Which is created by get_db()
    4. FastAPI passes the service to this function
    5. After function returns, FastAPI cleans up (closes db session)

    BENEFITS FOR TESTING:
    - Can override get_user_service to return mock service
    - No need to modify route code for testing
    - Dependencies are explicit and clear
    """
    return await service.create_user(user_data)


@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """
    Get user by ID.

    Notice: We don't create service manually, FastAPI does it for us.
    """
    return await service.get_user(user_id)


@app.get("/users/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service)
):
    """
    List all users with pagination.

    QUERY PARAMETERS AND DI:
    - skip and limit are query parameters (parsed from URL)
    - service is injected via DI
    - FastAPI handles both automatically
    """
    return await service.list_users(skip, limit)


@app.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service)
):
    """Update user information."""
    return await service.update_user(user_id, user_data)


@app.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service)
):
    """Delete user."""
    await service.delete_user(user_id)
    return None


# =============================================================================
# DEMONSTRATION ENDPOINT
# =============================================================================

@app.get("/dependency-info")
async def dependency_info(
    service: UserService = Depends(get_user_service),
    repository: UserRepository = Depends(get_user_repository),
    db: AsyncSession = Depends(get_db)
):
    """
    Demonstrates dependency caching.

    IMPORTANT: Even though we request three dependencies here,
    get_db() is called only ONCE for this request.

    The same database session is:
    1. Passed to repository
    2. Passed to service (via repository)
    3. Passed directly to this function

    You can verify this by checking that:
    - repository.db is db (same object)
    - service.repository.db is db (same object)

    This is FastAPI's dependency caching in action!
    """
    return {
        "message": "Dependency injection demonstration",
        "dependencies": {
            "service_type": type(service).__name__,
            "repository_type": type(repository).__name__,
            "db_type": type(db).__name__,
            "same_db_instance": service.repository.db is db,
            "explanation": (
                "All three dependencies (service, repository, db) are resolved "
                "from a single call to get_db(). FastAPI caches the result and "
                "reuses it for all dependencies in this request."
            )
        },
        "dependency_chain": [
            "1. FastAPI receives request",
            "2. Calls get_db() → creates AsyncSession",
            "3. Passes session to get_user_repository() → creates UserRepository",
            "4. Passes repository to get_user_service() → creates UserService",
            "5. Passes all to route handler",
            "6. After response, closes AsyncSession (cleanup)"
        ]
    }


# =============================================================================
# HOW TO RUN
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
