# Telemedicine Platform Setup Guide

## Initial Setup

### 1. Database Setup
```bash
# Create PostgreSQL database
# The database URL is automatically set in the DATABASE_URL environment variable
```

### 2. Python Dependencies
```bash
# Install Python packages
python -m pip install flask flask-sqlalchemy flask-login flask-migrate flask-cors
python -m pip install openai transformers torch sentencepiece accelerate
python -m pip install python-dotenv psycopg2-binary passlib email-validator

# Install AI/ML related packages
python -m pip install transformers torch sentencepiece accelerate
```

### 3. Node.js Dependencies
```bash
# Install Node.js packages
npm install

# Key frontend packages installed:
# - React and core dependencies
# - Shadcn UI components
# - Authentication and form handling
# - Video calling infrastructure
# - Data fetching and state management
```

## Development Commands

### Starting the Application
```bash
# Start the development server
npm run dev
```

### Database Management
```bash
# Initialize database
flask db init

# Create migrations
flask db migrate

# Apply migrations
flask db upgrade
```

### Build Commands
```bash
# Build the frontend
npm run build

# Build the backend
python run.py
```

## Environment Variables Required
```plaintext
# Database Configuration
DATABASE_URL=postgresql://...

# AI Model API Keys
OPENAI_API_KEY=sk-...
CHATBOT_MODEL=openai  # Options: openai, huggingface, llama

# Application Settings
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key
```

## Running Tests
```bash
# Frontend tests
npm test

# Backend tests
python -m pytest
```

## Deployment
```bash
# Build the application
npm run build

# Start production server
npm run start
```
