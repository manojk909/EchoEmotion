# 🎙️ EchoEmotion — Speech Emotion Recognition

> Detect human emotions (calm, happy, fearful, disgust) from audio in real-time using a multi-model ML pipeline, a FastAPI backend, and a React + Tailwind frontend.

[![CI](https://github.com/your-username/echoemotion/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/echoemotion/actions)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev)

---

## 📖 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Quick Start (Docker)](#quick-start-docker)
5. [Local Development](#local-development)
6. [Dataset Setup](#dataset-setup)
7. [Training the Model](#training-the-model)
8. [API Reference](#api-reference)
9. [Database Schema](#database-schema)
10. [Deployment](#deployment)
11. [Testing](#testing)
12. [Contributing](#contributing)

---

## Overview

EchoEmotion is an end-to-end production-ready Speech Emotion Recognition system built on the **RAVDESS** dataset. It compares five classifiers (MLP, Random Forest, SVM, XGBoost, LightGBM) and automatically selects the best by weighted F1 score.

**Accuracy: ~72 – 78% depending on model selection and dataset size.**

### Features
- 🎤 Browser microphone recording
- 📁 Drag-and-drop audio upload (WAV, MP3, OGG, FLAC, M4A)
- 📊 Probability chart + radar profile per prediction
- 🏆 Model comparison table with cross-validation
- 📈 Full dashboard with emotion distribution analytics
- 🔐 JWT authentication (register / login)
- 🐘 PostgreSQL persistence for all predictions
- 🐳 Docker Compose for one-command startup

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   React + Vite                      │
│  LandingPage / PredictPage / DashboardPage          │
│  Axios + TanStack Query + Framer Motion             │
└────────────────────┬────────────────────────────────┘
                     │ HTTP (REST)
┌────────────────────▼────────────────────────────────┐
│              FastAPI  (Python 3.11)                 │
│  /api/v1/predict   /train   /dashboard   /auth      │
│  JWT Auth · Rate Limiting · Swagger UI              │
│                                                     │
│  ┌───────────────────┐   ┌─────────────────────┐   │
│  │   ML Pipeline     │   │   PostgreSQL (ORM)  │   │
│  │  FeatureExtractor │   │  User / Prediction  │   │
│  │  ModelTrainer     │   │  EmotionStat        │   │
│  │  EmotionPredictor │   │  ModelRegistry      │   │
│  └───────────────────┘   └─────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

![CI/CD](https://github.com/manojk909/EchoEmotion/actions/workflows/ci.yml/badge.svg)

## Tech Stack

| Layer      | Technology                                       |
|------------|--------------------------------------------------|
| Frontend   | React 18 · Vite · TailwindCSS · Framer Motion    |
| Charts     | Recharts                                         |
| State      | TanStack Query · Zustand                         |
| Backend    | FastAPI · Uvicorn · Pydantic v2                  |
| Auth       | JWT (python-jose) · bcrypt (passlib)             |
| ML         | scikit-learn · librosa · XGBoost · LightGBM      |
| Database   | PostgreSQL 16 · SQLAlchemy 2 (async)             |
| DevOps     | Docker · Docker Compose · GitHub Actions         |

---

## Quick Start (Docker)

```bash
git clone https://github.com/your-username/echoemotion.git
cd echoemotion

# 1. Add RAVDESS dataset (see Dataset Setup below)
# 2. Copy environment files
cp backend/.env.example backend/.env

# 3. Start everything
docker compose up --build

# API docs:     http://localhost:8000/docs
# Frontend:     http://localhost:3000
# PostgreSQL:   localhost:5432
```

---

## Local Development

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL to your local Postgres

# Create tables
python scripts/init_db.py

# Run dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# Create .env.local
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env.local
npm run dev   # → http://localhost:5173
```

---

## Dataset Setup

1. Download the [RAVDESS dataset](https://zenodo.org/record/1188976) (speech-only files).
2. Place the extracted `Actor_*` folders inside `backend/dataset/`:

```
backend/
└── dataset/
    ├── Actor_01/
    │   ├── 03-01-01-01-01-01-01.wav
    │   └── ...
    ├── Actor_02/
    └── ...
```

---

## Training the Model

### Via API (recommended)
```bash
curl -X POST http://localhost:8000/api/v1/train \
  -H "Content-Type: application/json" \
  -d '{"observed_emotions": ["calm","happy","fearful","disgust"], "compare_models": true}'
```

### Via Python script
```bash
cd backend
python -c "
from app.ml.trainer import ModelTrainer
from app.core.config import EMOTIONS_MAP
t = ModelTrainer('dataset', 'models', EMOTIONS_MAP)
result = t.train(['calm','happy','fearful','disgust'])
print(result['best_model'], result['best_accuracy'])
"
```

The pipeline will train **MLP · Random Forest · SVM · XGBoost · LightGBM**, run 5-fold cross-validation on each, and save the best model automatically.

---

## API Reference

| Method | Endpoint               | Description                          |
|--------|------------------------|--------------------------------------|
| GET    | `/api/v1/health`       | Health check + model status          |
| GET    | `/api/v1/emotions`     | List supported emotions              |
| POST   | `/api/v1/predict`      | Upload audio → emotion + confidence  |
| POST   | `/api/v1/train`        | Train / retrain model                |
| GET    | `/api/v1/model-info`   | Active model metadata                |
| GET    | `/api/v1/metrics`      | Full training metrics + comparison   |
| GET    | `/api/v1/dashboard`    | Prediction statistics                |
| POST   | `/api/v1/auth/register`| Create account                       |
| POST   | `/api/v1/auth/login`   | Get JWT token                        |
| GET    | `/api/v1/auth/me`      | Current user info                    |

Full interactive docs: `http://localhost:8000/docs`

---

## Database Schema

```sql
users (id UUID PK, email, username, hashed_password, is_active, created_at)
predictions (id UUID PK, user_id FK, filename, predicted_emotion, confidence,
             all_probabilities JSON, audio_duration_s, created_at)
emotion_stats (id, emotion UNIQUE, total_count, avg_confidence, last_updated)
model_registry (id, version, algorithm, accuracy, metrics JSON, is_active, created_at)
```

---

## Deployment

### Backend → Render / Railway
```
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Environment: set all vars from .env.example
```

### Frontend → Vercel
```bash
cd frontend
npm run build
# Deploy /dist to Vercel
# Set VITE_API_URL to your backend URL
```

### Database → Supabase / Neon
Free-tier PostgreSQL — just update `DATABASE_URL` in your env.

---

## Testing

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend
cd frontend
npm test
```

---

## Resume Description

> **Speech Emotion Recognition System** · Python · FastAPI · React · PostgreSQL · Docker
>
> Built an end-to-end ML system that detects emotions (calm, happy, fearful, disgust) from
> speech audio. Implemented a multi-model training pipeline comparing MLP, Random Forest,
> SVM, XGBoost, and LightGBM with 5-fold cross-validation and automatic best-model selection.
> Wrapped in a production FastAPI backend with JWT auth, rate limiting, and Swagger docs.
> React frontend features drag-and-drop upload, live microphone recording, and interactive
> probability charts. Deployed via Docker Compose with PostgreSQL persistence.

---

## LinkedIn Post Draft

> 🎙️ Just shipped EchoEmotion — my Speech Emotion Recognition project!
>
> 🧠 Multi-model ML pipeline (MLP · Random Forest · SVM · XGBoost · LightGBM) trained on RAVDESS
> 🚀 FastAPI backend with JWT auth, Swagger docs, and PostgreSQL
> 🎨 React + TailwindCSS frontend with real-time mic recording and probability charts
> 🐳 Fully dockerized with GitHub Actions CI/CD
>
> Live demo: [link] | GitHub: [link]
>
> #MachineLearning #Python #FastAPI #React #SpeechRecognition #OpenSource

---

MIT License © 2024 Your Name
