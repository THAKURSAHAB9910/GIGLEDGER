-- GIGLEDGER Database Schema
-- Compatible with SQLite and PostgreSQL

-- 1. Workers Dimension Table (Pseudonymous Only)
CREATE TABLE IF NOT EXISTS workers (
    worker_pseudonym VARCHAR(32) PRIMARY KEY,
    platform_category VARCHAR(64) NOT NULL,
    vehicle_type VARCHAR(64) NOT NULL,
    primary_city VARCHAR(64) NOT NULL,
    data_origin VARCHAR(32) NOT NULL DEFAULT 'DEMO_SYNTHETIC',
    consent_confirmed BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Shifts Fact Table
CREATE TABLE IF NOT EXISTS shifts (
    shift_id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_pseudonym VARCHAR(32) NOT NULL,
    shift_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    total_hours REAL NOT NULL CHECK (total_hours >= 0.0),
    orders_completed INTEGER NOT NULL DEFAULT 0 CHECK (orders_completed >= 0),
    total_distance_km REAL NOT NULL DEFAULT 0.0 CHECK (total_distance_km >= 0.0),
    paid_distance_km REAL DEFAULT 0.0 CHECK (paid_distance_km >= 0.0),
    waiting_time_hours REAL DEFAULT 0.0 CHECK (waiting_time_hours >= 0.0),
    
    -- Earnings Components
    base_payout REAL NOT NULL DEFAULT 0.0 CHECK (base_payout >= 0.0),
    incentive_pay REAL NOT NULL DEFAULT 0.0 CHECK (incentive_pay >= 0.0),
    bonus_pay REAL NOT NULL DEFAULT 0.0 CHECK (bonus_pay >= 0.0),
    
    -- Deductions & Penalties
    deductions REAL NOT NULL DEFAULT 0.0 CHECK (deductions >= 0.0),
    cancellations_count INTEGER DEFAULT 0 CHECK (cancellations_count >= 0),
    cancellation_penalties REAL DEFAULT 0.0 CHECK (cancellation_penalties >= 0.0),
    
    -- Operating Expenses
    fuel_expense REAL NOT NULL DEFAULT 0.0 CHECK (fuel_expense >= 0.0),
    maintenance_expense REAL NOT NULL DEFAULT 0.0 CHECK (maintenance_expense >= 0.0),
    other_expenses REAL NOT NULL DEFAULT 0.0 CHECK (other_expenses >= 0.0),
    
    -- Contextual Dimensions
    platform_category VARCHAR(64),
    vehicle_type VARCHAR(64),
    city VARCHAR(64),
    data_origin VARCHAR(32) NOT NULL DEFAULT 'DEMO_SYNTHETIC',
    consent_confirmed BOOLEAN NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (worker_pseudonym) REFERENCES workers (worker_pseudonym)
);

CREATE INDEX IF NOT EXISTS idx_shifts_worker_date ON shifts (worker_pseudonym, shift_date);
CREATE INDEX IF NOT EXISTS idx_shifts_date ON shifts (shift_date);
CREATE INDEX IF NOT EXISTS idx_shifts_city_vehicle ON shifts (city, vehicle_type);
CREATE INDEX IF NOT EXISTS idx_shifts_origin ON shifts (data_origin);

-- 3. Consent Audit Log
CREATE TABLE IF NOT EXISTS consent_records (
    consent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_pseudonym VARCHAR(32) NOT NULL,
    consent_version VARCHAR(16) NOT NULL,
    agreed BOOLEAN NOT NULL,
    agreed_no_passwords BOOLEAN NOT NULL,
    research_purpose_accepted BOOLEAN NOT NULL,
    agreed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Benchmark Public Research Data
CREATE TABLE IF NOT EXISTS benchmark_research (
    benchmark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_title VARCHAR(128) NOT NULL,
    publication_year INTEGER NOT NULL,
    geography VARCHAR(64) NOT NULL,
    platform_type VARCHAR(64) NOT NULL,
    reported_gross_hourly REAL,
    reported_net_hourly REAL,
    reported_fuel_expense_ratio REAL,
    reported_waiting_time_ratio REAL,
    sample_size INTEGER,
    notes TEXT
);
