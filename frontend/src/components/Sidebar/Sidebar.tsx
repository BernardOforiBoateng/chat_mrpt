import React, { useState } from 'react';
import { useChatStore } from '@/stores/chatStore';
import api from '@/services/api';
import toast from 'react-hot-toast';
import ProfileSection from '@/components/Profile/ProfileSection';
import LoginModal from '@/components/Auth/LoginModal';
import SignupModal from '@/components/Auth/SignupModal';

const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(true);  // Start collapsed
  const [activeSection, setActiveSection] = useState<'history' | 'samples'>('history');
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  
  const session = useChatStore((state) => state.session);
  const setUploadedFiles = useChatStore((state) => state.setUploadedFiles);
  
  if (isCollapsed) {
    return (
      <div className="w-16 bg-gray-50 border-r border-gray-200 flex flex-col items-center py-4 transition-all duration-300 ease-in-out">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 hover:bg-gray-200 rounded-lg transition-all duration-200 group"
          title="Expand sidebar"
        >
          <svg className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
        
        {/* Quick Actions in Collapsed State */}
        <div className="mt-8 space-y-4">
          <button
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            title="Recent Files"
            onClick={() => {
              setIsCollapsed(false);
              setActiveSection('history');
            }}
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
          
          <button
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
            title="Sample Data"
            onClick={() => {
              setIsCollapsed(false);
              setActiveSection('samples');
            }}
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <>
      {/* Auth Modals */}
      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
        onSwitchToSignup={() => {
          setShowLoginModal(false);
          setShowSignupModal(true);
        }}
      />
      <SignupModal
        isOpen={showSignupModal}
        onClose={() => setShowSignupModal(false)}
        onSwitchToLogin={() => {
          setShowSignupModal(false);
          setShowLoginModal(true);
        }}
      />

      <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col transition-all duration-300 ease-in-out">
        {/* Profile Section */}
        <ProfileSection
          onLoginClick={() => setShowLoginModal(true)}
          onSignupClick={() => setShowSignupModal(true)}
        />

        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-semibold text-gray-900">Data Management</h3>
          <button
            onClick={() => setIsCollapsed(true)}
            className="p-1 hover:bg-gray-200 rounded-lg transition-all duration-200 group"
            title="Collapse sidebar"
          >
            <svg className="w-5 h-5 group-hover:-translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        </div>
        
        {/* Section Tabs */}
        <div className="flex space-x-1 p-1 bg-gray-100 rounded-lg">
          <button
            onClick={() => setActiveSection('history')}
            className={`flex-1 px-3 py-1.5 text-sm font-medium rounded transition-all duration-200 ${
              activeSection === 'history'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            History
          </button>
          <button
            onClick={() => setActiveSection('samples')}
            className={`flex-1 px-3 py-1.5 text-sm font-medium rounded transition-all duration-200 ${
              activeSection === 'samples'
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Samples
          </button>
        </div>
      </div>
      
      {/* Content Sections */}
      <div className="p-4 flex-1 overflow-y-auto">
        {/* History Section */}
        {activeSection === 'history' && (
          <div className="animate-fadeIn">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Recent Files</h4>
            {session.hasUploadedFiles && session.uploadedFiles ? (
            <div className="space-y-2">
              {session.uploadedFiles.csv && (
                <div className="flex items-center p-2 bg-white rounded border border-gray-200">
                  <svg className="w-4 h-4 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700 truncate">{session.uploadedFiles.csv}</span>
                </div>
              )}
              {session.uploadedFiles.shapefile && (
                <div className="flex items-center p-2 bg-white rounded border border-gray-200">
                  <svg className="w-4 h-4 text-green-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <span className="text-sm text-gray-700 truncate">{session.uploadedFiles.shapefile}</span>
                </div>
              )}
              </div>
            ) : (
              <p className="text-sm text-gray-500 text-center py-8">No files uploaded yet</p>
            )}
          </div>
        )}
        
        {/* Samples Section */}
        {activeSection === 'samples' && (
          <div className="animate-fadeIn">
            <h4 className="text-sm font-medium text-gray-700 mb-3">Available Sample Datasets</h4>
            <div className="space-y-2">
              <button
                onClick={async () => {
                  try {
                    await api.upload.loadSampleData('kano', session.sessionId);
                    toast.success('Kano sample data loaded');
                    setUploadedFiles('kano_sample.csv', 'kano_boundaries.zip');
                  } catch (error) {
                    toast.error('Failed to load sample data');
                  }
                }}
                className="w-full p-3 bg-white border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-300 transition-all duration-200 group text-left"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900 group-hover:text-blue-600">Kano State</p>
                    <p className="text-xs text-gray-500">Ward-level malaria risk data</p>
                  </div>
                  <svg className="w-5 h-5 text-gray-400 group-hover:text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </button>
              
              <button
                disabled
                className="w-full p-3 bg-gray-100 border border-gray-200 rounded-lg opacity-50 cursor-not-allowed text-left"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">Lagos State</p>
                    <p className="text-xs text-gray-400">Coming soon</p>
                  </div>
                  <svg className="w-5 h-5 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
              </button>
            </div>
          </div>
        )}
      </div>
      </div>
    </>
  );
};

export default Sidebar;