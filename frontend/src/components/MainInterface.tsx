import React, { useState, useEffect } from 'react';
import { useChatStore } from '@/stores/chatStore';
import ChatContainer from './Chat/ChatContainer';
import Sidebar from './Sidebar/Sidebar';
import Toolbar from './Toolbar/Toolbar';
import SettingsModal from './Modal/SettingsModal';
// import QuickStartModal from './Modal/QuickStartModal';
import TourOverlay from './Modal/TourOverlay';
import PrivacyModal from './Modal/PrivacyModal';

const MainInterface: React.FC = () => {
  const [showSettings, setShowSettings] = useState(false);
  // const [showQuickStart, setShowQuickStart] = useState(false);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [showTour, setShowTour] = useState(false);
  
  // Check for first-time user on mount
  useEffect(() => {
    const hasAcceptedPrivacy = localStorage.getItem('chatmrpt_privacy_accepted');
    if (!hasAcceptedPrivacy) {
      setShowPrivacyModal(true);
    }
    // Only start the tour when explicitly requested
    try {
      const start = localStorage.getItem('chatmrpt_start_tour') === '1';
      if (start) {
        setShowTour(true);
        localStorage.removeItem('chatmrpt_start_tour');
      }
    } catch {}
  }, []);
  
  const handlePrivacyAccept = () => {
    localStorage.setItem('chatmrpt_privacy_accepted', 'true');
    localStorage.setItem('chatmrpt_privacy_accepted_date', new Date().toISOString());
    setShowPrivacyModal(false);
  };
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Toolbar with Clear, Export, Settings */}
      <Toolbar onOpenSettings={() => setShowSettings(true)} />
      
      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar />
        
        {/* Chat Container */}
        <main className="flex-1 flex flex-col">
          <ChatContainer />
        </main>
      </div>
      
      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
      />
      {/* Quick Start Modal removed as per request */}
      {/* Guided Tour */}
      <TourOverlay isOpen={showTour} onClose={() => setShowTour(false)} onCompleted={() => setShowTour(false)} />
      
      {/* Privacy Modal - First Run */}
      <PrivacyModal
        isOpen={showPrivacyModal}
        onAccept={handlePrivacyAccept}
      />
    </div>
  );
};

export default MainInterface;
