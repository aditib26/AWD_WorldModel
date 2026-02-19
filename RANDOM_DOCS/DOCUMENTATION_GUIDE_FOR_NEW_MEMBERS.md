# AIRRVie Documentation Guide for New Team Members

## 🎯 Overview

This comprehensive guide helps new team members navigate the extensive documentation for the **AIRRVie Rice Farming Assistant** platform. 

**What is AIRRVie?**
AIRRVie is a digital decision-support platform designed to assist rice farmers in Vietnam, particularly in the Mekong Delta region. The system integrates:

- **AI-driven advisory services** with Retrieval-Augmented Generation (RAG)
- **Plant disease detection** using machine learning
- **Weather intelligence** and forecasting
- **Farm management tools** for plots, tasks, and journaling
- **Voice interface** for accessibility in field conditions
- **Bilingual support** (Vietnamese and English)

## 📚 Recommended Reading Order

### Phase 1: Understanding the System (Start Here - Day 1)

#### 1. **Business Logic & Requirements Documentation** 
**File:** `7. Business Logic & Requirements Documentation.txt`  
**Purpose:** Understand WHAT the system does and WHY it exists  
**Estimated Reading Time:** 30-45 minutes  

**Key Topics Covered:**
- **Functional Requirements:**
  - User Management (registration, authentication, profiles)
  - Farm and Plot Management (hierarchical agricultural entities)
  - AI Assistant with RAG (conversational AI with knowledge retrieval)
  - Disease Detection (image-based plant disease classification)
  - Task Management (farming workflow planning and tracking)
  - Farming Journal (activity logging with multimedia support)
  - Weather Integration (real-time and forecast data)
  - Voice Interface (speech-to-text and text-to-speech)
  - File Management (secure media upload and storage)

- **Non-Functional Requirements:**
  - Performance standards (sub-second API responses)
  - Reliability and availability (graceful degradation)
  - Security (authentication, data isolation, encryption)
  - Usability and Accessibility (mobile-first, bilingual, large fonts)
  - Maintainability (modular design, clear documentation)

- **User Workflows:**
  - Initial onboarding process
  - Daily farming operations
  - AI consultation patterns
  - Seasonal planning cycles

- **Edge Cases and Limitations:**
  - Network connectivity issues
  - Low-quality image handling
  - Mixed-language inputs
  - System constraints and boundaries

**Why Read First:** This document provides the business context and user needs that drive all technical decisions. Understanding this helps you appreciate the architectural choices made in later documents.

---

#### 2. **Software Architecture Documentation**
**File:** `2. Software Architecture Documentation.txt`  
**Purpose:** Understand HOW the system is built and WHY it's designed this way  
**Estimated Reading Time:** 60-90 minutes  

**Key Topics Covered:**
- **Architectural Overview:**
  - Distributed service architecture (VPS + TPU/GPU VM separation)
  - Single public entry point design
  - Internal service communication patterns

- **System Components:**
  - **Frontend Layer:** React + TypeScript PWA (Vite, mobile-first)
  - **Backend Layer:** FastAPI orchestration (Python 3.11)
  - **Data Layer:** PostgreSQL + Qdrant vector database
  - **AI Services:** Whisper ASR, Piper TTS, Qwen LLM
  - **Infrastructure:** Nginx reverse proxy, Docker containers

- **Technology Stack Details:**
  - Backend: FastAPI, Uvicorn, async PostgreSQL, JWT authentication
  - Frontend: React, TypeScript, Vite, PWA capabilities
  - Database: PostgreSQL 16 with core/sys schema separation
  - Vector DB: Qdrant for semantic search and RAG
  - AI Models: Whisper (ASR), Piper (TTS), Qwen (LLM)

- **Design Patterns:**
  - Monolithic backend with modular structure
  - Adapter pattern for external services
  - Dependency injection using FastAPI Depends
  - Stateless API design with external persistence

