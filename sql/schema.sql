DROP TABLE IF EXISTS fact_unusual_activity;
DROP TABLE IF EXISTS fact_options_event;
DROP TABLE IF EXISTS dim_option_contract;
DROP TABLE IF EXISTS dim_symbol;

CREATE TABLE dim_symbol (
    symbol_id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_option_contract (
    contract_id SERIAL PRIMARY KEY,
    contract_symbol TEXT NOT NULL UNIQUE,
    symbol TEXT NOT NULL,
    option_type TEXT NOT NULL,
    strike NUMERIC(12, 2) NOT NULL,
    expiration_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_option_contract_symbol
    ON dim_option_contract (symbol);

CREATE INDEX idx_dim_option_contract_expiration_date
    ON dim_option_contract (expiration_date);

CREATE INDEX idx_dim_option_contract_symbol_option_type_expiration
    ON dim_option_contract (symbol, option_type, expiration_date);

CREATE TABLE fact_options_event (
    event_id TEXT PRIMARY KEY,
    contract_symbol TEXT NOT NULL,
    symbol TEXT NOT NULL,
    option_type TEXT NOT NULL,
    strike NUMERIC(12, 2) NOT NULL,
    expiration_date DATE NOT NULL,
    bid NUMERIC(12, 4) NOT NULL,
    ask NUMERIC(12, 4) NOT NULL,
    last_price NUMERIC(12, 4) NOT NULL,
    volume INTEGER NOT NULL,
    open_interest INTEGER NOT NULL,
    volume_open_interest_ratio NUMERIC(12, 4),
    implied_volatility NUMERIC(12, 4) NOT NULL,
    delta NUMERIC(12, 4) NOT NULL,
    underlying_price NUMERIC(12, 4) NOT NULL,
    unusual_activity_score INTEGER NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    source TEXT NOT NULL,
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fact_options_event_symbol
    ON fact_options_event (symbol);

CREATE INDEX idx_fact_options_event_contract_symbol
    ON fact_options_event (contract_symbol);

CREATE INDEX idx_fact_options_event_event_timestamp
    ON fact_options_event (event_timestamp);

CREATE INDEX idx_fact_options_event_unusual_activity_score
    ON fact_options_event (unusual_activity_score);

CREATE INDEX idx_fact_options_event_symbol_event_timestamp
    ON fact_options_event (symbol, event_timestamp);

CREATE INDEX idx_fact_options_event_symbol_unusual_activity_score
    ON fact_options_event (symbol, unusual_activity_score);

CREATE TABLE fact_unusual_activity (
    activity_id SERIAL PRIMARY KEY,
    event_id TEXT NOT NULL,
    contract_symbol TEXT NOT NULL,
    symbol TEXT NOT NULL,
    flag TEXT NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    loaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_event_flag UNIQUE (event_id, flag)
);

CREATE INDEX idx_fact_unusual_activity_event_id
    ON fact_unusual_activity (event_id);

CREATE INDEX idx_fact_unusual_activity_symbol
    ON fact_unusual_activity (symbol);

CREATE INDEX idx_fact_unusual_activity_flag
    ON fact_unusual_activity (flag);

CREATE INDEX idx_fact_unusual_activity_event_timestamp
    ON fact_unusual_activity (event_timestamp);
