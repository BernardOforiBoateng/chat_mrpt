import React, { useRef, useEffect, useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import { useAnalysisStore } from '@/stores/analysisStore';
import UploadModal from '../Modal/UploadModal';

interface InputAreaProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  placeholder?: string;
}

const InputArea: React.FC<InputAreaProps> = ({
  value,
  onChange,
  onSend,
  isLoading,
  placeholder = "Type your message...",
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const messages = useChatStore((state) => state.messages);
  const hasUploadedFiles = useChatStore((state) => state.session.hasUploadedFiles);
  const analysisResults = useAnalysisStore((state) => state.analysisResults);
  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [value]);
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };
  
  // Generate context-aware suggestions
  const getSuggestions = () => {
    // No messages yet
    if (messages.length === 0) {
      return [
        "What is ChatMRPT?",
        "Help me analyze malaria risk",
        "Load sample data",
        "How do I upload my data?"
      ];
    }
    
    // Has uploaded files but no analysis
    if (hasUploadedFiles && analysisResults.length === 0) {
      return [
        "Run malaria risk analysis",
        "Show me PCA analysis",
        "Generate composite scores",
        "What variables are available?"
      ];
    }
    
    // Has analysis results
    if (analysisResults.length > 0) {
      return [
        "Show top 10 high-risk wards",
        "Create visualization map",
        "Export analysis results",
        "Compare PCA vs Composite"
      ];
    }
    
    // Default suggestions
    return [
      "What can you help me with?",
      "Upload new data",
      "Explain the analysis methods",
      "Show recent results"
    ];
  };
  
  const suggestions = getSuggestions();
  
  const handleSuggestionClick = (suggestion: string) => {
    onChange(suggestion);
    setShowSuggestions(false);
    textareaRef.current?.focus();
  };
  
  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Suggestion Buttons - COMMENTED OUT */}
      {/* {showSuggestions && suggestions.length > 0 && value.length === 0 && (
        <div className="px-4 pt-3 pb-2 animate-fadeIn">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-gray-500 font-medium">Suggestions</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => handleSuggestionClick(suggestion)}
                className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-all duration-200 hover:scale-105 animate-slideIn"
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )} */}
      
      <div className="p-4">
        <div className="flex items-end space-x-3">
        {/* Input Field */}
        <div className="flex-1" data-tour-id="chat-input" data-edu-tip-chat>
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
            style={{ maxHeight: '200px' }}
          />
        </div>
        
        {/* Action Buttons */}
        <div className="flex space-x-2">
          {/* Upload Button */}
          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              console.log('Upload button clicked, opening modal...');
              setShowUploadModal(true);
            }}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:text-gray-700 disabled:opacity-50 transition-colors"
            data-tour-id="upload-button"
            data-edu-tip-upload
            title="Upload files"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
              />
            </svg>
          </button>
          
          {/* Send Button */}
          <button
            onClick={onSend}
            disabled={isLoading || !value.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            data-tour-id="send-button"
          >
            {isLoading ? (
              <div className="flex items-center">
                <svg className="animate-spin h-4 w-4 mr-2" viewBox="0 0 24 24">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                    fill="none"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
                Sending...
              </div>
            ) : (
              <div className="flex items-center">
                <span>Send</span>
                <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </div>
            )}
          </button>
        </div>
        </div>
        
        {/* Helper Text */}
        <div className="mt-2 text-xs text-gray-500">Press Enter to send, Shift+Enter for new line</div>
      </div>
      
      {/* Upload Modal */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
      />
    </div>
  );
};

export default InputArea;
