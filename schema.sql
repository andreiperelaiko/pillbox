CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    telegram VARCHAR(100),
    CONSTRAINT users_telegram_unique UNIQUE (telegram),
    telegram_chat_id TEXT,
    password_hash TEXT,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    email_verification_token TEXT,
    email_verification_expires_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS user_guardians (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    guardian_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship TEXT,
    UNIQUE(user_id, guardian_id)
);

CREATE TABLE IF NOT EXISTS guardian_invites (
    id SERIAL PRIMARY KEY,
    patient_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    guardian_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    relationship TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    guardian_telegram_notified BOOLEAN NOT NULL DEFAULT FALSE,
    patient_telegram_notified BOOLEAN NOT NULL DEFAULT FALSE,
    initiated_by VARCHAR(20) NOT NULL DEFAULT 'guardian',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(patient_user_id, guardian_user_id)
);

CREATE TABLE IF NOT EXISTS medications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS medication_schedules (
    id SERIAL PRIMARY KEY,
    medication_id INTEGER NOT NULL REFERENCES medications(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    intake_at TIMESTAMP WITH TIME ZONE NOT NULL,
    taken BOOLEAN NOT NULL DEFAULT FALSE,
    dose TEXT
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES medication_schedules(id) ON DELETE CASCADE,
    guardian_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    telegram_sent_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS schedule_reminder_stats (
    schedule_id INTEGER NOT NULL REFERENCES medication_schedules(id) ON DELETE CASCADE,
    recipient_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    sent_count INTEGER NOT NULL DEFAULT 0,
    last_sent_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (schedule_id, recipient_user_id)
);

CREATE TABLE IF NOT EXISTS email_outbox (
    id SERIAL PRIMARY KEY,
    to_email VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NOT NULL,
    body TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);