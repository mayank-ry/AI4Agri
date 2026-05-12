'use client';
import { useState, useEffect, useRef } from 'react';
import { supabase, Field } from '@/lib/supabase';
import { sendChatMessage, sendChatMessageStreaming } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { ChatMessage } from '@/components/ChatMessage';
import { motion, AnimatePresence } from 'framer-motion';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  intent?: string;
  modelUsed?: string;
  timestamp: Date;
}

interface SpeechRecognitionResultEventLike {
  results: ArrayLike<{ 0: { transcript: string } }>;
}

interface SpeechRecognitionErrorEventLike {
  error: string;
}

interface SpeechRecognitionLike {
  lang: string;
  onresult: ((event: SpeechRecognitionResultEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  onend: (() => void) | null;
  start: () => void;
}

interface SpeechRecognitionWindow extends Window {
  SpeechRecognition?: new () => SpeechRecognitionLike;
  webkitSpeechRecognition?: new () => SpeechRecognitionLike;
}

export default function KisanMitraChatbot() {
  const router = useRouter();
  const [fields, setFields] = useState<Field[]>([]);
  const [selectedField, setSelectedField] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([
    { 
      id: '0',
      text: "Namaste! Main aapka Kisan Mitra hoon. Fasal ya kheti se judi koi bhi samasya pooch sakte hain.",
      sender: 'bot',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [lang] = useState('hi');
  const [errorMsg, setErrorMsg] = useState('');
  const [useStreaming, setUseStreaming] = useState(false); // Start with false for testing

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const msgCountRef = useRef(0);

  useEffect(() => {
    async function fetchFields() {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        // For testing: skip auth check if no session
        // In production, redirect to /auth or your login page
        if (!session) {
          console.warn('No session found — using test mode');
          // For testing, set a default field
          setSelectedField('test-field-1');
          return;
        }

        const { data } = await supabase.from('fields').select('*');
        if (data && data.length > 0) {
          setFields(data);
          setSelectedField(data[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch fields:', error);
        setSelectedField('test-field-1');
      }
    }
    fetchFields();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (text: string) => {
    if (!text.trim() || !selectedField) return;
    
    const userMsg = text.trim();
    const userMsgId = `msg_${++msgCountRef.current}`;
    
    setMessages(prev => [...prev, { 
      id: userMsgId,
      text: userMsg, 
      sender: 'user',
      timestamp: new Date()
    }]);
    setInput('');
    setLoading(true);
    setErrorMsg('');

    try {
      if (useStreaming) {
        // Try streaming first
        const botMsgId = `msg_${++msgCountRef.current}`;
        setMessages(prev => [...prev, { 
          id: botMsgId,
          text: '', 
          sender: 'bot',
          timestamp: new Date()
        }]);

        await sendChatMessageStreaming(userMsg, selectedField, lang, (chunk) => {
          setMessages(prev => {
            const updated = [...prev];
            const botIdx = updated.findIndex(m => m.id === botMsgId);
            if (botIdx >= 0) {
              updated[botIdx].text += chunk;
            }
            return updated;
          });
        });
      } else {
        // Fallback to regular POST
        const res = await sendChatMessage(userMsg, selectedField, lang);
        if (res && res.response) {
          const botMsgId = `msg_${++msgCountRef.current}`;
          setMessages(prev => [...prev, { 
            id: botMsgId,
            text: res.response, 
            sender: 'bot', 
            intent: res.intent, 
            modelUsed: res.model_used,
            timestamp: new Date()
          }]);
        }
      }
    } catch (error: unknown) {
      console.error('Chat error:', error);
      const errMsg = error instanceof Error ? error.message : "Network issue. Kripya dobara try karein.";
      setErrorMsg(errMsg);
      
      // Fallback from streaming to regular if needed
      if (useStreaming && errMsg.includes('Stream')) {
        setUseStreaming(false);
        setErrorMsg('Streaming unavailable, using fallback mode');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVoiceInput = () => {
    const speechWindow = window as SpeechRecognitionWindow;
    const SpeechRecognition = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Aapka browser voice input support nahi karta. Chrome use karein.");
      return;
    }
    
    const recognition = new SpeechRecognition();
    recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
    recognition.start();
    setIsListening(true);

    recognition.onresult = (event: SpeechRecognitionResultEventLike) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      setIsListening(false);
    };

    recognition.onerror = (event: SpeechRecognitionErrorEventLike) => {
      setErrorMsg(`Voice error: ${event.error}`);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
  };

  const suggestions = [
    "Aaj paani dena chahiye?",
    "Fasal mein kya problem hai?",
    "Khaad kab daalen?",
    "Is hafte ka mausam kaisa hai?"
  ];

  return (
    <div className="flex flex-col h-screen bg-gray-50 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-700 to-purple-600 text-white p-4 shadow-lg flex items-center justify-between shrink-0 z-10">
        <div className="flex items-center gap-3 flex-1">
          <button onClick={() => router.back()} className="text-xl hover:scale-110 transition-transform">🔙</button>
          <div className="flex flex-col flex-1">
            <h1 className="font-bold text-lg leading-tight">Kisan Mitra 🤖</h1>
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              <span className="text-xs text-purple-200 uppercase tracking-wider font-semibold">Online</span>
            </div>
          </div>
        </div>
        <select 
          className="bg-purple-600 border border-purple-400 rounded-lg p-2 text-xs text-white max-w-[140px] truncate focus:ring-2 focus:ring-purple-300 outline-none"
          value={selectedField}
          onChange={e => setSelectedField(e.target.value)}
        >
          {fields.map(f => <option key={f.id} value={f.id}>{f.field_name}</option>)}
        </select>
      </div>

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-[#ece5dd] relative">
        <div className="absolute inset-0 opacity-5 pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/leaves.png')]"></div>
        
        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.2 }}
            >
              <ChatMessage 
                text={m.text} 
                sender={m.sender} 
                intent={m.intent} 
                modelUsed={m.modelUsed}
                timestamp={m.timestamp}
              />
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start items-end gap-2"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
              🤖
            </div>
            <div className="bg-white rounded-xl rounded-bl-none p-3 shadow-sm border border-gray-100 text-gray-500 text-sm flex gap-1 items-center">
              <span className="font-medium">सोच रहा हूँ</span>
              <span className="flex gap-0.5">
                <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></span>
              </span>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Error Alert */}
      {errorMsg && (
        <motion.div 
          initial={{ y: -10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="px-4 py-2 bg-red-50 border-t border-red-200"
        >
          <p className="text-red-600 text-xs font-medium">⚠️ {errorMsg}</p>
        </motion.div>
      )}

      {/* Input Area */}
      <div className="bg-gray-100 p-3 shrink-0 border-t border-gray-200 shadow-[0_-4px_10px_rgba(0,0,0,0.05)]">
        {/* Suggestions Carousel */}
        <div className="flex overflow-x-auto gap-2 mb-3 pb-1 no-scrollbar scroll-smooth">
          {suggestions.map((s, i) => (
            <motion.button 
              key={i} 
              whileTap={{ scale: 0.95 }}
              onClick={() => handleSend(s)} 
              disabled={loading}
              className="whitespace-nowrap bg-white border border-purple-100 text-purple-700 px-3 py-2 rounded-full text-xs font-semibold shadow-sm hover:border-purple-300 hover:bg-purple-50 transition-all active:bg-purple-100 flex-shrink-0 disabled:opacity-50"
            >
              {s}
            </motion.button>
          ))}
        </div>
        
        {/* Input Box */}
        <div className="flex items-end gap-2 bg-white rounded-2xl shadow-inner border border-gray-300 p-2 pl-4 focus-within:border-purple-400 focus-within:ring-1 focus-within:ring-purple-100 transition-all">
          <textarea 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Apna sawaal likhein ya bolein..."
            className="flex-1 bg-transparent border-none focus:ring-0 resize-none py-2 max-h-32 text-gray-800 text-sm placeholder:text-gray-400"
            rows={1}
            disabled={loading}
            onKeyDown={(e) => { 
              if(e.key === 'Enter' && !e.shiftKey) { 
                e.preventDefault(); 
                handleSend(input); 
              } 
            }}
          />
          <div className="flex gap-1 pb-1 pr-1">
            <motion.button 
              onClick={handleVoiceInput}
              whileTap={{ scale: 0.9 }}
              disabled={loading}
              className={`p-2.5 rounded-xl transition-all ${isListening ? 'bg-red-500 text-white animate-pulse shadow-lg' : 'text-gray-400 hover:bg-gray-100 hover:text-purple-600 disabled:opacity-50'}`}
              title="Voice Input"
            >
              <span className="text-xl">🎤</span>
            </motion.button>
            <motion.button 
              onClick={() => handleSend(input)}
              whileTap={{ scale: 0.9 }}
              disabled={!input.trim() || loading}
              className={`p-2.5 rounded-xl shadow-lg transition-all transform active:scale-95 ${!input.trim() || loading ? 'bg-gray-200 text-gray-400 cursor-not-allowed' : 'bg-purple-600 text-white hover:bg-purple-700 hover:shadow-purple-200'}`}
            >
              <span className="text-xl">📤</span>
            </motion.button>
          </div>
        </div>
        <p className="text-[10px] text-center text-gray-400 mt-2 font-medium tracking-tight">
          AI can make mistakes. Verify farming decisions with experts.
        </p>
      </div>
    </div>
  );
}