- **Module Organization:**
  - API Routers (auth, farms, tasks, journal, assistant, weather)
  - Service Layer (business logic orchestration)
  - Utility Modules (auth helpers, email service, AI clients)

- **AI Pipeline Architecture:**
  - RAG implementation with Qdrant integration
  - Context building from user data and knowledge base
  - Multi-language support (Vietnamese/English)
  - Voice interaction orchestration

**Why Read Second:** This provides the technical foundation and explains the system's design philosophy, helping you understand where different components fit and why certain architectural decisions were made.

---

### Phase 2: Technical Implementation Details (Day 2)

#### 3. **API Documentation**
**File:** `5. API Documentation.txt`  
**Purpose:** Understand the contract between frontend and backend  
**Estimated Reading Time:** 45-60 minutes  

**Key Topics Covered:**
- **API Architecture:**
  - RESTful design principles
  - JSON over HTTP/HTTPS communication
  - Base URLs (production vs development)
  - HTTP methods supported (GET, POST, PUT, DELETE, PATCH)

- **Authentication Model:**
  - JWT-based stateless authentication
  - Token issuance and expiration (24 hours)
  - Authorization header format
  - OTP-based verification for sensitive actions

- **Complete Endpoint Reference:**
  - **Authentication API** (`/api/auth`): Registration, login, OTP handling
  - **User Management** (`/api/users`): Profile management, statistics
  - **Farm & Plot Management** (`/api/farms`, `/api/plots`): Agricultural entities
  - **Task Management** (`/api/tasks`): Task lifecycle and tracking
  - **Journal & Activity Logging** (`/api/journal`): Farm activity records
  - **AI Assistant** (`/api/assistant`): Conversational AI interface
  - **Weather API** (`/api/weather`): Meteorological data
  - **File Upload** (`/api/uploads`): Media handling
  - **Voice Assistant** (`/api/voice`): Speech interaction

- **Request/Response Conventions:**
  - Standard headers (Content-Type, Authorization, Accept-Language)
  - Success response format
  - Error response structure with status codes
  - CORS configuration details

- **Security Features:**
  - Explicit origin whitelisting
  - Credentials allowed for trusted origins
  - HTTPS enforcement in production

**Why Read Third:** If you're working on either frontend or backend, this document explains how they communicate and what data flows between them. It's essential for understanding the system's external interfaces.

---

#### 4. **Database Documentation**
**File:** `3. Database Documentation.txt`  
**Purpose:** Understand data persistence and relationships  
**Estimated Reading Time:** 75-90 minutes  

**Key Topics Covered:**
- **Database Design Overview:**
  - PostgreSQL 16 as primary relational database
  - Schema separation (core vs sys)
  - Entity-Relationship model
  - Soft deletion patterns

- **Core Schema Tables:**
  - **users**: Authentication, preferences, locale settings
  - **farms**: Agricultural units with location metadata
  - **plots**: Physical cultivation areas with agronomic attributes
  - **tasks**: Farming activities with priority and status tracking
  - **journal_entry**: Activity logs with multimedia support
  - **media_asset**: File metadata and storage references
  - **weather_daily**: Cached weather data by plot and date
  - **conversation**: AI assistant session management
  - **message**: Individual conversation messages
  - **knowledge_chunk**: RAG knowledge units with embeddings

- **System Schema Tables:**
  - **job_queue**: Background processing and async jobs

- **Advanced Features:**
  - **Stored Functions:** Automated timestamp updates, task synchronization
  - **Triggers:** Data integrity enforcement
  - **Constraints:** Business rule validation
  - **Indexes:** Performance optimization

- **Database Roles:**
  - **airrvie_app_user**: Application-level access
  - **airrvie_maintenance**: Operational procedures
  - **airrvie_admin**: Full administrative privileges

- **Connection Management:**
  - Connection strings and parameters
  - Connection pooling configuration
  - Environment variable injection

**Why Read Fourth:** This explains how data flows through the system and is essential for understanding business logic implementation, data relationships, and system state management.

