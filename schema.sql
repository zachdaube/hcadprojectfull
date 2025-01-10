-- Create the properties table
CREATE TABLE properties (
    id SERIAL PRIMARY KEY,
    account_number VARCHAR(20),
    street_address TEXT,
    city VARCHAR(100),
    zip_code VARCHAR(10),
    neighborhood_code VARCHAR(20),
    market_area VARCHAR(10),
    market_description TEXT,
    year_built INTEGER,
    building_area NUMERIC(12,2),
    land_area NUMERIC(12,2),
    acreage NUMERIC(8,4),
    land_value NUMERIC(12,2),
    building_value NUMERIC(12,2),
    extra_features_value NUMERIC(12,2),
    total_appraised_value NUMERIC(12,2),
    total_market_value NUMERIC(12,2),
    cdu NUMERIC(5,3),
    grade VARCHAR(5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX idx_properties_account ON properties(account_number);
CREATE INDEX idx_properties_neighborhood ON properties(neighborhood_code);
CREATE INDEX idx_properties_market_area ON properties(market_area);
CREATE INDEX idx_properties_building_area ON properties(building_area);
CREATE INDEX idx_properties_total_value ON properties(total_market_value);
CREATE INDEX idx_properties_zip ON properties(zip_code);