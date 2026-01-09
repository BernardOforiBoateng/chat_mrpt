import React, { useState } from 'react';
import ExportDropdown from '../Export/ExportDropdown';
import { useChatStore } from '@/stores/chatStore';
import { useAnalysisStore } from '@/stores/analysisStore';
import api from '@/services/api';
import toast from 'react-hot-toast';

interface ToolbarProps {
  onOpenSettings?: () => void;
}

const Toolbar: React.FC<ToolbarProps> = ({ onOpenSettings }) => {
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [isClearing, setIsClearing] = useState(false);
  const clearMessages = useChatStore((state) => state.clearMessages);
  const resetSession = useChatStore((state) => state.resetSession);
  const updateSession = useChatStore((state) => state.updateSession);
  const clearAnalysisResults = useAnalysisStore((state) => state.clearAnalysisResults);
  const hasMessages = useChatStore((state) => state.messages.length > 0);

  const handleClearChat = () => {
    setShowClearConfirm(true);
  };

  const confirmClear = async () => {
    setIsClearing(true);

    try {
      // First, clear backend session data
      const response = await api.session.clearSession();

      if (response.data.status === 'success') {
        // Clear frontend state after successful backend clear
        clearMessages();
        clearAnalysisResults();

        // Get the new session ID from backend
        const newSessionId = response.data.new_session_id;

        if (newSessionId) {
          // Don't call resetSession, instead manually reset with the backend's ID
          updateSession({
            sessionId: newSessionId,
            startTime: new Date(),
            messageCount: 0,
            hasUploadedFiles: false,
            uploadedFiles: undefined
          });
        } else {
          // Fallback if backend doesn't provide new ID
          resetSession();
        }

        setShowClearConfirm(false);
        toast.success('Chat cleared successfully');
      } else {
        throw new Error(response.data.message || 'Failed to clear session');
      }
    } catch (error) {
      console.error('Error clearing session:', error);
      toast.error('Failed to clear session. Please try again.');

      // Even if backend fails, we can still clear frontend for better UX
      // But notify user that backend might have issues
      if (window.confirm('Backend clear failed. Clear frontend data anyway?')) {
        clearMessages();
        clearAnalysisResults();
        resetSession();
        setShowClearConfirm(false);
        toast('Frontend cleared, but server data may persist', {
          icon: '⚠️',
          style: { background: '#FEF3C7', color: '#92400E' }
        });
      }
    } finally {
      setIsClearing(false);
    }
  };

  const cancelClear = () => {
    if (!isClearing) {
      setShowClearConfirm(false);
    }
  };
  
  return (
    <>
      <div className="sticky top-0 z-50 flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <h1 className="text-lg font-semibold text-gray-900">ChatMRPT</h1>
          <span className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
            Malaria Risk Analysis
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Clear Chat Button */}
          <button
            onClick={handleClearChat}
            disabled={!hasMessages}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Clear chat history"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            Clear
          </button>
          
          {/* Export Dropdown */}
          <ExportDropdown />
          
          {/* Settings Button */}
          <button
            onClick={onOpenSettings}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            title="Settings"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        </div>
      </div>
      
      {/* Clear Confirmation Dialog */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 overflow-y-auto">
          <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center">
            {/* Backdrop */}
            <div
              className="fixed inset-0 bg-black bg-opacity-50 transition-opacity"
              onClick={cancelClear}
            />
            
            {/* Dialog */}
            <div className="relative inline-block p-6 overflow-hidden text-left align-middle transition-all transform bg-white rounded-lg shadow-xl">
              <div className="flex items-center mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-red-100 rounded-full">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <h3 className="ml-3 text-lg font-medium text-gray-900">
                  Clear Chat History
                </h3>
              </div>
              
              <p className="text-sm text-gray-500">
                Are you sure you want to clear all chat history and analysis results? This action cannot be undone.
              </p>
              
              <div className="flex justify-end mt-6 space-x-3">
                <button
                  onClick={cancelClear}
                  disabled={isClearing}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmClear}
                  disabled={isClearing}
                  className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  {isClearing ? (
                    <>
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Clearing...
                    </>
                  ) : (
                    'Clear Chat'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default Toolbar;