---

### Phase 3: Development and Operations (Day 3)

#### 5. **Source Code and Version Control Access**
**File:** `1. Source Code and Version Control Access.txt`  
**Purpose:** Understand how to access and work with the codebase  
**Estimated Reading Time:** 30-45 minutes  

**Key Topics Covered:**
- **Repository Structure:**
  - **Backend Repository:** `https://github.com/PEPESHANTY/RA_Backend`
  - **Frontend Repository:** `https://github.com/PEPESHANTY/RA_Frontend`
  - Private repository access requirements
  - GitHub authentication setup

- **Backend Repository Organization:**
  - **API Layer:** Route handlers (`api/` directory)
  - **Database Layer:** Schema and initialization (`database/`)
  - **AI Components:** Model inference (`ml_models/`)
  - **Utilities:** Helper functions (`utils/`)
  - **Voice Assistant:** Audio processing (`voice_assistant/`)

- **Frontend Repository Organization:**
  - **Components:** React UI components (`src/components/`)
  - **Services:** API communication layer (`src/services/`)
  - **Build Configuration:** Vite setup and static assets

- **Development Practices:**
  - Branching strategy (main, app3 branches)
  - Commit history and evolution
  - Version control workflow
  - Code entry points and navigation

- **Internal Documentation:**
  - API endpoint descriptions within code
  - Database structure documentation
  - AI assistant pipeline documentation
  - Integration behavior explanations

**Why Read Fifth:** This tells you where the actual code lives and how to start working with it. It provides the practical foundation for beginning development work.

---

#### 6. **Environment & Deployment Documentation**
**File:** `4. Environment & Deployment Documentation.txt`  
**Purpose:** Understand how to set up and deploy the system  
**Estimated Reading Time:** 90-120 minutes  

**Key Topics Covered:**
- **Local Development Setup:**
  - Docker-first development approach
  - Frontend local build and testing
  - Backend local development limitations
  - Required tools and dependencies

- **Environment Configuration:**
  - Environment variable templates
  - Database connection parameters
  - External API keys and secrets
  - Storage configuration (S3-compatible)

- **Manual Deployment Process:**
  - Server prerequisites and setup
  - GitHub authentication for private repos
  - Docker image building and execution
  - Port mapping and networking
  - Firewall configuration

- **Coolify Deployment:**
  - CI/CD pipeline automation
  - Git-based deployment triggers
  - Environment-specific configurations
  - Health checks and monitoring
  - Rollback capabilities

- **Service-Specific Setup:**
  - Piper TTS configuration (English/Vietnamese)
  - Whisper ASR deployment
  - PostgreSQL containerization
  - Nginx reverse proxy configuration

- **Troubleshooting Section:**
  - Common authentication issues
  - Docker networking problems
  - CORS configuration errors
  - Environment variable debugging

**Why Read Sixth:** This is practical knowledge for getting the system running locally and deploying it. It contains the step-by-step procedures you'll need for development setup.

---

### Phase 4: Specialized Topics (Read as Needed)

#### 7. **Configuration & Integration Docs**
**File:** `6. Configuration & Integration Docs.txt`  
**Purpose:** Understand external service integrations  
**When to Read:** When working with external APIs or services  
**Estimated Reading Time:** 30-45 minutes  

**Key Topics:**
- OpenWeatherMap API integration
- Gmail SMTP for OTP delivery
- Third-party credentials management
- Coolify deployment integration
- Logging and operational visibility

---

#### 8. **Testing Documentation**
**File:** `8. Testing Documentation.txt`  
**Purpose:** Understand how to test the system  
**When to Read:** When writing tests or debugging issues  
**Estimated Reading Time:** 30-45 minutes  

**Key Topics:**
- Test types and frameworks used
- Backend test setup and execution
- Frontend testing procedures
- Test data and demo accounts
- Staging vs production testing
- Common test failure troubleshooting

---

