# AIRRVie - Full Stack Documentation

## Quick Overview

**AIRRVie** is a full-stack rice farming assistant for Vietnamese farmers with AI-powered advice, farm management, tasks, journal, weather, and voice interface.

**Tech Stack:**
- **Frontend:** React 18 + TypeScript + Vite + TailwindCSS + shadcn/ui
- **Backend:** FastAPI + Python + asyncpg + PostgreSQL
- **AI:** Qwen3-32B LLM + RAG (Qdrant) + MobileNetV2 (disease detection)
- **Services:** OpenWeather, Whisper (ASR), Piper (TTS), AWS S3

---

## Architecture

The application follows a three-tier architecture:

**Presentation Tier:** React frontend built with Vite and TypeScript

**Application Tier:** FastAPI backend handling business logic and API endpoints

**Data Tier:** PostgreSQL for structured data and AWS S3 for media storage

**External Services:** OpenWeather for weather data, Whisper for speech recognition, Piper for text-to-speech, Qwen LLM for AI responses, and Qdrant for vector search

**Communication:** The frontend and backend communicate via REST API using JSON. Authentication uses JWT tokens passed in HTTP headers.

### Request Flow
1. User action → 2. API call (JWT) → 3. Validate JWT → 4. DB query → 5. Response → 6. UI update

---

## Backend Structure

**Backend Organization:**

The backend is organized into several key directories:

**api folder** - Contains all API route handlers, each module handling a specific domain:
- auth.py handles user authentication (login, registration, OTP verification)
- farms.py manages farm and plot CRUD operations
- tasks.py handles task creation, updates, and tracking
- journal.py manages daily journal entries
- weather.py fetches weather data and generates AI insights
- assistant.py powers the AI conversation system
- voice.py handles voice chat functionality

**database folder** - Database connection configuration using asyncpg for async PostgreSQL operations

**ml_models folder** - Machine learning inference code for disease detection using MobileNetV2

**utils folder** - Shared utility functions:
- auth.py contains JWT token generation/verification and password hashing
- s3_utils.py handles AWS S3 file uploads and deletions

**main.py** - The application entry point that initializes FastAPI, configures middleware, and registers all routers

**How It Works:**

The backend is built on FastAPI, which creates a main application instance that serves as the entry point. When the application starts:

1. **Application Initialization**: FastAPI creates an app instance with configured metadata (title, version, API documentation URLs)

2. **Middleware Setup**: CORS (Cross-Origin Resource Sharing) middleware is added to allow the React frontend (running on different domains) to communicate with the backend. This middleware whitelists specific origins, enables credentials (cookies/auth headers), and allows all HTTP methods and headers.

3. **Router Registration**: Each API module (auth, farms, tasks, journal, weather, assistant, voice, uploads) is registered as a router. Routers are modular components that group related endpoints together. When a request comes in, FastAPI matches the URL path to the appropriate router and endpoint.

4. **Protected Endpoints**: For authenticated endpoints, FastAPI uses dependency injection. The get_current_user dependency extracts the JWT token from the Authorization header, verifies it, and returns the user_id. This user_id is then automatically passed to the endpoint function, ensuring only authenticated users can access the data.

5. **Database Operations**: The endpoint establishes an async connection to PostgreSQL using asyncpg, executes parameterized queries (preventing SQL injection), and returns the results as JSON.

6. **Async Processing**: All I/O operations (database queries, HTTP requests) use async/await, allowing the server to handle multiple concurrent requests without blocking.

---

## Frontend Structure

**Frontend Organization:**

**components folder** - Contains all React components:
- App.tsx is the main component that sets up routing for the entire application
- AppContext.tsx manages global application state (current user, farms, plots)
- Dashboard.tsx is the main landing page after login showing overview widgets
- Tasks.tsx displays and manages farming tasks
- Journal.tsx handles daily journal entries with photos and audio
- Weather.tsx shows weather data and AI recommendations
- SimpleAssistant.tsx provides the AI chat interface

**services folder** - Contains the API service layer:
- api.ts is the centralized module for all backend API calls, handling authentication headers, request formatting, and error handling

**How It Works:**

