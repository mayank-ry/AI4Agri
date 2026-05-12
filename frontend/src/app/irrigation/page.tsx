'use client';
import { useState, useEffect } from 'react';
import { supabase, Field } from '@/lib/supabase';
import { getIrrigationRecommendation } from '@/lib/api';
import { useRouter } from 'next/navigation';

interface IrrigationScheduleItem {
  day: number;
  action: string;
  liters: number;
}

interface IrrigationResult {
  recommendation: {
    priority: string;
    reason_hi: string;
  };
  rf_plan: {
    water_liters_ha: number;
    method_hi: string;
    schedule_7_days?: IrrigationScheduleItem[];
  };
}

export default function IrrigationAdvisor() {
  const router = useRouter();
  const [fields, setFields] = useState<Field[]>([]);
  const [selectedField, setSelectedField] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IrrigationResult | null>(null);

  useEffect(() => {
    async function fetchFields() {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return router.push('/auth/login');

      const { data } = await supabase.from('fields').select('*');
      if (data && data.length > 0) {
        setFields(data);
        setSelectedField(data[0].id);
      }
    }
    fetchFields();
  }, [router]);

  const handleRecommend = async () => {
    if (!selectedField) return;
    setLoading(true);
    setResult(null);
    try {
      const response = await getIrrigationRecommendation(selectedField);
      if (response && response.success) {
        setResult(response);
      }
    } catch (error) {
      console.error('Irrigation error:', error);
      alert('Error fetching recommendation. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getPriorityBadge = (pri: string) => {
    if (pri === 'CRITICAL') return 'bg-red-500';
    if (pri === 'HIGH') return 'bg-orange-500';
    if (pri === 'MEDIUM') return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 pb-20">
      <div className="flex items-center mb-6 gap-3">
        <button onClick={() => router.back()} className="text-2xl">🔙</button>
        <h1 className="text-2xl font-bold text-blue-800">Paani Advice 💧</h1>
      </div>

      <div className="bg-white p-4 rounded-xl shadow-sm mb-4">
        <label className="block text-gray-700 font-medium mb-2">Khet Chunein</label>
        <select 
          className="w-full bg-gray-50 border rounded-lg p-3 text-gray-800"
          value={selectedField}
          onChange={e => setSelectedField(e.target.value)}
        >
          {fields.map(f => <option key={f.id} value={f.id}>{f.field_name} ({f.crop_type})</option>)}
        </select>
      </div>

      <button 
        onClick={handleRecommend}
        disabled={loading || !selectedField}
        className={`w-full py-4 rounded-xl font-bold text-white text-lg shadow-md mb-6 ${loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
      >
        {loading ? <span className="animate-pulse">⏳ Data laa raha hai...</span> : "Paani Ki Zarurat Pata Karein"}
      </button>

      {result && (
        <div className="space-y-4 animate-fade-in">
          {/* Main Info */}
          <div className="bg-white p-5 rounded-xl shadow-lg border-t-4 border-blue-500 text-center">
            <h2 className="text-gray-600 font-medium text-sm uppercase tracking-wider mb-2">Paani Ki Zarurat (Water Needed)</h2>
            <p className="text-5xl font-black text-blue-600 mb-1">{result.rf_plan.water_liters_ha}</p>
            <p className="text-sm text-gray-500 mb-6">Liters per Hectare</p>
            
            <div className={`inline-block px-4 py-1 rounded-full text-white font-bold text-sm mb-4 ${getPriorityBadge(result.recommendation.priority)}`}>
              Priority: {result.recommendation.priority}
            </div>
            
            <div className="bg-blue-50 p-3 rounded-lg text-blue-800 text-sm font-medium">
              💡 {result.recommendation.reason_hi}
            </div>
            <div className="bg-gray-50 p-3 rounded-lg text-gray-700 text-sm font-medium mt-2">
              🛠 {result.rf_plan.method_hi}
            </div>
          </div>

          {/* Schedule Table */}
          {result.rf_plan.schedule_7_days && result.rf_plan.schedule_7_days.length > 0 && (
            <div className="bg-white p-4 rounded-xl shadow-sm">
              <h3 className="font-bold text-gray-800 mb-3 border-b pb-2">Agale 7 Din Ka Plan</h3>
              <div className="space-y-2">
                {result.rf_plan.schedule_7_days.map((item, idx) => (
                  <div key={idx} className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="bg-blue-100 text-blue-800 rounded-full w-8 h-8 flex items-center justify-center font-bold text-xs">D{item.day}</span>
                      <span className="text-gray-700 font-medium text-sm">{item.action}</span>
                    </div>
                    {item.liters > 0 && <span className="font-bold text-blue-600 text-sm">{item.liters} L</span>}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
