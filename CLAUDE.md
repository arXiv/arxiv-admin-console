# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the arXiv admin console - a web application for managing arXiv users, submissions, endorsements, and moderation. It consists of two main components:

1. **API Backend** (`api_arxiv_admin/`) - Python FastAPI application for admin operations
2. **Frontend UI** (`ui-arxiv-admin/`) - React-based admin interface built with react-admin

## Development Commands

### Root Level Commands (Makefile)
- `make bootstrap` - Set up development environment for all components
- `make docker-image` - Build Docker images for API and UI
- `make up` - Run docker-compose stack (requires .env file)
- `make down` - Stop docker-compose stack
- `make test` - Run tests across all components
- `make help` - Show available commands

### API Backend (`api_arxiv_admin/`)
- `cd api_arxiv_admin && make bootstrap` - Set up Python virtual environment with Poetry
- `cd api_arxiv_admin && poetry install` - Install Python dependencies
- `cd api_arxiv_admin && poetry run uvicorn arxiv_admin_api.main:app --reload` - Run development server
- `cd api_arxiv_admin && poetry run pytest` - Run tests
- `cd api_arxiv_admin && poetry run mypy -p arxiv_admin_api` - Type checking

### Frontend UI (`ui-arxiv-admin/`)
- `cd ui-arxiv-admin && npm install` - Install Node.js dependencies
- `cd ui-arxiv-admin && npm run dev` - Start development server (Vite)
- `cd ui-arxiv-admin && npm run build` - Build production bundle
- `cd ui-arxiv-admin && npm run lint` - Run ESLint
- `cd ui-arxiv-admin && npm test` - Run Jest tests

### Testing Commands
- `cd tests && make up` - Start test database with Docker Compose
- `cd tests && make down` - Stop test database
- `cd tests && ./type-check.sh arxiv_admin_api` - Run mypy type checking
- `cd tests && ./lint.sh` - Run pylint (requires MIN_SCORE env var, defaults to 8)

## Architecture

### API Backend Structure
- **FastAPI Application**: Main app in `arxiv_admin_api/main.py` with middleware for CORS, logging, and authentication
- **Business Logic**: Core functionality in `biz/` directory (endorsements, paper ownership, submissions)
- **Data Access**: Models and database operations in `dao/` directory  
- **API Routes**: Domain-specific routers (users, documents, endorsements, etc.)
- **Authentication**: JWT-based auth with Keycloak integration via arxiv-base library
- **Database**: MySQL via SQLAlchemy with Classic arXiv database schema

### Frontend Structure
- **React Admin Framework**: Built on react-admin with Material-UI components
- **Pages**: Each admin function has its own page component (Users, Documents, Endorsements, etc.)
- **Components**: Reusable components in `bits/` (fields, dialogs, layouts)
- **Authentication**: OIDC authentication provider integration
- **Data Provider**: Custom data provider for API communication

### Key Integrations
- **arXiv Base Library**: Authentication, configuration, and shared utilities
- **Keycloak**: Identity and access management
- **Classic Database**: Legacy arXiv MySQL database for user and submission data
- **FastAPI + React Admin**: RESTful API with pagination, filtering, and CRUD operations

## Environment Setup

The application requires a `.env` file (symlinked from `../arxiv-keycloak/.env`) with database credentials, JWT secrets, and service URLs. The system integrates with:

- Classic arXiv database (MySQL)
- Keycloak authentication server
- arXiv submission system

## Testing

The project uses pytest for Python testing and Jest for JavaScript testing. Database tests require Docker to run a test MySQL instance. Type checking is done with mypy for Python and TypeScript for the frontend.

## Code Quality

- Python code uses mypy for type checking with strict settings
- Linting is enforced with pylint (minimum score 8/10)
- Frontend uses ESLint with React-specific rules
- All components follow established patterns for consistency