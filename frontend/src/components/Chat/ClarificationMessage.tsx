import React from 'react';
import { useChatStore } from '@/stores/chatStore';
import useMessageStreaming from '@/hooks/useMessageStreaming';
import type { ClarificationMessage as ClarificationMessageType } from '@/types';

interface ClarificationMessageProps {
  message: ClarificationMessageType;
}

const ClarificationMessage: React.FC<ClarificationMessageProps> = ({ message }) => {
  const { sendMessage } = useMessageStreaming();
  const setLoading = useChatStore((state) => state.setLoading);

  const handleOptionClick = async (option: ClarificationMessageType['options'][0]) => {
    // Send the user's choice as a message
    // The backend will recognize this as a clarification response
    const response = option.id === 'analyze_data' || option.id === 'explain_results' 
      ? '1' // Tools option
      : '2'; // Arena option
    
    setLoading(true);
    await sendMessage(response);
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="w-5 h-5 text-blue-500 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-3a1 1 0 00-.867.5 1 1 0 11-1.731-1A3 3 0 0113 8a3.001 3.001 0 01-2 2.83V11a1 1 0 11-2 0v-1a1 1 0 011-1 1 1 0 100-2zm0 8a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
          </svg>
        </div>
        
        <div className="ml-3 flex-1">
          <p className="text-sm text-gray-700 mb-3">{message.content}</p>
          
          <div className="space-y-2">
            {message.options.map((option) => (
              <button
                key={option.id}
                onClick={() => handleOptionClick(option)}
                className="w-full text-left px-4 py-3 bg-white border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all duration-200 group"
              >
                <div className="flex items-center">
                  <span className="text-xl mr-3 group-hover:scale-110 transition-transform">
                    {option.icon}
                  </span>
                  <span className="text-sm font-medium text-gray-700 group-hover:text-blue-600">
                    {option.label}
                  </span>
                </div>
              </button>
            ))}
          </div>
          
          {message.originalMessage && (
            <div className="mt-3 pt-3 border-t border-blue-100">
              <p className="text-xs text-gray-500">
                Your question: "{message.originalMessage}"
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClarificationMessage;