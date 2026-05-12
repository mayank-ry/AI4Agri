-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ==========================================
-- 1. TABLE: farmers
-- ==========================================
CREATE TABLE farmers (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    auth_user_id uuid UNIQUE, -- Links to Supabase auth.users
    name varchar(100) NOT NULL,
    phone varchar(15) UNIQUE NOT NULL,
    district varchar(100) NOT NULL,
    state varchar(50) NOT NULL,
    preferred_lang varchar(5) DEFAULT 'hi',
    created_at timestamptz DEFAULT now()
);

-- ==========================================
-- 2. TABLE: fields
-- ==========================================
CREATE TABLE fields (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    farmer_id uuid REFERENCES farmers(id) ON DELETE CASCADE,
    field_name varchar(100) DEFAULT 'Mera Khet',
    crop_type varchar(50) NOT NULL,
    growth_stage varchar(30) DEFAULT 'vegetative',
    area_hectares float NOT NULL,
    latitude float NOT NULL,
    longitude float NOT NULL,
    sowing_date date,
    is_active boolean DEFAULT true,
    created_at timestamptz DEFAULT now()
);

-- ==========================================
-- 3. TABLE: ndvi_readings
-- ==========================================
CREATE TABLE ndvi_readings (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    field_id uuid REFERENCES fields(id) ON DELETE CASCADE,
    ndvi_value float NOT NULL,
    health_status varchar(20) NOT NULL,
    health_color varchar(10) NOT NULL,
    satellite_date date NOT NULL,
    created_at timestamptz DEFAULT now()
);

-- ==========================================
-- 4. TABLE: soil_readings
-- ==========================================
CREATE TABLE soil_readings (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    field_id uuid REFERENCES fields(id) ON DELETE CASCADE,
    moisture_pct float,
    ph float,
    nitrogen_mg_kg float,
    phosphorus_mg_kg float,
    potassium_mg_kg float,
    source varchar(20) DEFAULT 'api',
    recorded_at timestamptz DEFAULT now()
);

-- ==========================================
-- 5. TABLE: health_scores
-- ==========================================
CREATE TABLE health_scores (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    field_id uuid REFERENCES fields(id) ON DELETE CASCADE,
    achs_score float NOT NULL,
    wsri_score float,
    cyas_score float,
    ndvi_component float,
    soil_component float,
    weather_component float,
    calculated_at timestamptz DEFAULT now()
);

-- ==========================================
-- 6. TABLE: disease_detections
-- ==========================================
CREATE TABLE disease_detections (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    field_id uuid REFERENCES fields(id) ON DELETE CASCADE,
    image_url text NOT NULL,
    disease_name varchar(100) NOT NULL,
    disease_name_hi varchar(100),
    confidence float NOT NULL,
    severity varchar(20),
    treatment_en text,
    treatment_hi text,
    top3_predictions jsonb,
    detected_at timestamptz DEFAULT now()
);

-- ==========================================
-- 7. TABLE: irrigation_recommendations
-- ==========================================
CREATE TABLE irrigation_recommendations (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    field_id uuid REFERENCES fields(id) ON DELETE CASCADE,
    wsri_score float,
    water_liters_ha float NOT NULL,
    schedule_datetime timestamptz,
    priority varchar(10) DEFAULT 'MEDIUM',
    reason_hi text,
    et0_used float,
    is_completed boolean DEFAULT false,
    created_at timestamptz DEFAULT now()
);

-- ==========================================
-- 8. TABLE: alerts
-- ==========================================
CREATE TABLE alerts (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    field_id uuid REFERENCES fields(id) ON DELETE CASCADE,
    farmer_id uuid REFERENCES farmers(id) ON DELETE CASCADE,
    alert_type varchar(30) NOT NULL,
    priority varchar(10) NOT NULL DEFAULT 'MEDIUM',
    title_hi varchar(200),
    message_hi text,
    is_read boolean DEFAULT false,
    created_at timestamptz DEFAULT now()
);


-- ==========================================
-- INDEXES
-- ==========================================
CREATE INDEX ON fields(farmer_id);
CREATE INDEX ON ndvi_readings(field_id, satellite_date DESC);
CREATE INDEX ON health_scores(field_id, calculated_at DESC);
CREATE INDEX ON disease_detections(field_id, detected_at DESC);
CREATE INDEX ON alerts(farmer_id, created_at DESC);


-- ==========================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ==========================================

-- Enable RLS on all tables
ALTER TABLE farmers ENABLE ROW LEVEL SECURITY;
ALTER TABLE fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE ndvi_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE soil_readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE health_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE disease_detections ENABLE ROW LEVEL SECURITY;
ALTER TABLE irrigation_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- 1. farmers: auth.uid() = auth_user_id
CREATE POLICY "Farmers can access their own profile" 
ON farmers FOR ALL USING (auth.uid() = auth_user_id);

-- 2. fields: farmer_id IN (SELECT id FROM farmers WHERE auth_user_id = auth.uid())
CREATE POLICY "Farmers can access their own fields" 
ON fields FOR ALL USING (
    farmer_id IN (SELECT id FROM farmers WHERE auth_user_id = auth.uid())
);

-- 3. ndvi_readings
CREATE POLICY "Farmers can access their own ndvi readings" 
ON ndvi_readings FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farmer_id IN (SELECT id FROM farmers WHERE auth_user_id = auth.uid()))
);

-- 4. soil_readings
CREATE POLICY "Farmers can access their own soil readings" 
ON soil_readings FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farmer_id IN (SELECT id FROM farmers WHERE auth_user_id = auth.uid()))
);

-- 5. health_scores
CREATE POLICY "Farmers can access their own health scores" 
ON health_scores FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farmer_id IN (SELECT id FROM farmers WHERE auth_user_id = auth.uid()))
);

-- 6. disease_detections
CREATE POLICY "Farmers can access their own disease detections" 
ON disease_detections FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farmer_id IN (SELECT id FROM farmers WHERE auth_user_id = auth.uid()))
);

-- 7. irrigation_recommendations
CREATE POLICY "Farmers can access their own irrigation recommendations" 
ON irrigation_recommendations FOR ALL USING (
    field_id IN (SELECT id FROM fields WHERE farmer_id IN (SELECT id FROM farmers WHERE auth_user_id = auth.uid()))
);

-- 8. alerts (Uses farmer_id directly for faster lookup, or field_id)
CREATE POLICY "Farmers can access their own alerts" 
ON alerts FOR ALL USING (
    farmer_id IN (SELECT id FROM farmers WHERE auth_user_id = auth.uid())
);
