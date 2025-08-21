# Rituo 

Rituo is an AI-powered assistant that integrates with Google Workspace (Gmail, Calendar, Tasks) to automate your digital workflow.

## Key Features

- **AI-Powered**: Groq LLM with LangChain for intelligent task understanding
- **Gmail Integration**: Send emails, search messages, manage drafts
- **Calendar Management**: Create events, check schedules, manage calendars
- **Task Management**: Create and organize Google Tasks
- **Secure OAuth**: Google OAuth 2.1 authentication
- **Modern Chat UI**: Real-time responsive interface

## Architecture

### Frontend
- **Framework**: Next.js 15 with TypeScript
- **Styling**: Tailwind CSS with Swiss design principles
- **Deployment**: Vercel

### Backend
- **Framework**: FastAPI with async support
- **AI**: Groq LLM via LangChain
- **Google APIs**: Integrated via FastMCP protocol
- **Database**: MongoDB with async Motor driver
- **Auth**: JWT tokens with OAuth 2.1
- **Deployment**: Docker (Digital Ocean ready)

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.12+
- MongoDB instance
- Google Cloud project with Gmail/Calendar/Tasks APIs enabled
- Groq API key

### Development Setup

1. **Backend**
   ```bash
   cd server
   cp .env.example .env
   # Configure environment variables
   
   pip install uv
   uv sync
   uv run app.py
   ```

2. **Frontend**
   ```bash
   npm install
   npm run dev
   ```

3. **Access**
   - Frontend: http://localhost:3000

### Backend Environment (.env)
```bash
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret
MONGODB_URL=mongodb://localhost:27017/rituo_app
API_PORT=8000
PORT=8001
```

### Frontend Environment (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_MCP_URL=http://localhost:8001
```

## Project Structure
```
rituo/
├── src/           # Next.js frontend
│   ├── app/       # Pages and routes
│   ├── components/ # UI components
│   └── lib/       # Utilities
├── server/        # FastAPI backend
│   ├── api/       # API routes
│   ├── auth/      # Authentication
│   ├── database/  # Models and connections
│   ├── services/  # Business logic
│   └── gmail/,
│       gcalendar/,
│       gtasks/    # Google Workspace tools
└── docs/          # Documentation
```

### Frontend
```bash
npm run dev        # Start dev server
npm run build      # Production build
npm run lint       # Code linting
```

### Backend
```bash
uv run app.py      # Start server
uv sync            # Install dependencies
```

## Documentation

- **API Docs**: http://localhost:8000/docs (when running)
- **Deployment Guides**: See DEPLOYMENT*.md files
- **Architecture Details**: Refer to code comments and docstrings

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Open Pull Request

## License

GPL-3.0 license - see [LICENSE](LICENSE) file.