**API Service Layer:**

The frontend uses a centralized API service layer that acts as a bridge between React components and the backend:

1. **Base URL Configuration**: The service dynamically determines the backend URL based on the environment (app, app2, app3), allowing the same codebase to work across multiple deployments.

2. **Authentication Headers**: Before each API request, the service retrieves the JWT token from browser localStorage and includes it in the Authorization header as a Bearer token. This ensures authenticated requests.

3. **API Modules**: The service exports separate modules for each backend resource (authAPI, farmsAPI, tasksAPI, etc.). Each module contains methods for CRUD operations (GET, POST, PUT, DELETE).

4. **Request Handling**: When a component calls an API method, the service constructs the full URL, adds authentication headers, serializes the request body to JSON, sends the fetch request, handles errors, and returns parsed JSON.

**Routing:**

The frontend uses React Router for client-side navigation:

1. **BrowserRouter**: Wraps the entire application and manages browser history, enabling navigation without page reloads.

2. **AppProvider**: A React Context provider that manages global state (current user, farms, plots, language preference). All components within can access this shared state.

3. **Route Protection**: The ProtectedRoute component checks if a user is logged in (by verifying the user exists in AppContext). If not authenticated, it redirects to the login page. If authenticated, it renders the requested component.

4. **Lazy Loading**: Routes are configured to load components on-demand, reducing initial bundle size.

5. **State Management**: When navigation occurs, React Router updates the URL and re-renders the appropriate component while preserving the global state in AppContext.

---

## Database Schema

**PostgreSQL Schema: `core`**

The database uses 7 main tables:

**1. Users Table** - Stores user account information including UUID id, name, unique email, bcrypt password hash, preferred language (defaults to Vietnamese), creation timestamp, and soft delete timestamp.

**2. Farms Table** - Represents physical farm locations with UUID id, foreign key to user (owner), farm name, Vietnamese province and district for weather localization, optional address, and timestamps.

**3. Plots Table** - Individual cultivation areas within farms. Contains UUID id, foreign key to parent farm, plot name, area in square meters (decimal precision), soil type, rice variety, planting and harvest dates, irrigation method, notes, photos as JSONB array of S3 URLs, and soft delete timestamp.

**4. Tasks Table** - Tracks farming activities with UUID id, foreign keys to both plot and user, title, description, due date, priority level (low/medium/high), status (pending/in_progress/done), type (planting/weeding/fertilizer/irrigation/pest/harvest/other), reminder flag, completion flag, and soft delete timestamp.

**5. Journal Entries Table** - Daily farming logs with UUID id, foreign keys to plot and user, entry date, activity type, title, content text, photos JSONB array, audio note URL, and soft delete timestamp.

**6. Conversations Table** - AI assistant chat sessions with UUID id, user foreign key, optional farm and plot context links, conversation title, JSONB context metadata, start time, and soft delete timestamp.

**7. Messages Table** - Individual messages in conversations with UUID id, conversation foreign key, role (user or assistant), content text, JSONB metadata (containing language versions, citations, input type), and creation timestamp.

**Design Principles:** All tables use UUID primary keys for security. Soft deletes use a deleted_at timestamp (NULL when active). JSONB fields provide schema flexibility for arrays and metadata. Foreign keys enforce referential integrity.

---

## Authentication

### JWT Flow

**Registration Process:**

1. User submits name, email, phone, password, and language preference to the registration endpoint
2. Backend hashes the password using bcrypt with cost factor 12 (never stores plaintext)
3. User record is created in PostgreSQL with a UUID primary key
4. JWT token is generated with 7-day expiration containing the user's ID
5. Token and user data are returned to the client
6. Client stores token in localStorage for subsequent requests

**Login Process:**

1. User submits email and password to the login endpoint
2. Backend queries the database for the user by email
3. Password is verified against the stored bcrypt hash
4. If valid, a new JWT token is generated with 7-day expiration
5. Token and user data are returned to the client
6. Client stores token in localStorage and redirects to dashboard

**Protected Request Flow:**