#### 9. **Operational & Maintenance Documents**
**File:** `9. Operational & Maintenance Documents.txt`  
**Purpose:** Understand system operations and known issues  
**When to Read:** When maintaining or troubleshooting the system  
**Estimated Reading Time:** 20-30 minutes  

**Key Topics:**
- Known bugs and technical limitations
- Qwen AI client initialization issues
- Model loading inconsistencies
- Debug logging in production
- Release notes and version history
- Monitoring and alert setup
- Logging locations and formats

---

#### 10. **Environment Variables Documentation**
**File:** `10. Env Variables CEADAR.txt`  
**Purpose:** Detailed environment variable reference  
**When to Read:** When configuring deployments or debugging environment issues  
**Estimated Reading Time:** 15-20 minutes  

**Key Topics:**
- Complete environment variable list
- Configuration examples
- Security considerations
- Deployment-specific values

---

### Phase 5: Advanced Architecture (Optional)

#### 11. **Three Levels of Architecture**
**File:** `three levels of Architecture.txt`  
**Purpose:** Deep architectural understanding  
**When to Read:** When making significant architectural decisions  
**Estimated Reading Time:** 20-30 minutes  

---

#### 12. **High-Level Architecture Documentation**
**File:** `DOCS High level and Low Level Separated/2. (High Level) Software Architecture Documentation.txt`  
**Purpose:** High-level architectural overview  
**When to Read:** For system-wide architectural perspective  
**Estimated Reading Time:** 30-45 minutes  

---

## 📋 Document Purpose Summary

| Document | Primary Purpose | Target Audience | Reading Priority | Est. Time |
|----------|----------------|------------------|------------------|-----------|
| **Business Logic & Requirements** | Understand system purpose and user needs | All team members | **1st (Critical)** | 30-45 min |
| **Software Architecture** | Understand technical design and structure | Developers, Architects | **2nd (Critical)** | 60-90 min |
| **API Documentation** | Understand frontend-backend communication | Frontend/Backend Devs | **3rd (High)** | 45-60 min |
| **Database Documentation** | Understand data model and persistence | Backend Devs, DBAs | **4th (High)** | 75-90 min |
| **Source Code Access** | Understand codebase structure and access | All developers | **5th (High)** | 30-45 min |
| **Environment & Deployment** | Understand setup and deployment | DevOps, All Devs | **6th (High)** | 90-120 min |
| **Configuration & Integration** | Understand external services | Integration specialists | As needed | 30-45 min |
| **Testing Documentation** | Understand testing approach | QA, All Devs | As needed | 30-45 min |
| **Operational & Maintenance** | Understand system operations | Ops, Support team | As needed | 20-30 min |
| **Environment Variables** | Configuration reference | DevOps, All Devs | As needed | 15-20 min |
| **Architecture Deep Dive** | Advanced architectural understanding | Architects, Senior Devs | Optional | 20-30 min |

---

## 🚀 Quick Start Checklist

### Day 1: System Orientation (2-3 hours)
- [ ] **Read Business Logic & Requirements Documentation** (Document 7)
  - Understand core functional requirements
  - Review user workflows and edge cases
  - Note system limitations and constraints
- [ ] **Read Software Architecture Documentation** (Document 2)
  - Understand distributed architecture
  - Review technology stack choices
  - Note module organization and AI pipeline
- [ ] **Review Source Code and Version Control Access** (Document 1)
  - Get repository access credentials
  - Clone both repositories
  - Explore code structure and entry points

### Day 2: Technical Foundation (3-4 hours)
- [ ] **Read API Documentation** (Document 5)
  - Understand authentication flow
  - Review all endpoint groups
  - Note request/response formats
- [ ] **Read Database Documentation** (Document 3)
  - Understand schema design
  - Review entity relationships
  - Note stored functions and triggers
- [ ] **Begin Environment Setup** (Document 4)
  - Install required tools (Docker, Git, etc.)
  - Review environment variable template
  - Start local development configuration

