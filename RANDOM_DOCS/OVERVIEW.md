# AIRRVie - Rice Assistant App Overview

## Introduction

**AIRRVie** (AI Rice Assistant for Vietnamese farmers) is an intelligent farming assistant web application designed to help Vietnamese rice farmers optimize their cultivation practices through AI-powered insights, farm management tools, and real-time disease detection. The application combines modern web technologies with advanced machine learning to deliver personalized agricultural advice in both Vietnamese and English.

## Purpose & Target Users

The application serves Vietnamese rice farmers by providing:
- **Real-time agricultural guidance** through an AI chatbot powered by large language models
- **Disease detection** using computer vision to identify rice plant diseases from photos
- **Farm management tools** for tracking plots, tasks, and daily activities
- **Weather intelligence** with location-specific forecasts and farming recommendations
- **Voice interface** for hands-free interaction in the field
- **Digital journaling** to document farming activities with photos and audio notes

## Core Features

### 1. **AI Assistant with RAG**
- Powered by Qwen3-32B large language model (32 billion parameters)
- Retrieval-Augmented Generation (RAG) using Qdrant vector database for searching agricultural handbooks
- Context-aware responses incorporating user's farm data, weather conditions, and crop growth stages
- Bilingual support (Vietnamese and English) with automatic translation
- Conversation memory maintaining chat history for contextual follow-ups

### 2. **Disease Detection**
- MobileNetV3-Large deep learning model trained on 3,200 rice plant images
- Identifies 8 disease/pest conditions: Brown Spot Disease, Rice Blast, Brown Plant Hopper, Golden Apple Snails, Rice Borer, Rice Gall Midge, Rice Leaf Roller, and Healthy plants
- Provides confidence scores and treatment recommendations
- Processes images in 1-3 seconds with detailed AI-generated advice

### 3. **Farm & Plot Management**
- Multi-farm support for farmers managing multiple locations
- Detailed plot tracking (area, rice variety, planting/harvest dates, soil type, irrigation method)
- Photo uploads stored on AWS S3
- Vietnamese province/district selection for weather localization

### 4. **Task Management**
- Task types: Planting, Weeding, Fertilizer, Irrigation, Pest Control, Harvest
- Priority levels (Low, Medium, High) and status tracking (Pending, In Progress, Done)
- Due date management with overdue tracking
- Task reminders and completion statistics

### 5. **Digital Journal**
- Daily farming logs linked to specific plots
- Photo and audio note attachments
- Activity categorization and searchable history
- Statistics and insights on farming activities

### 6. **Weather Intelligence**
- OpenWeather API integration for current conditions and 5-day forecasts
- Location-based weather using IP geolocation or plot coordinates
- AI-generated farming recommendations based on weather patterns
- Weather alerts for rain, wind, and heat stress

### 7. **Voice Interface**
- Speech-to-text using Whisper model
- Text-to-speech using Piper TTS
- Complete voice chat workflow: audio upload → transcription → AI response → synthesized audio
- Supports Vietnamese and English languages

## Technical Architecture

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development and optimized production builds
- **Styling**: TailwindCSS utility-first framework
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Routing**: React Router v6 with protected routes
- **State Management**: React Context API for global state (user, farms, plots, language)
- **API Integration**: Centralized service layer with automatic JWT authentication

### Backend
- **Framework**: FastAPI (Python async web framework)
- **Database**: PostgreSQL with asyncpg for async operations
- **Authentication**: JWT tokens (7-day expiration) with bcrypt password hashing
- **Media Storage**: AWS S3 for images and audio files
- **Machine Learning**: PyTorch for MobileNetV3 disease detection
- **External APIs**: OpenWeather, Whisper, Piper TTS, Qwen LLM, Qdrant vector DB

### Database Schema
PostgreSQL database with 7 core tables:
- **Users**: Account information with language preferences
- **Farms**: Physical farm locations with province/district
- **Plots**: Individual cultivation areas within farms
- **Tasks**: Farming activities with priorities and status
- **Journal Entries**: Daily logs with media attachments
- **Conversations**: AI assistant chat sessions
- **Messages**: Individual messages in conversations

