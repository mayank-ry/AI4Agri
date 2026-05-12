import React from 'react';
import { Badge } from '@/components/ui/badge';

interface ChatMessageProps {
  text: string;
  sender: 'user' | 'bot';
  intent?: string;
  modelUsed?: string;
  timestamp?: Date;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ 
  text, 
  sender, 
  intent, 
  modelUsed,
  timestamp
}) => {
  const isUser = sender === 'user';
  const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString('hi-IN', { hour: '2-digit', minute: '2-digit' }) : '';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3 items-end gap-2`}>
      {/* Bot Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
          🤖
        </div>
      )}

      {/* Message Bubble */}
      <div
        className={`max-w-xs lg:max-w-md px-4 py-2 rounded-xl shadow-sm ${
          isUser
            ? 'bg-[#dcf8c6] text-gray-800 rounded-br-none'
            : 'bg-white text-gray-800 rounded-bl-none border border-gray-100'
        }`}
      >
        {/* Text */}
        <p className="whitespace-pre-line leading-relaxed text-sm break-words">{text}</p>

        {/* Badges + Timestamp */}
        <div className="mt-1.5 flex flex-wrap gap-1.5 items-center text-xs">
          {/* Intent Badge */}
          {intent && (
            <Badge 
              variant="secondary" 
              className="text-xs bg-blue-100 text-blue-700 border-0"
            >
              💡 {intent}
            </Badge>
          )}

          {/* Fallback Indicator */}
          {modelUsed && modelUsed !== 'gemini' && (
            <Badge 
              variant="outline" 
              className="text-xs bg-yellow-50 text-yellow-700 border-yellow-200"
            >
              ⚠️ {modelUsed === 'flan_t5_fallback' ? 'T5' : modelUsed}
            </Badge>
          )}

          {/* Timestamp */}
          {timeStr && (
            <span className={`text-xs ${isUser ? 'text-gray-500' : 'text-gray-400'}`}>
              {timeStr}
            </span>
          )}
        </div>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
          👨‍🌾
        </div>
      )}
    </div>
  );
};
