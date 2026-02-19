# 8. Testing Documentation

## 8.1 Overview

This section documents the comprehensive testing strategy, infrastructure, and procedures for the AIRRVie Rice Farming Assistant application. Testing encompasses both backend (FastAPI/Python) and frontend (React/Vite) components, integration workflows, code quality assurance, and continuous validation processes. All testing follows industry best practices, supports automated execution, and maintains high code coverage standards to ensure application reliability, security, and performance.

The testing framework supports unit testing, integration testing, end-to-end workflows, performance validation, and security verification. It integrates with CI/CD pipelines for automated quality gates and provides comprehensive reporting for code coverage and test results.

## 8.2 Testing Architecture

### Testing Strategy

**Testing Pyramid:**
- **Unit Tests (70%):** Individual component and function validation
- **Integration Tests (20%):** Inter-component and API integration verification
- **End-to-End Tests (10%):** Complete user workflow validation

**Testing Frameworks:**
- **Backend:** pytest with async support
- **Frontend:** Vitest with React Testing Library
- **Integration:** httpx AsyncClient for API testing
- **Mocking:** pytest-mock, Faker for test data generation

**Test Environment Configuration:**
- **Development:** Local test database and mock services
- **CI/CD:** Containerized test environment with PostgreSQL and Redis
- **Staging:** Production-like environment for integration tests

**Code Coverage Standards:**
- Minimum overall coverage: 70%
- Critical components (auth, payments): 85%+
- Automated coverage reporting via CI/CD
- HTML and terminal coverage reports

**Supported Test Types:**
- Unit tests for isolated component logic
- Integration tests for API endpoints and database operations
- Functional tests for business logic workflows
- Performance tests for response time validation
- Security tests for authentication and authorization

All tests are automated, isolated, and deterministic to ensure reliable execution across environments.

## 8.3 Backend Testing Framework

### Framework Architecture

**Technology Stack:**
- **Test Runner:** pytest 7.4+
- **Async Support:** pytest-asyncio 0.21+
- **HTTP Client:** httpx for API testing
- **Coverage Tool:** pytest-cov 4.1+
- **Mock Data:** Faker 19.0+
- **Database:** SQLAlchemy with async support

**Test Organization:**
```
RA_Backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures and configuration
│   ├── test_auth.py             # Authentication and authorization
│   ├── test_users.py            # User management
│   ├── test_farms.py            # Farm CRUD operations
│   ├── test_plots.py            # Plot management
│   ├── test_tasks.py            # Task tracking
│   ├── test_journal.py          # Journal entries
│   ├── test_weather.py          # Weather API integration
│   ├── test_assistant.py        # AI assistant logic
│   ├── test_voice.py            # Voice processing
│   ├── test_uploads.py          # File upload handling
│   ├── test_ml_models.py        # ML inference
│   ├── integration/
│   │   ├── test_qdrant.py       # Vector database integration
│   │   ├── test_full_flow.py    # End-to-end workflows
│   │   └── test_api_security.py # Security validation
│   └── fixtures/
│       ├── mock_data.py         # Test data factories
│       └── mock_ai.py           # AI response mocks
```

**Configuration (pytest.ini):**
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

### Test Dependencies

**Required Packages (requirements.txt):**
```txt
# Testing Dependencies
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
httpx>=0.27.0
faker>=19.0.0
```

**Installation:**
```bash
cd RA_Backend
pip install -r requirements.txt
```

### Fixture Configuration

**Core Fixtures (conftest.py):**

