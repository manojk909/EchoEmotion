-- EchoEmotion Database Schema
-- Run: psql -U ser_user -d ser_db -f schema.sql

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Users ──────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email            VARCHAR(255) UNIQUE NOT NULL,
    username         VARCHAR(100) UNIQUE NOT NULL,
    hashed_password  VARCHAR(255) NOT NULL,
    is_active        BOOLEAN DEFAULT TRUE,
    is_admin         BOOLEAN DEFAULT FALSE,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email    ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- ── Predictions ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id            UUID REFERENCES users(id) ON DELETE SET NULL,
    filename           VARCHAR(255) NOT NULL,
    file_size_bytes    INTEGER,
    audio_duration_s   FLOAT,
    predicted_emotion  VARCHAR(50)  NOT NULL,
    confidence         FLOAT        NOT NULL,
    all_probabilities  JSONB,
    model_version      VARCHAR(50)  DEFAULT 'v1',
    created_at         TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictions_user_id          ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_predicted_emotion ON predictions(predicted_emotion);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at        ON predictions(created_at DESC);

-- ── Emotion stats (denormalised for fast dashboard) ───────────────────────────
CREATE TABLE IF NOT EXISTS emotion_stats (
    id           SERIAL PRIMARY KEY,
    emotion      VARCHAR(50) UNIQUE NOT NULL,
    total_count  INTEGER DEFAULT 0,
    avg_confidence FLOAT DEFAULT 0.0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- ── Model registry ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS model_registry (
    id         SERIAL PRIMARY KEY,
    version    VARCHAR(50) UNIQUE NOT NULL,
    algorithm  VARCHAR(100) NOT NULL,
    accuracy   FLOAT NOT NULL,
    metrics    JSONB,
    is_active  BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    notes      TEXT
);

-- Only one active model at a time
CREATE UNIQUE INDEX IF NOT EXISTS idx_model_registry_active
    ON model_registry(is_active)
    WHERE is_active = TRUE;