1. Client includes JWT token in Authorization header (format: "Bearer <token>")
2. Server's get_current_user dependency function extracts the token
3. Token signature is verified using the secret key
4. Expiration timestamp is checked
5. User ID is extracted from the token's "sub" claim
6. User ID is automatically injected into the endpoint function via FastAPI dependency injection
7. Endpoint uses user_id to filter database queries, ensuring data isolation

**JWT Implementation Details:**

**Token Generation:** The server creates a JSON payload containing the user's ID as the "sub" (subject) claim and an expiration timestamp. This payload is encoded using the HS256 algorithm with a secret key, producing a three-part token (header.payload.signature).

**Token Verification:** For protected endpoints, FastAPI's dependency injection extracts and verifies the token. The signature is validated against the secret key, expiration is checked, and the user_id is extracted. This happens automatically before the endpoint function executes.

**Stateless Design:** No session data is stored server-side. All authentication state is in the token itself, enabling horizontal scaling without shared session storage.

### OTP System
- **Used for:** Email verification, password reset
- **Flow:** Request OTP → Send email → Store in memory → Verify → Delete

---

## API Endpoints

### Authentication (`/api/auth`)

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/register` | POST | No | Register user |
| `/login` | POST | No | Login |
| `/request-otp` | POST | No | Request email OTP |
| `/verify-otp` | POST | No | Verify OTP |
| `/me` | GET | Yes | Get current user |

### Farms & Plots (`/api`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/farms` | GET | Get all farms |
| `/farms` | POST | Create farm |
| `/farms/{id}` | PUT | Update farm |
| `/farms/{id}` | DELETE | Delete farm |
| `/plots` | GET | Get all plots |
| `/plots` | POST | Create plot |
| `/plots/{id}` | PUT | Update plot |
| `/plots/{id}` | DELETE | Delete plot |

### Tasks (`/api/tasks`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tasks` | GET | Get all tasks |
| `/tasks/upcoming` | GET | Tasks due in 7 days |
| `/tasks/stats` | GET | Statistics |
| `/tasks` | POST | Create task |
| `/tasks/{id}` | PUT | Update task |
| `/tasks/{id}/complete` | PUT | Mark complete |
| `/tasks/{id}` | DELETE | Delete task |

**Task Types:** planting, weeding, fertilizer, irrigation, pest, harvest, other

### Journal (`/api/journal`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/journal` | GET | Get all entries |
| `/journal/plot/{id}` | GET | Entries for plot |
| `/journal/stats` | GET | Statistics |
| `/journal` | POST | Create entry |
| `/journal/{id}` | PUT | Update entry |
| `/journal/{id}` | DELETE | Delete entry |

### Weather (`/api/weather`)

| Endpoint | Description |
|----------|-------------|
| `/weather` | Get weather (IP-based location) |
| `/weather?lat={lat}&lon={lon}` | Weather for coordinates |
| `/weather/plot/{id}` | Weather for plot location |

**Response includes:** Current weather, 5-day forecast, alerts, AI recommendations

### AI Assistant (`/api/assistant`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/conversations` | GET | Get all conversations |
| `/conversations/{id}` | GET | Get conversation + messages |
| `/conversations` | POST | Create conversation |
| `/conversations/{id}/messages` | POST | Send text message |
| `/conversations/{id}/voice` | POST | Send voice message |
| `/conversations/{id}/image` | POST | Upload image (disease detection) |
| `/conversations/{id}` | DELETE | Delete conversation |

**AI Features:**
- **Context-aware:** Uses farm, plot, weather, task data
- **RAG:** Searches agricultural handbooks via Qdrant
- **Bilingual:** Generates VI + EN responses simultaneously
- **Voice:** Whisper (speech-to-text) + Piper (text-to-speech)
- **Disease Detection:** MobileNetV2 on crop images

### Voice (`/api/voice`)

| Endpoint | Description |
|----------|-------------|
| `/talk` | Voice chat (audio → transcript → AI → TTS audio) |

### Uploads (`/api/uploads`)

| Endpoint | Description |
|----------|-------------|
| `/images/no-auth` | Upload image → returns S3 URL |
| `/audio/no-auth` | Upload audio → returns S3 URL |
| `/{media_id}` | Delete media from S3 |