**Event Loop Fixture:**
```python
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

**Database Session Fixture:**
```python
@pytest.fixture
async def db_session():
    """Provide async database session for tests"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        await session.rollback()
```

**HTTP Client Fixture:**
```python
@pytest.fixture
async def client():
    """Provide async HTTP client for API testing"""
    from main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

**Authentication Fixture:**
```python
@pytest.fixture
def auth_headers(mock_user):
    """Generate JWT authentication headers"""
    from utils.auth import create_access_token
    token = create_access_token(data={"sub": str(mock_user["user_id"])})
    return {"Authorization": f"Bearer {token}"}
```

**Mock User Fixture:**
```python
@pytest.fixture
def mock_user():
    """Provide mock user data"""
    return {
        "user_id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "phone_number": "+1234567890"
    }
```

## 8.4 Frontend Testing Framework

### Framework Architecture

**Technology Stack:**
- **Test Runner:** Vitest 1.0+
- **Component Testing:** React Testing Library 14.0+
- **DOM Assertions:** @testing-library/jest-dom 6.1+
- **User Interactions:** @testing-library/user-event 14.5+
- **Test Environment:** jsdom 23.0+
- **Coverage:** Vitest coverage with v8 provider

**Test Organization:**
```
RA_Frontend/src/
├── tests/
│   ├── setup.ts                 # Global test configuration
│   ├── components/
│   │   ├── Dashboard.test.tsx
│   │   ├── FarmCard.test.tsx
│   │   ├── TaskList.test.tsx
│   │   └── AssistantChat.test.tsx
│   ├── pages/
│   │   ├── Login.test.tsx
│   │   ├── Register.test.tsx
│   │   ├── Home.test.tsx
│   │   └── FarmDetails.test.tsx
│   ├── hooks/
│   │   ├── useAuth.test.ts
│   │   ├── useFarms.test.ts
│   │   └── useWeather.test.ts
│   └── utils/
│       ├── api.test.ts
│       └── validation.test.ts
```

**Vitest Configuration (vite.config.ts):**
```typescript
export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/tests/setup.ts',
    css: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'src/tests/'],
      lines: 70,
      functions: 70,
      branches: 70,
      statements: 70,
    },
  },
})
```

### Test Dependencies

**Required Packages (package.json):**
```json
{
  "devDependencies": {
    "@testing-library/react": "^14.0.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "@vitest/ui": "^1.0.0",
    "vitest": "^1.0.0",
    "jsdom": "^23.0.0"
  }
}
```

**Installation:**
```bash
cd RA_Frontend
npm install
```

### Test Setup Configuration

**Global Setup (src/tests/setup.ts):**
```typescript
import '@testing-library/jest-dom'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

afterEach(() => {
  cleanup()
})

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

**Test Scripts (package.json):**
```json
{
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:watch": "vitest --watch"
  }
}
```

## 8.5 Test Execution Commands

### Backend Test Execution

**Run All Tests:**
```bash
cd RA_Backend
pytest
```

**Run by Test Category:**
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Database-dependent tests
pytest -m requires_db

# Qdrant-dependent tests
pytest -m requires_qdrant

# Exclude slow tests
pytest -m "not slow"
```

**Run Specific Test Files:**
```bash
pytest tests/test_auth.py
pytest tests/test_assistant.py
pytest tests/integration/test_qdrant.py
```

**Run with Coverage:**
```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
# View HTML report: htmlcov/index.html
```

**Run in Parallel:**
```bash
pytest -n auto
```

### Frontend Test Execution

**Run All Tests:**
```bash
cd RA_Frontend
npm test
```

**Run with UI:**
```bash
npm run test:ui
```

**Run with Coverage:**
```bash
npm run test:coverage
# View HTML report: coverage/index.html
```

**Watch Mode:**
```bash
npm run test:watch
```

**Run Specific Test Files:**
```bash
npm test -- tests/components/Dashboard.test.tsx
```

### Existing Integration Tests

**RAG Integration Test:**
```bash
cd RA_Backend
python test_rag_integration.py
```

**Features Tested:**
- Qdrant vector database connectivity
- RAG context retrieval accuracy
- Vector similarity search
- Chunk metadata extraction
- Health check validation

**Voice Integration Test:**
```bash
cd RA_Backend
python test_voice_integration.py
```

**Features Tested:**
- Backend server startup validation
- Voice model server availability (port 8005)
- Health endpoint responses
- Integration with main API

**Integrated Voice Test:**
```bash
cd RA_Backend
python test_integrated_voice.py
```

**Features Tested:**
- Voice model endpoint availability
- API documentation accessibility
- Health endpoint integration
- Audio processing workflows

## 8.6 Test Data and Mock Accounts

### Pre-configured Test Accounts

**Administrator Account:**
```json
{
  "username": "admin",
  "email": "admin@airrvie.com",
  "password": "Admin123!",
  "role": "admin",
  "verified": true
}
```

**Standard User Account:**
```json
{
  "username": "testuser",
  "email": "test@airrvie.com",
  "password": "Test123!",
  "role": "user",
  "verified": true
}
```

**Demo Farmer Account:**
```json
{
  "username": "farmer_demo",
  "email": "farmer@demo.com",
  "password": "Demo123!",
  "role": "user",
  "verified": true
}
```

### Mock Data Generation

**Initialize Test Database:**
```bash
cd RA_Backend
python database/init_db.py
python database/add_complete_demo_data.py
```

**Generated Test Data:**
- 5 test user accounts
- 10 sample farms with location metadata
- 25 plots with agricultural details
- 30 tasks across different statuses
- 20 journal entries with timestamps
- Sample weather data for multiple locations

**Mock Data Factory (tests/fixtures/mock_data.py):**
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
            "user_id": user_id
        }
    
    @staticmethod
    def create_task(plot_id=1):
        return {
            "task_id": fake.random_int(1, 10000),
            "plot_id": plot_id,
            "title": fake.sentence(nb_words=4),
            "description": fake.text(max_nb_chars=200),
            "due_date": datetime.now() + timedelta(days=7),
            "status": "pending",
            "priority": fake.random_element(["low", "medium", "high"])
        }
```

**Mock AI Responses (tests/fixtures/mock_ai.py):**
```python
MOCK_AI_RESPONSES = {
    "disease_detection": {
        "disease": "Blast",
        "confidence": 0.85,
        "recommendations": [
            "Apply fungicide treatment",
            "Improve field drainage",
            "Monitor for disease spread"
        ]
    },
    "rag_context": {
        "rag_enabled": True,
        "context_text": "Blast disease information...",
        "chunks_metadata": [{
            "score": 0.92,
            "headings_path": "Rice Diseases > Blast",
            "chunk_text": "Detailed information..."
        }]
    }
}
```

## 8.7 Code Coverage Standards

### Coverage Requirements by Component

| Component | Minimum Coverage | Target Coverage | Critical Path |
|-----------|------------------|-----------------|---------------|
| **Backend** |
| API Routes | 75% | 85% | Required |
| Authentication | 85% | 95% | Critical |
| Database Operations | 80% | 90% | Required |
| AI Assistant | 70% | 80% | Recommended |
| ML Models | 60% | 75% | Recommended |
| Utilities | 70% | 80% | Required |
| Voice Processing | 65% | 75% | Recommended |
| **Frontend** |
| Components | 70% | 80% | Required |
| Pages | 65% | 75% | Required |
| Hooks | 75% | 85% | Required |
| API Utilities | 80% | 90% | Critical |
| Validation | 75% | 85% | Required |
| **Overall** | 70% | 80% | Required |

### Coverage Report Generation

**Backend Coverage:**
```bash
cd RA_Backend
pytest --cov=. --cov-report=html --cov-report=term-missing
# HTML Report: htmlcov/index.html
# Terminal: Shows uncovered lines
```

**Frontend Coverage:**
```bash
cd RA_Frontend
npm run test:coverage
# HTML Report: coverage/index.html
# Terminal: Coverage summary
```

**Coverage Enforcement:**
- CI/CD pipeline fails if coverage drops below minimum threshold
- Pull requests require coverage maintenance or improvement
- Critical components enforce stricter coverage requirements
- Coverage reports uploaded to code quality platforms

## 8.8 Integration and End-to-End Testing

### Integration Test Architecture

**Test Scope:**
- API endpoint integration
- Database transaction workflows
- External service integration (Qdrant, S3, Weather API)
- Authentication and authorization flows
- File upload and processing
- AI model inference pipelines

**Example Integration Test (tests/integration/test_full_flow.py):**

**User Registration and Authentication Flow:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_registration_and_login(client: AsyncClient):
    # Register new user
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!"
    }
    response = await client.post("/api/auth/register", json=register_data)
    assert response.status_code == 201
    
    # Login with credentials
    login_data = {
        "username": "testuser",
        "password": "TestPass123!"
    }
    response = await client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
```

**Farm and Plot Management Flow:**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_farm_and_plot_workflow(client: AsyncClient, auth_headers):
    # Create farm
    farm_data = {
        "farm_name": "Test Farm",
        "province": "Test Province",
        "district": "Test District",
        "address": "123 Test St"
    }
    response = await client.post("/api/farms", json=farm_data, headers=auth_headers)
    assert response.status_code == 201
    farm_id = response.json()["farm_id"]
    
    # Create plot within farm
    plot_data = {
        "farm_id": farm_id,
        "area": 5000,
        "soil_type": "Clay loam",
        "rice_variety": "IR64"
    }
    response = await client.post("/api/plots", json=plot_data, headers=auth_headers)
    assert response.status_code == 201
```

### End-to-End Test Prerequisites

**Environment Requirements:**
- Backend running on http://localhost:8000
- Frontend running on http://localhost:5173
- PostgreSQL database accessible
- Qdrant vector database accessible
- Test data initialized
- Environment variables configured

**Integration Test Execution:**
```bash
pytest -m integration --verbose
```

## 8.9 Continuous Integration and Deployment

### CI/CD Pipeline Configuration

**GitHub Actions Workflow (.github/workflows/tests.yml):**

**Backend Test Job:**
```yaml
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
```

**Frontend Test Job:**
```yaml
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

**Pipeline Triggers:**
- Push to main or develop branches
- Pull request creation or updates
- Manual workflow dispatch
- Scheduled nightly builds

**Quality Gates:**
- All tests must pass
- Code coverage must meet minimum thresholds
- No critical security vulnerabilities
- Linting and formatting checks pass

## 8.10 Testing Best Practices

### General Testing Principles

**Test Naming Convention:**
```
test_<component>_<scenario>_<expected_result>

Examples:
- test_user_login_with_valid_credentials_returns_token
- test_farm_creation_without_auth_returns_401
- test_task_completion_updates_status_to_completed
```

**Test Structure (Arrange-Act-Assert):**
```python
def test_example():
    # Arrange: Set up test data and preconditions
    user = create_test_user()
    
    # Act: Execute the operation being tested
    result = perform_operation(user)
    
    # Assert: Verify expected outcomes
    assert result.status == "success"
```

**Test Isolation:**
- Each test is independent and self-contained
- Tests do not rely on execution order
- Database state is reset between tests
- External dependencies are mocked
- No shared mutable state between tests

**Mock External Dependencies:**
- AI API calls (OpenAI, Qwen)
- Cloud storage (S3)
- Email services
- Weather APIs
- Payment gateways
- Real-time data sources

### Backend Testing Guidelines

**Use Test Markers:**
```python
@pytest.mark.unit
@pytest.mark.requires_db
@pytest.mark.slow
async def test_complex_operation():
    pass
```

**Test Both Success and Failure Paths:**
```python
async def test_login_success():
    # Test valid credentials

async def test_login_invalid_password():
    # Test authentication failure

async def test_login_nonexistent_user():
    # Test user not found
```

**Validate Input Sanitization:**
```python
async def test_sql_injection_prevention():
    malicious_input = "'; DROP TABLE users; --"
    # Verify input is sanitized
```

**Test Authorization:**
```python
async def test_protected_endpoint_without_auth():
    # Should return 401

async def test_protected_endpoint_with_expired_token():
    # Should return 401

async def test_access_other_user_data():
    # Should return 403
```

### Frontend Testing Guidelines

**Test User Interactions:**
```typescript
test('clicking submit button calls API', async () => {
  const user = userEvent.setup()
  render(<LoginForm />)
  
  await user.type(screen.getByLabelText('Email'), 'test@example.com')
  await user.type(screen.getByLabelText('Password'), 'password123')
  await user.click(screen.getByRole('button', { name: 'Login' }))
  
  expect(mockLoginAPI).toHaveBeenCalled()
})
```

**Use Data Test IDs:**
```tsx
<button data-testid="submit-button">Submit</button>

// In test
const button = screen.getByTestId('submit-button')
```

**Mock API Calls:**
```typescript
vi.mock('../api/auth', () => ({
  login: vi.fn(() => Promise.resolve({ token: 'mock-token' }))
}))
```

**Test Accessibility:**
```typescript
test('form has proper ARIA labels', () => {
  render(<LoginForm />)
  expect(screen.getByLabelText('Email')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Login' })).toBeEnabled()
})
```

## 8.11 Troubleshooting and Common Issues

### Backend Testing Issues

**Database Connection Failures:**
```bash
# Set test database URL
export TEST_DATABASE_URL="postgresql+asyncpg://user:pass@localhost/test_db"

# Verify PostgreSQL is running
pg_isready -h localhost -p 5432
```

**Qdrant Connection Issues:**
```bash
# Verify Qdrant credentials in .env
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_api_key

# Test connection
python test_rag_integration.py
```

**Async Test Failures:**
```python
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Verify asyncio_mode in pytest.ini
asyncio_mode = auto
```

### Frontend Testing Issues

**Test Timeouts:**
```typescript
// Increase timeout in vite.config.ts
test: {
  testTimeout: 10000,
}
```

**Module Import Errors:**
```typescript
// Add path aliases in vite.config.ts
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src'),
  },
}
```

**Component Rendering Issues:**
```typescript
// Ensure jsdom environment is configured
test: {
  environment: 'jsdom',
  setupFiles: './src/tests/setup.ts',
}
```

## 8.12 Test Environment Configuration

### Environment Variables

**Backend Test Environment (.env.test):**
```bash
# Database
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost/test_db

# JWT
JWT_SECRET=test_secret_key_minimum_32_characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# External Services (use mocks)
OPENAI_API_KEY=test_key
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=test_key
AWS_ACCESS_KEY_ID=test_access_key
AWS_SECRET_ACCESS_KEY=test_secret_key
```

**Frontend Test Environment (.env.test):**
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_ENV=test
```

### Test Database Management

**Reset Test Database:**
```python
# tests/reset_test_db.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from database.models import Base

async def reset_test_database():
    engine = create_async_engine(TEST_DATABASE_URL)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Test database reset complete")

if __name__ == "__main__":
    asyncio.run(reset_test_database())
```

**Execute Reset:**
```bash
python tests/reset_test_db.py
```

## 8.13 Performance and Load Testing

### Performance Test Configuration

**Response Time Validation:**
```python
@pytest.mark.performance
async def test_api_response_time(client: AsyncClient):
    start_time = time.time()
    response = await client.get("/api/farms")
    end_time = time.time()
    
    response_time = (end_time - start_time) * 1000  # Convert to ms
    assert response_time < 200  # Must respond within 200ms
```

**Load Testing with Locust:**
```python
from locust import HttpUser, task, between

class RiceAppUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_farms(self):
        self.client.get("/api/farms", headers=self.auth_headers)
    
    @task
    def create_task(self):
        self.client.post("/api/tasks", json=self.task_data)
```

**Execute Load Test:**
```bash
locust -f tests/load_test.py --host=http://localhost:8000
```

## 8.14 Security Testing

### Security Validation

**SQL Injection Prevention:**
```python
@pytest.mark.security
async def test_sql_injection_protection():
    malicious_input = "admin' OR '1'='1"
    response = await client.post("/api/auth/login", json={
        "username": malicious_input,
        "password": "password"
    })
    assert response.status_code == 401
```

**XSS Prevention:**
```python
@pytest.mark.security
async def test_xss_protection():
    malicious_script = "<script>alert('XSS')</script>"
    response = await client.post("/api/farms", json={
        "farm_name": malicious_script
    })
    # Verify script is sanitized in response
```

**Authentication Bypass Prevention:**
```python
@pytest.mark.security
async def test_protected_endpoint_requires_auth():
    response = await client.get("/api/farms")
    assert response.status_code == 401
```

## 8.15 Test Reporting and Documentation

### Coverage Report Access

**Backend HTML Report:**
```bash
cd RA_Backend
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

**Frontend HTML Report:**
```bash
cd RA_Frontend
npm run test:coverage
open coverage/index.html
```

### Test Result Documentation

**Generate Test Report:**
```bash
pytest --html=report.html --self-contained-html
```

**View Test Results:**
- HTML coverage reports show line-by-line coverage
- Terminal output shows pass/fail summary
- CI/CD dashboards display historical trends
- Coverage badges in README for quick status

### Additional Resources

**Documentation Links:**
- [Pytest Documentation](https://docs.pytest.org/)
- [Vitest Documentation](https://vitest.dev/)
- [React Testing Library](https://testing-library.com/react)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)

**Support Channels:**
- Development team Slack channel
- GitHub repository issues
- Internal documentation wiki
- Code review process

---

**Document Version:** 1.0.0  
**Last Updated:** December 2024  
**Maintained By:** AIRRVie Development Team
