import axios from 'axios';
import { supabase } from './supabase';

const API = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
});

// Add Supabase JWT to every request
API.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// API functions
export const detectDisease = (formData: FormData) =>
  API.post('/disease/detect', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }).then(r => r.data);

export const getFieldHealth = (fieldId: string) =>
  API.get(`/health/${fieldId}`).then(r => r.data);

export const getIrrigationRecommendation = (fieldId: string) =>
  API.post('/irrigation/recommend', { field_id: fieldId }).then(r => r.data);

export const sendChatMessage = (message: string, fieldId: string, lang: string = 'hi') =>
  API.post('/chatbot/message', { message, field_id: fieldId, lang }).then(r => r.data);

export const getWeather = (fieldId: string) =>
  API.get(`/weather/${fieldId}`).then(r => r.data);

export const getChatSuggestions = (fieldId: string) =>
  API.get(`/chatbot/suggestions/${fieldId}`).then(r => r.data);

// Streaming version: posts to /chatbot/message/stream and calls `onChunk` for incremental text.
export async function sendChatMessageStreaming(
  message: string,
  fieldId: string,
  lang: string = 'hi',
  onChunk?: (chunk: string) => void
): Promise<{ response: string; intent?: string; model_used?: string }> {
  const baseURL = API.defaults.baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
  
  // Try to get token, but don't fail if it's missing (for test mode)
  let token: string | undefined;
  try {
    const tokenResp = await supabase.auth.getSession();
    token = tokenResp.data.session?.access_token;
  } catch {
    console.warn('Could not fetch token, proceeding without auth');
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  console.log('Streaming request to:', `${baseURL}/chatbot/message/stream`);

  const res = await fetch(`${baseURL}/chatbot/message/stream`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message, field_id: fieldId, lang }),
  });

  if (!res.ok) {
    const text = await res.text();
    console.error('Stream error:', res.status, text);
    throw new Error(`Stream failed: ${res.status} ${text}`);
  }

  if (!res.body) return { response: '' };

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let done = false;
  let buffer = '';
  let fullText = '';

  while (!done) {
    const { value, done: d } = await reader.read();
    done = d;
    if (value) {
      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // Process complete lines
      const lines = buffer.split(/\n\n|\n/).filter(Boolean);
      for (let i = 0; i < lines.length - 1; i++) {
        const line = lines[i];
        let textChunk = line;
        if (line.startsWith('data:')) {
          const payload = line.replace(/^data:\s*/i, '');
          try {
            const obj = JSON.parse(payload);
            textChunk = obj.delta ?? obj.text ?? payload;
          } catch {
            textChunk = payload;
          }
        } else {
          try {
            const obj = JSON.parse(line);
            textChunk = obj.delta ?? obj.text ?? line;
          } catch {
            textChunk = line;
          }
        }
        if (textChunk) {
          fullText += textChunk;
          if (onChunk) onChunk(textChunk);
        }
      }
      // Keep last incomplete line in buffer
      buffer = lines[lines.length - 1] ?? '';
    }
  }

  // Process remaining buffer
  if (buffer.trim()) {
    try {
      const obj = JSON.parse(buffer);
      return { 
        response: fullText, 
        intent: obj.intent, 
        model_used: obj.model_used 
      };
    } catch {
      return { response: fullText + buffer };
    }
  }

  return { response: fullText };
}