Design uses UUID primary keys, soft deletes (deleted_at timestamps), and JSONB fields for flexible metadata storage.

### Communication Flow
1. User action in React frontend
2. API call with JWT token in Authorization header
3. FastAPI validates token and extracts user_id
4. Async database query using asyncpg
5. External API calls if needed (weather, AI, ML)
6. JSON response returned
7. React component updates UI

## Key Technology Highlights

### AI/ML Integration
- **RAG Pipeline**: Query embedding → Qdrant vector search → Context retrieval → LLM generation with citations
- **Disease Detection**: MobileNetV3 with depthwise separable convolutions for efficiency
- **Bilingual AI**: Single inference produces both Vietnamese and English responses simultaneously
- **Context Awareness**: AI incorporates real-time farm data, weather, tasks, and growth stages

### Performance Optimizations
- **Async I/O**: Non-blocking database and HTTP operations for concurrent request handling
- **Lazy Loading**: ML model loads only when first needed and stays cached
- **Stateless API**: JWT authentication enables horizontal scaling
- **CDN Storage**: S3 for static media reduces server load

### Security Features
- **Password Security**: Bcrypt hashing with cost factor 12
- **Token Expiration**: 7-day JWT tokens require periodic re-authentication
- **CORS Protection**: Whitelist specific frontend origins
- **SQL Injection Prevention**: Parameterized queries throughout
- **Data Isolation**: User_id filtering ensures users only access their own data

## Deployment Architecture

The application supports multi-instance deployment (app, app2, app3) with:
- Separate frontend and backend deployments
- CORS configured for multiple frontend domains
- Environment variables for configuration (.env files)
- Docker support with Dockerfiles for both frontend and backend

## Development Workflow

### Backend Setup
```bash
cd RA_Backend
pip install -r requirements.txt
uvicorn main:app --reload
```
Server runs on port 8000 with auto-reload on code changes.

### Frontend Setup
```bash
cd RA_Frontend
npm install
npm run dev
```
Vite dev server with hot module replacement.

### API Documentation
FastAPI auto-generates interactive documentation:
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`

## Use Cases

1. **Disease Diagnosis**: Farmer notices spots on rice leaves → Takes photo → Uploads to app → Receives instant diagnosis and treatment plan
2. **Weather Planning**: Checks 5-day forecast → AI recommends irrigation adjustments based on expected rainfall
3. **Task Tracking**: Creates fertilizer application task → Sets reminder → Marks complete after application
4. **Voice Consultation**: In field with dirty hands → Uses voice chat to ask about pest control → Receives audio response
5. **Farm Documentation**: Takes daily journal photos → Records audio notes → Builds historical record for analysis

## Project Impact

AIRRVie transforms traditional rice farming by:
- **Reducing crop losses** through early disease detection
- **Optimizing resource use** with weather-based recommendations
- **Lowering barriers** with voice interface for farmers with limited literacy
- **Building knowledge** through documented farming history
- **Democratizing expertise** by making agricultural knowledge accessible to all farmers

## Future Enhancement Opportunities

- Push notifications for task reminders and weather alerts
- Offline mode for areas with poor connectivity
- Multi-crop support beyond rice
- Predictive analytics for yield forecasting
- Community features for farmer-to-farmer knowledge sharing
- Integration with IoT sensors for real-time field monitoring

---

**Documentation Structure:**
- `OVERVIEW.md` - This high-level summary
- `fullstack.md` - Detailed technical documentation of architecture
- `mobilenet.md` - In-depth explanation of disease detection system
- `TESTING.md` / `TESTING_DOCUMENTATION.md` - Testing procedures and results
- `RA_Backend/API_ENDPOINTS_DOCUMENTATION.md` - Complete API reference
- `RA_Backend/DATABASE_GUIDE.md` - Database schema and queries