---

## Key Features

### 1. Farm Management
- **Multi-farm support:** Users can manage multiple farms
- **Plot tracking:** Detailed info (area, variety, planting/harvest dates, soil type)
- **Photos:** JSONB array of S3 URLs

### 2. Task Management
- **Types:** Planting, weeding, fertilizer, irrigation, pest control, harvest
- **Priorities:** Low, medium, high
- **Status tracking:** Pending → In Progress → Done
- **Reminders:** Boolean flag for notifications
- **Statistics:** Total, pending, overdue, due today

### 3. Digital Journal
- **Daily entries:** Date, type, title, content
- **Media:** Photos (JSONB array) + audio notes (S3 URL)
- **Per-plot tracking:** Link entries to specific plots
- **Statistics:** Total entries, by type, by time period

### 4. Weather Intelligence
- **Data source:** OpenWeather API
- **Current weather:** Temperature, humidity, rainfall, wind, visibility
- **5-day forecast:** High/low temps, rainfall, conditions
- **AI insights:** Qwen3-32B generates farming recommendations
- **Alerts:** Rain, wind, heat stress warnings
- **Location-based:** IP geolocation or plot coordinates

### 5. AI Assistant
- **LLM:** Qwen3-32B (32B parameters, self-hosted on TPU)
- **RAG:** Vector search in agricultural handbooks via Qdrant
- **Context:** Incorporates user's farm, plot, weather, tasks, growth stage
- **Bilingual:** Generates both VI and EN responses for language toggle
- **Conversation memory:** Maintains chat history (last 10 messages)
- **Citations:** References handbook pages in responses

**AI Processing Pipeline:**

1. **User Input**: User sends a message via text, voice, or image upload
2. **Context Gathering**: System fetches relevant context including user's farms, plots, current weather, active tasks, and crop growth stage
3. **RAG Search**: Query is embedded and searched in Qdrant vector database containing agricultural handbooks, returning relevant passages
4. **Prompt Construction**: An enhanced prompt is built combining the user's question, retrieved handbook context, and user-specific data
5. **LLM Inference**: Qwen3-32B generates a response in both Vietnamese and English simultaneously
6. **Database Storage**: Both the user message and AI response are saved to the messages table
7. **Response Delivery**: The bilingual response with citations is returned to the user

### 6. Voice Interface
- **Speech-to-text:** Whisper (self-hosted)
- **Text-to-speech:** Piper TTS (self-hosted)
- **Voice chat:** Audio upload → Transcribe → AI response → Synthesize audio
- **Supported:** Vietnamese and English
- **Public/Private:** Configurable authentication via `VOICE_API_PUBLIC`

### 7. Disease Detection
- **Model:** MobileNetV2 (fine-tuned on rice diseases)
- **Input:** Plant image
- **Output:** Disease prediction + confidence + treatment advice
- **Integration:** Upload via `/conversations/{id}/image`
- **Context-aware:** AI combines disease detection with plot/weather data

---

## Technology Highlights

### Backend
- **FastAPI:** Modern async Python framework
- **asyncpg:** High-performance async PostgreSQL driver
- **Pydantic:** Type-safe request/response validation
- **bcrypt:** Secure password hashing (cost factor 12)
- **PyJWT:** Stateless JWT authentication
- **httpx:** Async HTTP client for external APIs

### Frontend
- **React 18:** Modern hooks-based architecture
- **Vite:** Fast dev server and optimized production builds
- **TypeScript:** Type safety across the application
- **React Router v6:** Client-side routing with protected routes
- **React Context API:** Global state (user, farms, plots)
- **TailwindCSS:** Utility-first styling
- **Radix UI:** Accessible component primitives
- **shadcn/ui:** Beautiful pre-built components

### DevOps
- **Deployment:** Multi-instance deployment (app, app2, app3)
- **CORS:** Configured for multiple frontend domains
- **Environment:** `.env` for secrets
- **Media Storage:** AWS S3 for images and audio
- **Caching:** Redis for OTP storage (production)

---

## Interview Talking Points

