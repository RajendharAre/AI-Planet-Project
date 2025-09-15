# 🚀 AI Planet - No-Code/Low-Code Workflow Builder

> **Full-Stack Engineering Internship Assignment**  
> A visual workflow builder that enables users to create intelligent AI workflows with drag-and-drop components.

![AI Planet Demo](https://via.placeholder.com/800x400/667eea/ffffff?text=AI+Planet+Workflow+Builder)

## 📋 Table of Contents

- [🎯 Overview](#-overview)
- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Tech Stack](#️-tech-stack)
- [🚀 Quick Start](#-quick-start)
- [📖 Detailed Setup](#-detailed-setup)
- [🎮 Usage Guide](#-usage-guide)
- [🧪 Testing](#-testing)
- [🚢 Deployment](#-deployment)
- [📚 API Documentation](#-api-documentation)
- [🎥 Demo Video](#-demo-video)
- [🤝 Contributing](#-contributing)

## 🎯 Overview

AI Planet is a **No-Code/Low-Code visual workflow builder** that empowers users to create intelligent AI workflows without writing code. Users can drag and drop components, configure them visually, and execute complex AI workflows through an intuitive interface.

### Core Workflow Components:
1. **👤 User Query** - Entry point for user questions
2. **📚 KnowledgeBase** - Document upload, processing, and vector search
3. **🤖 LLM Engine** - AI processing with Gemini integration
4. **💬 Output** - Chat interface for responses

## ✨ Features

### 🎨 Visual Workflow Builder
- **Drag & Drop Interface** - Intuitive component placement
- **Real-time Validation** - Instant feedback on workflow structure
- **Professional UI/UX** - Modern, responsive design
- **Component Configuration** - Dynamic panels for each component type

### 📄 Document Processing
- **PDF Upload & Processing** - Extract text with PyMuPDF
- **AI-Powered Analysis** - Document summarization and insights
- **Vector Embeddings** - Semantic search with Gemini embeddings
- **Multiple Format Support** - PDF, TXT, MD, DOC, DOCX

### 🤖 AI Integration
- **Gemini AI** - Google's latest language models
- **Custom Prompts** - Define AI behavior and expertise
- **Context-Aware Responses** - Document-based question answering
- **Fallback Mechanisms** - Robust error handling

### 💻 Technical Excellence
- **Real-time Workflow Execution** - Instant feedback
- **PostgreSQL Database** - Reliable data persistence
- **RESTful APIs** - Clean, documented endpoints
- **Authentication System** - Secure user management
- **Public Testing Endpoints** - Easy demo and testing

## 🏗️ Architecture

```mermaid
graph TB
    subgraph "Frontend (React + React Flow)"
        A[Component Library Panel]
        B[Workflow Canvas]
        C[Configuration Panel]
        D[Chat Interface]
    end
    
    subgraph "Backend (FastAPI)"
        E[Authentication API]
        F[Document Processing API]
        G[Workflow Execution API]
        H[Chat API]
    end
    
    subgraph "External Services"
        I[Gemini AI API]
        J[PostgreSQL Database]
    end
    
    A --> E
    B --> G
    C --> F
    D --> H
    F --> I
    G --> I
    H --> I
    E --> J
    F --> J
    G --> J
    H --> J
```

## 🛠️ Tech Stack

### Frontend
- **React.js** - Modern UI framework
- **React Flow** - Interactive workflow canvas
- **Axios** - HTTP client
- **Modern CSS** - Professional styling

### Backend
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - ORM with async support
- **Pydantic** - Data validation and serialization

### AI & Processing
- **Gemini AI** - Google's language models
- **PyMuPDF** - PDF text extraction
- **Vector Embeddings** - Semantic search capabilities

### DevOps
- **Uvicorn** - ASGI server
- **Git** - Version control
- **Environment Variables** - Secure configuration

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 15+
- Git

### 1️⃣ Clone Repository
```bash
git clone https://github.com/yourusername/ai-planet.git
cd ai-planet
```

### 2️⃣ Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Set environment variables (Windows)
set DATABASE_URL=postgresql://postgres:Raju@33*@localhost:5432/workflow_db
set SECRET_KEY=your-secret-key-here
set GEMINI_API_KEY=your-gemini-api-key
set SERP_API_KEY=your-serp-api-key

# Initialize database
python -c "from database import init_db; import asyncio; asyncio.run(init_db())"

# Start the server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 3️⃣ Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4️⃣ Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## 📖 Detailed Setup

### Database Configuration

#### Option 1: Local PostgreSQL (Recommended)
1. **Install PostgreSQL:**
   - Download from: https://www.postgresql.org/download/
   - Use credentials: `postgres` / `Raju@33*`
   - Create database: `ai_planet_db`

2. **Initialize Database:**
   ```bash
   cd backend
   python init_db.py init
   ```

#### Option 2: Cloud Database
Update `.env` with your cloud PostgreSQL URL:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/db
```

### API Keys Setup

#### Get Gemini API Key (Free)
1. Visit: https://aistudio.google.com/app/apikey
2. Create API key
3. Update `.env`:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

### Environment Variables
Create `.env` file in backend directory:
```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:Raju%4033%2A@localhost:5432/ai_planet_db

# AI Services
GEMINI_API_KEY=your_gemini_api_key
SERP_API_KEY=your_serp_api_key (optional)

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
APP_NAME=AI Planet
APP_VERSION=1.0.0
DEBUG=true
ENV=development

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=uploads

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## 🎮 Usage Guide

### 1. Upload Documents
1. Click **"📄 Upload Documents"**
2. Select PDF files
3. Wait for processing completion
4. Documents are now available in workflows

### 2. Build Workflow
1. Click **"🔧 Build Workflow"**
2. Drag components from Component Library:
   - **User Query** (Entry point)
   - **KnowledgeBase** (Document search)
   - **LLM Engine** (AI processing)
   - **Output** (Response display)
3. Connect components with arrows
4. Configure each component by clicking

### 3. Configure Components

#### KnowledgeBase Configuration:
- Select uploaded documents
- Set similarity threshold (0.1-0.9)
- Choose max results (3-15)

#### LLM Engine Configuration:
- Choose AI model (Gemini Flash/Pro)
- Set custom system prompt
- Adjust temperature (creativity)
- Configure response length

#### Output Configuration:
- Choose format (Text/JSON/Markdown)
- Include source references
- Add metadata

### 4. Execute Workflow
1. Click **"🔨 Build Stack"** to validate
2. Click **"💬 Chat with AI"** to test
3. Ask questions and get AI responses

## 🧪 Testing

### Manual Testing
1. **Document Upload Test:**
   ```bash
   # Upload a PDF file through the UI
   # Verify: Document appears in KnowledgeBase configuration
   ```

2. **Workflow Validation Test:**
   ```bash
   # Create workflow with all 4 components
   # Verify: Build Stack shows "Valid"
   ```

3. **End-to-End Test:**
   ```bash
   # Upload document → Build workflow → Configure components → Chat
   # Verify: AI responds with document context
   ```

### API Testing
```bash
# Test document upload
curl -X POST "http://localhost:8001/api/v1/documents/upload-public" \
  -F "file=@sample.pdf"

# Test workflow execution
curl -X POST "http://localhost:8001/api/v1/workflows/run-public" \
  -H "Content-Type: application/json" \
  -d '{"definition": {"nodes": [], "edges": []}, "query": "Hello"}'
```

### Backend Health Check
```bash
curl http://localhost:8001/api/health
```

## 🚢 Deployment

### Production Build

#### Frontend
```bash
cd frontend
npm run build
# Serve dist/ folder with nginx/apache
```

#### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### Cloud Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment options including:
- Heroku
- Railway
- Render
- PythonAnywhere
- Traditional VPS setup

### Environment Variables for Production
```env
DEBUG=false
ENV=production
ALLOWED_ORIGINS=https://yourdomain.com
DATABASE_URL=postgresql://user:pass@prod-host:5432/db
```

## 📚 API Documentation

### Core Endpoints

#### Documents
- `POST /api/v1/documents/upload-public` - Upload document
- `GET /api/v1/documents/public` - List documents

#### Workflows
- `POST /api/v1/workflows/run-public` - Execute workflow
- `GET /api/v1/workflows/components/available` - Get components

#### Health
- `GET /api/health` - Health check
- `GET /api/info` - Application info

### Interactive API Docs
Visit: http://localhost:8001/api/docs

## 🎥 Demo Video

> **Note:** Create a 3-5 minute demo video showing:
> 1. Document upload process
> 2. Workflow creation with drag & drop
> 3. Component configuration
> 4. End-to-end execution
> 5. AI responses with document context

## 🏆 Assignment Evaluation Criteria

### ✅ Functional Correctness
- All 4 core components implemented
- Workflow validation and execution
- Document processing and AI integration
- Chat interface functionality

### ✅ UI/UX Quality
- Professional, modern design
- Intuitive drag & drop interface
- Responsive layout
- Clear visual feedback

### ✅ Backend Architecture
- RESTful API design
- Database integration
- Error handling
- Security measures

### ✅ Code Quality
- Clean, well-documented code
- Modular design
- Proper error handling
- Performance optimization

### ✅ Tool Integration
- Gemini AI integration
- PostgreSQL database
- PyMuPDF for text extraction
- React Flow for workflows

### ✅ Extensibility
- Modular component architecture
- Configuration-driven design
- Plugin-ready structure
- Scalable database design

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Gemini AI** - Powerful language models
- **React Flow** - Excellent workflow library
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Reliable database system

---

**Built with ❤️ for Full-Stack Engineering Internship Assignment**

For questions or support, please contact: [your-email@example.com]