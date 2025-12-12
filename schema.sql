-- Медикаменты
CREATE TABLE IF NOT EXISTS medications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    form VARCHAR(50) NOT NULL CHECK (form IN ('таблетки', 'капсулы', 'жидкость', 'укол', 'порошок', 'мазь', 'спрей')),
    default_amount INTEGER NOT NULL DEFAULT 1 CHECK (default_amount >= 1),
    image_url TEXT,
    created_at BIGINT NOT NULL
);

-- Приемы медикаментов
CREATE TABLE IF NOT EXISTS intakes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date_time BIGINT NOT NULL CHECK (date_time > 0),
    medications JSONB NOT NULL,  -- Массив MedicationDose
    created_at BIGINT NOT NULL,
    series_id UUID
);

-- Опекуны
CREATE TABLE IF NOT EXISTS caregivers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50) NOT NULL,
    email VARCHAR(255) NOT NULL,
    telegram VARCHAR(100) NOT NULL,
    created_at BIGINT NOT NULL
);

-- Настройки (одна запись)
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    notification_delay_minutes INTEGER NOT NULL DEFAULT 30 CHECK (notification_delay_minutes >= 0)
);

-- Инициализировать настройки дефолтными значениями
INSERT INTO settings (id, notification_delay_minutes)
VALUES (1, 30)
ON CONFLICT (id) DO NOTHING;

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_intakes_date_time ON intakes(date_time);
CREATE INDEX IF NOT EXISTS idx_intakes_series_id ON intakes(series_id);
CREATE INDEX IF NOT EXISTS idx_medications_name ON medications(name);