### Architecture Decisions
1. **Why FastAPI?** Async support for concurrent requests, automatic OpenAPI docs, Pydantic validation
2. **Why asyncpg?** 3x faster than psycopg2, native async/await support
3. **Why JWT?** Stateless authentication, easy to scale horizontally
4. **Why soft deletes?** Data recovery, audit trails, GDPR compliance
5. **Why JSONB?** Flexible schema for photos array, conversation metadata

### Scalability
- **Async I/O:** Non-blocking database and HTTP operations
- **Stateless API:** JWT enables horizontal scaling
- **Caching:** Redis for frequently accessed data
- **CDN:** S3 for static media files
- **Database indexing:** UUIDs, foreign keys, deleted_at filters

### Security
- **Password hashing:** bcrypt with high cost factor
- **JWT expiration:** 7-day tokens force re-authentication
- **CORS:** Whitelist specific origins
- **SQL injection prevention:** Parameterized queries ($1, $2)
- **Soft deletes:** Preserve audit trail

### AI/ML Integration
- **RAG:** Grounds AI responses in expert knowledge
- **Context-aware:** Uses real-time farm/weather data
- **Bilingual:** Single inference, dual language output
- **Disease detection:** Real-time image analysis
- **Voice interface:** End-to-end voice workflow

### Full Stack Skills Demonstrated
- **Frontend:** React, TypeScript, state management, routing, API integration
- **Backend:** Python, FastAPI, async programming, database design
- **Database:** PostgreSQL, schema design, migrations, JSONB
- **Auth:** JWT, bcrypt, OTP system
- **APIs:** RESTful design, external API integration
- **AI/ML:** LLM integration, RAG, computer vision
- **DevOps:** Multi-environment deployment, S3, environment configuration

---


## Quick Reference

### Environment Variables Configuration

The application uses environment variables for configuration, stored in a `.env` file:

**Database Configuration:**
- **DATABASE_URL**: PostgreSQL connection string containing host, port, database name, username, and password. Format typically: `postgresql://user:password@host:port/database`

**Authentication:**
- **SECRET_KEY**: Random string used for JWT token signing. Must be kept secret and should be at least 32 characters for security.

**External APIs:**
- **WEATHER_API**: OpenWeather API key for fetching weather data
- **QWEN_TPU_ENDPOINT**: URL of the self-hosted Qwen3-32B inference server
- **QDRANT_URL**: URL of the Qdrant vector database for RAG functionality
- **WHISPER_ENDPOINT**: URL of the self-hosted Whisper speech-to-text server
- **PIPER_TTS_API**: URL of the self-hosted Piper text-to-speech service

**AWS S3 Storage:**
- **AWS_ACCESS_KEY_ID**: AWS credential for S3 access
- **AWS_SECRET_ACCESS_KEY**: AWS secret key for authentication
- **S3_BUCKET_NAME**: Name of the S3 bucket for storing images and audio files

**Configuration Management:** These variables are loaded at application startup using the `python-dotenv` library. Never commit the `.env` file to version control.

### Running the Application

**Backend Setup:**
1. Navigate to the `RA_Backend` directory
2. Install Python dependencies from `requirements.txt` using pip
3. Start the FastAPI server using Uvicorn with the `--reload` flag for auto-restart on code changes
4. The server runs on port 8000 by default

**Frontend Setup:**
1. Navigate to the `RA_Frontend` directory
2. Install Node.js dependencies from `package.json` using npm
3. Start the Vite development server
4. The frontend runs on port 3000 (or 5173 for Vite default) with hot module replacement

**Development Workflow:** Both servers run simultaneously. The frontend makes API calls to the backend. CORS middleware ensures the frontend origin is allowed.

### API Documentation

FastAPI automatically generates interactive API documentation:

**Swagger UI:** Available at `/api/docs` endpoint. Provides:
- Complete list of all endpoints
- Request/response schemas
- Interactive testing interface (can send requests directly from browser)
- Authentication support (add JWT token to test protected endpoints)
- Automatic schema validation display

**ReDoc:** Alternative documentation at `/api/redoc` with a cleaner, read-focused interface

These docs are generated automatically from Pydantic models and route definitions, ensuring they're always in sync with the code.

---


