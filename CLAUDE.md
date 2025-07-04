# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a disinformation analysis platform consisting of:
- **Backend**: Flask API with MLX-optimized machine learning models for tweet analysis
- **Frontend**: React/Vite application for interactive dashboard
- **Analysis Pipeline**: Python scripts for narrative generation, similarity scoring, and polarity testing

- **CloudFlare Tunnel**: Self-hosting using Cloudflare on narrativedashboard.xyz, with the api on localhost:5000 and the frontend on localhost:3000

## Development Commands

### Backend (Flask API)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run Flask development server
python app.py

# The API runs on localhost:5000 with /api prefix
```

### Frontend (React Dashboard)
```bash
# Navigate to frontend directory
cd tweet-analysis-app

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Core Architecture

### Backend API Structure
- **app.py**: Main Flask application with Firebase authentication middleware
- **Authentication**: All API endpoints require Firebase token verification via `@verify_firebase_token` decorator
- **CORS**: Configured for specific production domains (narrativedashboard.xyz)
- **ML Models**: 
  - MLX-optimized models for Mac GPU acceleration
  - SentenceTransformer for embeddings (MPS/GPU accelerated)
  - Mistral models for summarization and polarity analysis

### Key API Endpoints
- `POST /api/post-datasets` - List available CSV datasets
- `POST /api/trace-over-time` - Filter tweets by narrative similarity over time
- `POST /api/generate-narratives` - Generate narrative summaries from filtered data
- `POST /api/save-filtered-data` - Save analysis results to server
- `GET /api/list-saved-data` - List saved analysis files
- `POST /api/load-saved-data` - Load previously saved analysis

### Analysis Pipeline Components
- **generate_narratives.py**: Clusters tweets and generates narrative summaries using KMeans + LLM
- **impact_analysis.py**: Analyzes tweet polarity (support/opposition/neutral) relative to target narratives
- **graph_sims.py**: Calculates similarity scores between tweets and target narratives over time
- **preprocess.py**: Data preprocessing utilities for tweet datasets

### Frontend Architecture
- **React 19** with Vite build system
- **TailwindCSS** for styling
- **Recharts** for data visualization
- **Firebase Authentication** integration
- **Components**:
  - `TweetAnalysisDashboard.jsx`: Main analysis interface
  - `SavedDataBrowser.jsx`: Manage saved analysis results
  - `Auth.jsx`: Firebase authentication context
  - `LoginForm.jsx`: Authentication UI

### Data Flow
1. User selects tweet datasets and analysis parameters
2. Backend processes tweets using similarity scoring against target narrative
3. Results filtered by date range and similarity threshold
4. Optional narrative generation using clustering + LLM summarization
5. Results visualized in interactive dashboard with time series charts

### Authentication & Security
- Firebase Admin SDK for token verification
- Environment variables for sensitive credentials
- CORS restrictions to specific domains
- All API endpoints protected with authentication middleware

### Performance Optimizations
- MLX framework for Apple Silicon GPU acceleration
- MPS (Metal Performance Shaders) for PyTorch models
- Memory management with garbage collection in analysis endpoints
- Sourcemap generation disabled in production builds

## File Structure
- `tweets/`: Raw tweet datasets (CSV format)
- `saved_data/`: Processed analysis results (pickle + CSV)
- `tweet-analysis-app/`: React frontend application
- `glue_results/`: Evaluation metrics and visualizations
- Analysis scripts: `generate_narratives.py`, `impact_analysis.py`, `graph_sims.py`, `preprocess.py`

## Environment Setup
- Requires `FIREBASE_ADMIN_SDK_KEY` environment variable for authentication
- Python virtual environment recommended for backend dependencies
- Node.js environment for frontend development