### Day 3: Practical Implementation (2-3 hours)
- [ ] **Complete Environment Setup** (Document 4)
  - Finish Docker container setup
  - Test local development environment
  - Verify frontend-backend connectivity
- [ ] **Review Testing Documentation** (Document 8)
  - Understand test structure
  - Run existing tests
  - Set up test data if needed
- [ ] **Begin Code Exploration**
  - Navigate to your area of focus
  - Review relevant code sections
  - Set up development tools and IDE

---

## 👥 Role-Specific Reading Paths

### 🎨 Frontend Developers
**Priority Reading Order:**
1. **Business Logic & Requirements** → Understand user needs and workflows
2. **Software Architecture** → Understand system overview and frontend role
3. **API Documentation** → Understand backend communication contracts
4. **Source Code Access** → Get frontend repository and explore structure
5. **Environment & Deployment** → Set up local development environment
6. **Testing Documentation** → Understand frontend testing approach

**Focus Areas:**
- React component structure and state management
- API integration patterns
- Mobile-first responsive design
- Bilingual support implementation
- Progressive Web App features

### ⚙️ Backend Developers
**Priority Reading Order:**
1. **Business Logic & Requirements** → Understand business rules and constraints
2. **Software Architecture** → Understand backend design and patterns
3. **API Documentation** → Understand endpoint contracts and responsibilities
4. **Database Documentation** → Understand data models and relationships
5. **Source Code Access** → Get backend repository and explore modules
6. **Environment & Deployment** → Set up local development environment
7. **Testing Documentation** → Understand backend testing approach

**Focus Areas:**
- FastAPI application structure
- Database ORM and query patterns
- AI service integration
- Authentication and authorization
- Business logic implementation

### 🚀 DevOps Engineers
**Priority Reading Order:**
1. **Software Architecture** → Understand system components and infrastructure
2. **Environment & Deployment** → Primary focus document for setup and deployment
3. **Configuration & Integration** → Understand external service integrations
4. **Operational & Maintenance** → Understand system operations and monitoring
5. **Source Code Access** → Understand deployment pipeline and CI/CD
6. **Environment Variables** → Configuration reference for deployments

**Focus Areas:**
- Docker containerization
- CI/CD pipeline setup
- Infrastructure management
- Monitoring and logging
- Security configuration

### 🧪 QA Engineers
**Priority Reading Order:**
1. **Business Logic & Requirements** → Understand expected behavior and user workflows
2. **API Documentation** → Understand testing interfaces and data contracts
3. **Testing Documentation** → Primary focus document for testing approach
4. **Environment & Deployment** → Set up test environments
5. **Database Documentation** → Understand data validation and integrity
6. **Operational & Maintenance** → Understand known issues and limitations

**Focus Areas:**
- Test strategy and frameworks
- API testing methodologies
- User acceptance testing
- Performance testing
- Regression testing

---

## 💡 Tips for Effective Documentation Reading

### 1. **Don't Read Everything at Once**
- Follow the recommended reading order for your role
- Focus on documents relevant to your immediate tasks
- Use the quick start checklist for structured progression
- Return to specialized documents when needed

### 2. **Take Active Notes**
- Document questions that arise while reading
- Note configuration values, URLs, and commands you'll need
- Keep track of which sections are most relevant to your role
- Create a personal reference sheet for quick lookups

### 3. **Cross-Reference Documents**
- Many documents reference each other (Document 2 → Document 5, etc.)
- When a document mentions another, pause and read that relevant section
- The architecture explains why the API is designed a certain way
- Database schema relates to API endpoint structures

### 4. **Apply Knowledge Practically**
- Try setting up the development environment as you read Document 4
- Test API endpoints mentioned in Document 5
- Look at the actual code structure while reading Document 1
- Run database initialization scripts from Document 3

### 5. **Use Multiple Learning Methods**
- Read the documentation first for understanding
- Then explore the actual code implementation
- Set up the development environment for hands-on experience
- Ask team members for clarification on unclear points

