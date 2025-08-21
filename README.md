# 🤖 Rituo - AI Assistant for Google Workspace

Rituo is a sophisticated AI-powered assistant that seamlessly integrates with Google Workspace (Gmail, Calendar, Tasks) to help you manage your digital workspace efficiently.

## ✨ Features

- **🧠 AI-Powered**: Uses Groq LLM for intelligent conversation and task understanding
- **📧 Gmail Integration**: Search, send, and manage emails through natural language
- **📅 Calendar Management**: Schedule meetings, create events, and manage your calendar
- **✅ Task Management**: Create and organize tasks in Google Tasks
- **🔐 Secure Authentication**: OAuth 2.1 integration with Google
- **💬 Chat Interface**: Modern, responsive chat UI for seamless interaction
- **🔄 Real-time Updates**: Live chat with streaming responses

## 🏗️ Architecture

### Frontend (Next.js + TypeScript)
- **Framework**: Next.js 14 with TypeScript
- **UI**: Custom components with Tailwind CSS
- **State Management**: React hooks with context
- **Deployment**: Vercel

### Backend (FastAPI + Python)
- **API Framework**: FastAPI with async support
- **AI Integration**: Groq LLM with LangChain
- **Google APIs**: Gmail, Calendar, Tasks via MCP protocol
- **Database**: MongoDB with Motor (async driver)
- **Authentication**: OAuth 2.1 with JWT tokens
- **Deployment**: Docker on Digital Ocean

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12+
- MongoDB (Atlas or local)
- Google Cloud Console account
- Groq API key

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/rituo.git
   cd rituo
   ```

2. **Set up the backend**
   ```bash
   cd server
   cp env.production.example .env
   # Edit .env with your credentials
   
   # Install dependencies
   pip install uv
   uv sync
   
   # Run the server
   uv run app.py
   ```

3. **Set up the frontend**
   ```bash
   cd ../  # Back to project root
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## 🌐 Production Deployment

### Backend (Digital Ocean)

The backend is containerized and ready for Digital Ocean deployment:

```bash
# On your Digital Ocean droplet
git clone https://github.com/your-username/rituo.git /opt/rituo
cd /opt/rituo

# Configure environment
cp server/env.production.example .env.production
# Edit .env.production with your production values

# Deploy with one command
chmod +x deploy.sh
sudo ./deploy.sh
```

**📚 Detailed Guide**: [DEPLOYMENT_DIGITAL_OCEAN.md](./DEPLOYMENT_DIGITAL_OCEAN.md)

### Frontend (Vercel)

The frontend deploys seamlessly to Vercel:

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**📚 Detailed Guide**: [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```bash
# Google OAuth
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
GOOGLE_OAUTH_REDIRECT_URI=http://localhost:8001/oauth2callback

# Database
MONGODB_URL=mongodb://localhost:27017/rituo_app

# AI
GROQ_API_KEY=your-groq-api-key

# Server
PORT=8001
API_PORT=8000
```

#### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MCP_URL=http://localhost:8001
```

### Google Cloud Console Setup

1. Create a new project or use existing
2. Enable these APIs:
   - Gmail API
   - Google Calendar API
   - Google Tasks API
3. Create OAuth 2.0 credentials
4. Add authorized redirect URIs:
   - `http://localhost:8001/oauth2callback` (development)
   - `https://your-domain.com:8001/oauth2callback` (production)

## 🛠️ Development

### Project Structure
```
rituo/
├── src/                    # Frontend (Next.js)
│   ├── app/               # App router pages
│   ├── components/        # Reusable components
│   └── lib/              # Utilities
├── server/                # Backend (FastAPI)
│   ├── api/              # API routes
│   ├── auth/             # Authentication
│   ├── core/             # Core utilities
│   ├── database/         # Database models
│   ├── services/         # Business logic
│   ├── gcalendar/        # Google Calendar tools
│   ├── gmail/            # Gmail tools
│   └── gtasks/           # Google Tasks tools
└── docs/                 # Documentation
```

### Available Scripts

#### Frontend
```bash
npm run dev          # Development server
npm run build        # Production build
npm run start        # Production server
npm run lint         # Lint code
```

#### Backend
```bash
uv run app.py        # Start server
uv run --dev app.py  # Development mode
uv sync              # Install dependencies
uv run pytest       # Run tests
```

## 🔍 API Documentation

The backend provides comprehensive API documentation:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🧪 Testing

### Frontend Testing
```bash
npm run test         # Run tests
npm run test:watch   # Watch mode
npm run test:coverage # Coverage report
```

### Backend Testing
```bash
uv run pytest              # Run all tests
uv run pytest --cov       # With coverage
uv run pytest -v          # Verbose output
```

## 📊 Monitoring

### Health Checks
- **Backend**: `GET /health`
- **Frontend**: Built-in Next.js monitoring

### Logging
- **Backend**: Structured logging with Python logging
- **Frontend**: Console logging (development) / Analytics (production)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` folder for detailed guides
- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Use GitHub Discussions for questions and community support

## 🙏 Acknowledgments

- **Google Cloud Platform** for Workspace APIs
- **Groq** for fast AI inference
- **Next.js** and **FastAPI** for excellent frameworks
- **Vercel** and **Digital Ocean** for hosting platforms

---

Made with ❤️ for productivity enthusiasts