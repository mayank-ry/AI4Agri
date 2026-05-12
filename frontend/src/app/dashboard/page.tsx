'use client';
import { useEffect, useState } from 'react';
import { supabase, Field } from '@/lib/supabase';
import { getFieldHealth } from '@/lib/api';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';

// A simple Map placeholder component since Leaflet requires specific browser setup
const MapComponent = dynamic(() => Promise.resolve(({ field, health }: { field: Field; health: { health_status: string } | null }) => (
  <div className="w-full h-full bg-green-100 flex items-center justify-center rounded-lg border-2 border-green-200">
    <div className="text-center text-green-800">
      <p className="font-bold">📍 {field.field_name}</p>
      <p className="text-sm">Health: {health ? health.health_status : 'Loading...'}</p>
    </div>
  </div>
)), { ssr: false });

interface HealthData {
  achs_score: number; 
  wsri_score: number;
  ndvi_value: number; 
  health_status: string;
  health_color: string; 
  message_hi: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [fields, setFields] = useState<Field[]>([]);
  const [selectedField, setSelectedField] = useState<Field | null>(null);
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadFields() {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        router.push('/auth/login');
        return;
      }

      // We need farmer_id first, then fields. Or use RLS which auto-filters fields.
      const { data: fieldsData } = await supabase.from('fields').select('*');
      
      if (fieldsData && fieldsData.length > 0) {
        setFields(fieldsData);
        setSelectedField(fieldsData[0]);
      }
      setLoading(false);
    }
    loadFields();
  }, [router]);

  useEffect(() => {
    if (selectedField) {
      async function loadHealth() {
        try {
          const healthData = await getFieldHealth(selectedField!.id);
          if (healthData && healthData.success) {
            setHealth({
              achs_score: healthData.achs.achs_score,
              wsri_score: healthData.wsri.wsri_score,
              ndvi_value: healthData.raw_data.ndvi,
              health_status: healthData.achs.status_hi,
              health_color: healthData.achs.achs_score >= 55 ? '#22c55e' : '#ef4444',
              message_hi: healthData.achs.status_hi
            });
          }
        } catch (error) {
          console.error("Failed to load health", error);
        }
      }
      loadHealth();
    }
  }, [selectedField]);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading Data...</div>;
  }

  if (!fields.length) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 p-4">
        <h2 className="text-2xl font-bold mb-4">Koi khet register nahi hai</h2>
        <button onClick={() => router.push('/field/register')} className="bg-green-600 text-white px-6 py-3 rounded-lg">
          Naya Khet Jodein ➕
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 pb-24">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-green-700">🌾 AI4Agri</h1>
        <select 
          className="bg-white border rounded p-2 text-sm text-gray-700 shadow-sm"
          value={selectedField?.id || ''}
          onChange={(e) => setSelectedField(fields.find(f => f.id === e.target.value) || null)}
        >
          {fields.map(f => (
            <option key={f.id} value={f.id}>{f.field_name} ({f.crop_type})</option>
          ))}
        </select>
      </div>

      {/* 4 KPI Cards - simple grid */}
      <div className="grid grid-cols-2 gap-3 mb-6">
        {/* Card 1: ACHS Health Score */}
        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-green-500 flex flex-col items-center justify-center">
          <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">Health (ACHS)</p>
          <p className="text-3xl font-bold text-gray-800">{health ? `${health.achs_score}` : '...'}</p>
        </div>
        {/* Card 2: Water Stress WSRI */}
        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-blue-500 flex flex-col items-center justify-center">
          <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">Water Need</p>
          <p className="text-3xl font-bold text-blue-600">{health ? `${health.wsri_score}%` : '...'}</p>
        </div>
        {/* Card 3: Status */}
        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-yellow-500 flex flex-col items-center justify-center">
          <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">Crop Status</p>
          <p className="text-lg font-bold text-gray-800 text-center">{health ? health.health_status : '...'}</p>
        </div>
        {/* Card 4: NDVI Status */}
        <div className="bg-white p-4 rounded-xl shadow-sm border-l-4 border-emerald-500 flex flex-col items-center justify-center">
          <p className="text-gray-500 text-xs font-medium uppercase tracking-wider mb-1">Satellite (NDVI)</p>
          <p className="text-2xl font-bold text-gray-800">{health ? health.ndvi_value.toFixed(2) : '...'}</p>
        </div>
      </div>

      {/* Map - lightweight */}
      <div className="h-48 rounded-xl overflow-hidden shadow-sm mb-6 bg-white p-2">
        {selectedField && <MapComponent field={selectedField} health={health}/>}
      </div>

      {/* Quick action buttons - 4 large buttons */}
      <div className="grid grid-cols-2 gap-4">
        <button onClick={() => router.push('/disease')}
          className="bg-emerald-600 hover:bg-emerald-700 transition shadow-md text-white py-6 rounded-2xl font-semibold flex flex-col items-center gap-2">
          <span className="text-3xl">📸</span>
          <span className="text-sm">Fasal Doctor</span>
        </button>
        <button onClick={() => router.push('/irrigation')}
          className="bg-blue-600 hover:bg-blue-700 transition shadow-md text-white py-6 rounded-2xl font-semibold flex flex-col items-center gap-2">
          <span className="text-3xl">💧</span>
          <span className="text-sm">Paani Advice</span>
        </button>
        <button onClick={() => router.push('/chatbot')}
          className="bg-purple-600 hover:bg-purple-700 transition shadow-md text-white py-6 rounded-2xl font-semibold flex flex-col items-center gap-2">
          <span className="text-3xl">🤖</span>
          <span className="text-sm">Kisan Mitra</span>
        </button>
        <button onClick={() => router.push('/field/register')}
          className="bg-orange-500 hover:bg-orange-600 transition shadow-md text-white py-6 rounded-2xl font-semibold flex flex-col items-center gap-2">
          <span className="text-3xl">➕</span>
          <span className="text-sm">Naya Khet</span>
        </button>
      </div>
    </div>
  );
}
