# Testing Documentation

## Overview

This document provides comprehensive testing guidelines for the AIRRVie Rice Farming Assistant application, covering both backend (FastAPI) and frontend (React/Vite) testing procedures.

---

## Table of Contents

1. [Backend Testing](#backend-testing)
2. [Frontend Testing](#frontend-testing)
3. [Integration Testing](#integration-testing)
4. [Code Coverage Requirements](#code-coverage-requirements)
5. [Test Accounts & Mock Data](#test-accounts--mock-data)
6. [CI/CD Integration](#cicd-integration)

---

## Backend Testing

### Prerequisites

Ensure you have the following installed:
- Python 3.11+
- PostgreSQL database
- Qdrant vector database access
- Required environment variables configured in `.env`

### Test Setup

#### 1. Install Testing Dependencies

Add the following to `RA_Backend/requirements.txt`:

```txt
# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
httpx>=0.27.0
faker>=19.0.0
pytest-mock>=3.11.0
```

Install dependencies:

```bash
cd RA_Backend
pip install -r requirements.txt
```

#### 2. Create Test Directory Structure

```
RA_Backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures and configuration
│   ├── test_auth.py             # Authentication tests
│   ├── test_farms.py            # Farm management tests
│   ├── test_tasks.py            # Task management tests
│   ├── test_journal.py          # Journal entry tests
│   ├── test_weather.py          # Weather API tests
│   ├── test_assistant.py        # AI assistant tests
│   ├── test_voice.py            # Voice processing tests
│   ├── test_uploads.py          # File upload tests
│   ├── test_ml_models.py        # ML model inference tests
│   └── integration/
│       ├── __init__.py
│       ├── test_qdrant.py       # Qdrant RAG integration
│       └── test_full_flow.py    # End-to-end workflows
```

#### 3. Configuration File

Create `RA_Backend/pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    --verbose
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    requires_db: Tests requiring database
    requires_qdrant: Tests requiring Qdrant
    requires_ai: Tests requiring AI models
```

#### 4. Test Fixtures (conftest.py)

Create `RA_Backend/tests/conftest.py`:

```python
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Test database URL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost/test_db")

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def client():
    """Create test client"""
    from main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_user():
    """Mock user data"""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "phone_number": "+1234567890"
    }

@pytest.fixture
def mock_farm():
    """Mock farm data"""
    return {
        "farm_id": 1,
        "farm_name": "Test Farm",
        "location": "Test Location",
        "size": 10.5,
        "user_id": 1
    }

@pytest.fixture
def auth_headers(mock_user):
    """Generate authentication headers"""
    from utils.auth import create_access_token
    token = create_access_token(data={"sub": str(mock_user["user_id"])})
    return {"Authorization": f"Bearer {token}"}
```

### Running Backend Tests

#### Run All Tests

```bash
cd RA_Backend
pytest
```

#### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Tests requiring database
pytest -m requires_db

# Tests requiring Qdrant
pytest -m requires_qdrant

# Exclude slow tests
pytest -m "not slow"
```

#### Run Specific Test Files

```bash
pytest tests/test_auth.py
pytest tests/test_assistant.py
pytest tests/integration/test_qdrant.py
```

#### Run with Coverage Report

```bash
pytest --cov=. --cov-report=html
# View report at htmlcov/index.html
```

### Existing Integration Tests

The following integration tests are already available:

#### 1. RAG Integration Test

Tests Qdrant vector database integration:

```bash
python test_rag_integration.py
```

**What it tests:**
- Qdrant health check
- RAG context retrieval
- Vector search functionality
- Chunk metadata retrieval

#### 2. Voice Integration Test

Tests voice model integration:

```bash
python test_voice_integration.py
```

**What it tests:**
- Backend server startup
- Voice model server availability (port 8005)
- Health endpoint responses

#### 3. Integrated Voice Test

Tests voice model endpoints in main backend:

```bash
python test_integrated_voice.py
```

**What it tests:**
- Voice model endpoints availability
- API documentation accessibility
- Integrated health endpoints

---

## Frontend Testing

### Prerequisites

- Node.js 18+
- npm or yarn

### Test Setup

#### 1. Install Testing Dependencies

Add to `RA_Frontend/package.json`:

```json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "@vitest/ui": "^1.0.0",
    "vitest": "^1.0.0",
    "jsdom": "^23.0.0",
    "@testing-library/react-hooks": "^8.0.1"
  }
}
```

Install dependencies:

```bash
cd RA_Frontend
npm install
```

#### 2. Configure Vitest

Update `RA_Frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup.ts',
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/tests/',
      ],
      lines: 70,
      functions: 70,
      branches: 70,
      statements: 70,
    },
  },
})
```

#### 3. Test Setup File

Create `RA_Frontend/src/tests/setup.ts`:

```typescript
import '@testing-library/jest-dom'
import { expect, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => {},
  }),
})
```

#### 4. Create Test Directory Structure

```
RA_Frontend/src/
├── tests/
│   ├── setup.ts
│   ├── components/
│   │   ├── Dashboard.test.tsx
│   │   ├── FarmCard.test.tsx
│   │   └── TaskList.test.tsx
│   ├── pages/
│   │   ├── Login.test.tsx
│   │   └── Home.test.tsx
│   ├── hooks/
│   │   └── useAuth.test.ts
│   └── utils/
│       └── api.test.ts
```

#### 5. Add Test Scripts

Update `RA_Frontend/package.json` scripts:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
}
```

