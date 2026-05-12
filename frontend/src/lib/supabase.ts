import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'PASTE_YOUR_SUPABASE_URL_HERE';
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'PASTE_YOUR_SUPABASE_ANON_KEY_HERE';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

// TypeScript types for our tables
export type Farmer = {
  id: string; 
  name: string; 
  phone: string;
  district: string; 
  state: string; 
  preferred_lang: string;
};

export type Field = {
  id: string; 
  farmer_id: string; 
  field_name: string;
  crop_type: string; 
  growth_stage: string;
  area_hectares: number; 
  latitude: number; 
  longitude: number;
  sowing_date: string; 
  is_active: boolean;
};

export type HealthScore = {
  achs_score: number; 
  wsri_score: number;
  cyas_score: number; 
  calculated_at: string;
};

export type DiseaseDetection = {
  disease_name: string; 
  disease_name_hi: string;
  confidence: number; 
  severity: string;
  treatment_hi: string; 
  image_url: string;
};