---

## ❓ Common Questions Answered

### Q: Where do I find the actual code?
**A:** Document 1 provides repository URLs and access instructions:
- Backend: `https://github.com/PEPESHANTY/RA_Backend`
- Frontend: `https://github.com/PEPESHANTY/RA_Frontend`
- Both repositories are private - access requires GitHub authentication

### Q: How do I set up my local development environment?
**A:** Document 4 contains comprehensive setup instructions:
- Docker-based development approach
- Environment variable configuration
- Frontend and backend container setup
- Troubleshooting common issues

### Q: What's the relationship between frontend and backend?
**A:** 
- Document 2 explains the overall architecture and separation of concerns
- Document 5 details the API contract between frontend and backend
- Frontend is a React PWA, backend is FastAPI with AI orchestration

### Q: How does the AI assistant work?
**A:** Document 2 contains a detailed section on the AI Assistant Pipeline:
- RAG implementation with Qdrant vector database
- Context building from user data and agricultural knowledge
- Multi-language support (Vietnamese/English)
- Voice interaction orchestration with Whisper and Piper

### Q: What database should I use for development?
**A:** Document 3 explains the PostgreSQL setup:
- PostgreSQL 16 with core/sys schema separation
- Database initialization scripts provided
- Connection string format and configuration
- Docker containerization support

### Q: How do I deploy the system?
**A:** Document 4 covers multiple deployment approaches:
- Manual deployment with Docker containers
- Coolify-based deployment with CI/CD pipeline
- Environment-specific configurations
- Server setup and networking requirements

### Q: What are the known issues or limitations?
**A:** Document 9 (Operational & Maintenance) covers:
- Known bugs and technical limitations
- Qwen AI client initialization issues
- Model loading inconsistencies
- Debug logging considerations

---

## 🆘 Getting Help

If you encounter issues while working through the documentation:

### 1. **Self-Service First**
- Check the relevant document section for your issue
- Look at troubleshooting sections in Documents 4 and 8
- Review the Operational & Maintenance Documents for known issues
- Search the documentation for keywords related to your problem

### 2. **Team Collaboration**
- Ask team members for clarification on unclear points
- Share specific questions with document references
- Discuss architectural decisions with senior developers
- Coordinate with DevOps for deployment issues

### 3. **Documentation Improvement**
- Note areas that are unclear or missing information
- Suggest improvements to make documentation better
- Contribute examples or troubleshooting steps
- Help keep documentation current with system changes

### 4. **Technical Support Channels**
- Use team communication channels for quick questions
- Schedule dedicated time for complex architectural discussions
- Create documentation tickets for missing or unclear information
- Participate in documentation review sessions

---

## 🎉 Conclusion

This documentation set is comprehensive but designed to be approachable for new team members. Following the recommended reading order will give you a solid understanding of the AIRRVie system from:

1. **Business Requirements** → Why the system exists
2. **Technical Architecture** → How it's built and why
3. **Implementation Details** → How to work with it
4. **Operational Procedures** → How to deploy and maintain it

### Key Takeaways:

- **Start with business context** before diving into technical details
- **Follow the role-specific reading paths** for focused learning
- **Apply knowledge practically** through hands-on development setup
- **Ask questions early** to avoid confusion later
- **Contribute to documentation** to help future team members

### Remember:
The documentation is a living resource that evolves with the system. As you work with AIRRVie, you'll discover areas that could be clearer or more detailed. Your feedback and contributions help make the documentation better for everyone who joins after you.

### Welcome to the AIRRVie Team! 🌾

We're excited to have you join us in building a platform that helps rice farmers in Vietnam make better decisions through AI-driven insights and digital tools. Your contributions will help improve agricultural practices and support sustainable farming in the Mekong Delta region.

---

**Last Updated:** January 2026  
**Maintained by:** AIRRVie Development Team  
**Version:** 1.0