### Running Frontend Tests

#### Run All Tests

```bash
cd RA_Frontend
npm test
```

#### Run with UI

```bash
npm run test:ui
```

#### Run with Coverage

```bash
npm run test:coverage
# View report at coverage/index.html
```

#### Watch Mode

```bash
npm test -- --watch
```

---

## Integration Testing

### Full Stack Integration Tests

#### Prerequisites

1. Backend server running on `http://localhost:8000`
2. Frontend dev server running on `http://localhost:5173`
3. PostgreSQL database accessible
4. Qdrant database accessible

#### End-to-End Test Flow

Create `RA_Backend/tests/integration/test_full_flow.py`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    """Test user registration and login flow"""
    # Register new user
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "phone_number": "+1234567890",
        "password": "TestPass123!"
    }
    response = await client.post("/api/auth/register", json=register_data)
    assert response.status_code == 201
    
    # Login
    login_data = {
        "username": "testuser",
        "password": "TestPass123!"
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_farm_creation_and_retrieval(client: AsyncClient, auth_headers):
    """Test creating and retrieving farm data"""
    # Create farm
    farm_data = {
        "farm_name": "Test Farm",
        "location": "Test Location",
        "size": 10.5
    }
    response = await client.post(
        "/api/farms",
        json=farm_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    farm_id = response.json()["farm_id"]
    
    # Retrieve farm
    response = await client.get(
        f"/api/farms/{farm_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["farm_name"] == "Test Farm"
```

---

## Code Coverage Requirements

### Backend Coverage Targets

| Component | Minimum Coverage | Target Coverage |
|-----------|-----------------|-----------------|
| API Routes | 75% | 85% |
| Database Operations | 80% | 90% |
| Authentication | 85% | 95% |
| Utilities | 70% | 80% |
| ML Models | 60% | 70% |
| Overall | 70% | 80% |

### Frontend Coverage Targets

| Component | Minimum Coverage | Target Coverage |
|-----------|-----------------|-----------------|
| Components | 70% | 80% |
| Pages | 65% | 75% |
| Hooks | 75% | 85% |
| Utils | 80% | 90% |
| Overall | 70% | 80% |

### Generating Coverage Reports

#### Backend

```bash
cd RA_Backend
pytest --cov=. --cov-report=html --cov-report=term-missing
# Open htmlcov/index.html to view detailed report
```

#### Frontend

```bash
cd RA_Frontend
npm run test:coverage
# Open coverage/index.html to view detailed report
```

---

## Test Accounts & Mock Data

### Test User Accounts

For development and testing purposes, use these pre-configured test accounts:

#### Admin Account
```json
{
  "username": "admin",
  "email": "admin@airrvie.com",
  "password": "Admin123!",
  "role": "admin"
}
```

#### Regular User Account
```json
{
  "username": "testuser",
  "email": "test@airrvie.com",
  "password": "Test123!",
  "role": "user"
}
```

#### Demo Farmer Account
```json
{
  "username": "farmer_demo",
  "email": "farmer@demo.com",
  "password": "Demo123!",
  "role": "user"
}
```

### Mock Data Scripts

#### Initialize Test Database

```bash
cd RA_Backend
python database/init_db.py
python database/add_complete_demo_data.py
```

This creates:
- 5 test users
- 10 sample farms
- 20 sample tasks
- 15 journal entries
- Sample weather data

#### Mock Data for Unit Tests

Create `RA_Backend/tests/fixtures/mock_data.py`:

```python
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()

class MockDataFactory:
    @staticmethod
    def create_user(user_id=None):
        return {
            "user_id": user_id or fake.random_int(1, 10000),
            "username": fake.user_name(),
            "email": fake.email(),
            "phone_number": fake.phone_number(),
            "created_at": datetime.now()
        }
    
    @staticmethod
    def create_farm(user_id=1):
        return {
            "farm_id": fake.random_int(1, 10000),
            "farm_name": f"{fake.city()} Rice Farm",
            "location": fake.address(),
            "size": round(fake.random.uniform(1.0, 50.0), 2),
            "user_id": user_id,
            "created_at": datetime.now()
        }
    
    @staticmethod
    def create_task(farm_id=1):
        return {
            "task_id": fake.random_int(1, 10000),
            "farm_id": farm_id,
            "task_name": fake.sentence(nb_words=3),
            "description": fake.text(max_nb_chars=200),
            "due_date": datetime.now() + timedelta(days=7),
            "status": "pending",
            "priority": fake.random_element(["low", "medium", "high"])
        }
    
    @staticmethod
    def create_journal_entry(farm_id=1):
        return {
            "entry_id": fake.random_int(1, 10000),
            "farm_id": farm_id,
            "entry_text": fake.text(max_nb_chars=500),
            "entry_date": datetime.now(),
            "images": []
        }
```

#### Mock AI Responses

Create `RA_Backend/tests/fixtures/mock_ai.py`:

```python
MOCK_AI_RESPONSES = {
    "disease_detection": {
        "disease": "Blast",
        "confidence": 0.85,
        "recommendations": [
            "Apply fungicide treatment",
            "Improve drainage",
            "Monitor closely for spread"
        ]
    },
    "rag_context": {
        "rag_enabled": True,
        "context_text": "Blast disease is a fungal infection...",
        "chunks_metadata": [
            {
                "score": 0.92,
                "headings_path": "Rice Diseases > Blast",
                "chunk_text": "Blast is caused by the fungus Magnaporthe oryzae..."
            }
        ]
    },
    "voice_transcription": {
        "text": "How do I control blast disease in rice?",
        "language": "en",
        "confidence": 0.95
    }
}
```

### Test Database Reset

Create `RA_Backend/tests/reset_test_db.py`:

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from database.config import get_test_database_url

async def reset_test_database():
    """Drop and recreate test database"""
    engine = create_async_engine(get_test_database_url())
    
    async with engine.begin() as conn:
        # Drop all tables
        await conn.run_sync(Base.metadata.drop_all)
        # Recreate all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Test database reset complete")

if __name__ == "__main__":
    asyncio.run(reset_test_database())
```

---

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd RA_Backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd RA_Backend
          pytest --cov=. --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/test_db
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./RA_Backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: |
          cd RA_Frontend
          npm install
      
      - name: Run tests
        run: |
          cd RA_Frontend
          npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./RA_Frontend/coverage/coverage-final.json
```

---

## Best Practices

### General Testing Guidelines

1. **Test Naming**: Use descriptive names following the pattern `test_<feature>_<scenario>_<expected_result>`
2. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification phases
3. **Isolation**: Each test should be independent and not rely on other tests
4. **Mock External Services**: Mock AI APIs, S3, email services to avoid external dependencies
5. **Test Data Cleanup**: Always clean up test data after tests complete

### Backend Testing Best Practices

- Use `pytest.mark` to categorize tests (unit, integration, slow, etc.)
- Test both success and failure scenarios
- Validate input sanitization and error handling
- Test authentication and authorization for protected endpoints
- Use async fixtures for database operations

### Frontend Testing Best Practices

- Test user interactions, not implementation details
- Use `data-testid` attributes for reliable element selection
- Test accessibility (a11y) features
- Mock API calls to avoid backend dependencies
- Test responsive behavior and edge cases

---

## Troubleshooting

### Common Issues

#### Backend Tests Fail to Connect to Database

**Solution**: Ensure test database URL is correctly configured
```bash
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test_db"
```

#### Qdrant Tests Fail

**Solution**: Check Qdrant connection in `.env`
```bash
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_api_key
```

#### Frontend Tests Timeout

**Solution**: Increase test timeout in `vite.config.ts`
```typescript
test: {
  testTimeout: 10000,
}
```

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)

---

## Contact

For questions or issues with testing, contact the development team or open an issue in the project repository.
