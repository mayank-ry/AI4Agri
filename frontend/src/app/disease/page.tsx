// frontend/src/app/disease/page.tsx
'use client';
import { useState, useEffect } from 'react';
import type { ComponentProps } from 'react';
import { useRouter } from 'next/navigation';
import { supabase, Field } from '@/lib/supabase';
import { detectDisease } from '@/lib/api';
import { ImageUploader } from '@/components/ImageUploader';
import { PredictionCard } from '@/components/PredictionCard';
import { motion } from 'framer-motion';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

type DiseaseResult = ComponentProps<typeof PredictionCard>['result'];

export default function DiseaseDetection() {
  const router = useRouter();
  const [fields, setFields] = useState<Field[]>([]);
  const [selectedField, setSelectedField] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<DiseaseResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>('');

  // Fetch fields on mount
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

  const handleDetect = async () => {
    if (!file || !selectedField) return;
    setLoading(true);
    setErrorMsg('');
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('image', file);
      formData.append('field_id', selectedField);
      const response = await detectDisease(formData);
      if (response && response.success) {
        setResult(response.detection);
      } else {
        setErrorMsg('सर्वर से प्रतिक्रिया नहीं मिली। कृपया बाद में पुनः प्रयास करें।');
      }
    } catch (e) {
      console.error('Detection error:', e);
      setErrorMsg('डिटेक्शन के दौरान त्रुटि हुई। नेटवर्क कनेक्शन जाँचें।');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 pb-20 flex flex-col items-center">
      {/* Header */}
      <div className="flex items-center mb-6 gap-3 w-full max-w-3xl">
        <button onClick={() => router.back()} className="text-2xl">
          🔙
        </button>
        <h1 className="text-2xl font-bold text-green-800">फसल डॉक्टर 📸</h1>
      </div>

      {/* Field selector */}
      <div className="bg-white w-full max-w-3xl p-4 rounded-xl shadow-sm mb-6">
        <label className="block text-gray-700 font-medium mb-2">खेत चुनें</label>
        <select
          className="w-full bg-gray-50 border rounded-lg p-3 text-gray-800"
          value={selectedField}
          onChange={e => setSelectedField(e.target.value)}
        >
          {fields.map(f => (
            <option key={f.id} value={f.id}>
              {f.field_name} ({f.crop_type})
            </option>
          ))}
        </select>
      </div>

      {/* Image uploader */}
      <ImageUploader
        file={file}
        setFile={setFile}
        preview={preview}
        setPreview={setPreview}
        disabled={loading}
      />

      {/* Detect button */}
      <motion.button
        onClick={handleDetect}
        disabled={!file || loading}
        className={`w-full max-w-3xl mt-4 py-3 rounded-xl font-bold text-white text-lg flex justify-center items-center gap-2 ${!file || loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-emerald-600 hover:bg-emerald-700 shadow-lg'}`}
        whileHover={!loading && file ? { scale: 1.02 } : {}}
      >
        {loading ? (
          <motion.span
            className="animate-pulse"
            initial={{ opacity: 0.5 }}
            animate={{ opacity: 1 }}
            transition={{ repeat: Infinity, duration: 1 }}
          >
            ⏳ जाँच जारी है…
          </motion.span>
        ) : (
          'रोग का पता लगाएँ'
        )}
      </motion.button>

      {/* Error alert */}
      {errorMsg && (
        <Alert variant="destructive" className="w-full max-w-3xl mt-4">
          <AlertTitle>⚠️ त्रुटि</AlertTitle>
          <AlertDescription>{errorMsg}</AlertDescription>
        </Alert>
      )}

      {/* Result card */}
      {result && (
        <div className="w-full max-w-3xl mt-6">
          <PredictionCard result={result} />
        </div>
      )}
    </div>
  );
}
