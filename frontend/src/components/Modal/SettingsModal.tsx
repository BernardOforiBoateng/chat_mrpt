import React, { useState } from 'react';
import Modal from './Modal';
import { useChatStore } from '@/stores/chatStore';
import { useTheme } from '@/contexts/ThemeContext';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [activeTab, setActiveTab] = useState<'general' | 'appearance' | 'data'>('general');
  const session = useChatStore((state) => state.session);
  const { theme, setTheme } = useTheme();
  
  // Local settings state
  const [settings, setSettings] = useState({
    streamResponses: true,
    showTimestamps: true,
    enableMarkdown: true,
    fontSize: 'medium' as 'small' | 'medium' | 'large',
    compactMode: false,
    autoSave: true,
    saveInterval: 5,
  });
  
  const handleSave = () => {
    // Save settings to localStorage or backend
    localStorage.setItem('chatmrpt-settings', JSON.stringify(settings));
    onClose();
  };
  
  const tabs = [
    { id: 'general', label: 'General', icon: '⚙️' },
    { id: 'appearance', label: 'Appearance', icon: '🎨' },
    { id: 'data', label: 'Data & Privacy', icon: '🔒' },
  ];
  
  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Settings"
      size="large"
    >
      <div className="flex h-[500px]">
        {/* Sidebar Navigation */}
        <div className="w-48 border-r border-gray-200 pr-4">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`
                  w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg
                  ${activeTab === tab.id
                    ? 'bg-blue-50 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }
                `}
              >
                <span className="mr-3">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
        
        {/* Content Area */}
        <div className="flex-1 pl-6 overflow-y-auto">
          {activeTab === 'general' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">Response Settings</h3>
                <div className="space-y-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.streamResponses}
                      onChange={(e) => setSettings({ ...settings, streamResponses: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-3 text-sm text-gray-700">
                      Stream responses in real-time
                    </span>
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.showTimestamps}
                      onChange={(e) => setSettings({ ...settings, showTimestamps: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-3 text-sm text-gray-700">
                      Show message timestamps
                    </span>
                  </label>
                  
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={settings.enableMarkdown}
                      onChange={(e) => setSettings({ ...settings, enableMarkdown: e.target.checked })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-3 text-sm text-gray-700">
                      Enable markdown formatting
                    </span>
                  </label>
                </div>
              </div>
            </div>
          )}
          
          {activeTab === 'appearance' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">Theme</h3>
                <div className="space-y-3">
                  {(['light', 'dark'] as const).map((themeOption) => (
                    <label key={themeOption} className="flex items-center">
                      <input
                        type="radio"
                        name="theme"
                        value={themeOption}
                        checked={theme === themeOption}
                        onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <span className="ml-3 text-sm text-gray-700">
                        <span className="capitalize font-medium">{themeOption}</span>
                      </span>
                    </label>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">Font Size</h3>
                <select
                  value={settings.fontSize}
                  onChange={(e) => setSettings({ ...settings, fontSize: e.target.value as any })}
                  className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                >
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                </select>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">Display</h3>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.compactMode}
                    onChange={(e) => setSettings({ ...settings, compactMode: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-3 text-sm text-gray-700">
                    Compact mode (reduced spacing)
                  </span>
                </label>
              </div>
            </div>
          )}
          
          {activeTab === 'data' && (
            <div className="space-y-6">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">Session Information</h3>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Session ID:</span>
                    <span className="font-mono text-xs">{session.sessionId}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Started:</span>
                    <span>{new Date(session.startTime).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Messages:</span>
                    <span>{session.messageCount}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">Auto-Save</h3>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={settings.autoSave}
                    onChange={(e) => setSettings({ ...settings, autoSave: e.target.checked })}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-3 text-sm text-gray-700">
                    Auto-save chat history
                  </span>
                </label>
                
                {settings.autoSave && (
                  <div className="mt-3">
                    <label className="block text-sm text-gray-700">
                      Save interval (minutes)
                      <input
                        type="number"
                        min="1"
                        max="60"
                        value={settings.saveInterval}
                        onChange={(e) => setSettings({ ...settings, saveInterval: parseInt(e.target.value) })}
                        className="mt-1 block w-24 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      />
                    </label>
                  </div>
                )}
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-4">Privacy</h3>
                <button className="px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 text-sm font-medium">
                  Clear All Local Data
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Footer */}
      <div className="mt-6 flex justify-end space-x-3 pt-4 border-t border-gray-200">
        <button
          onClick={onClose}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Cancel
        </button>
        <button
          onClick={handleSave}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Save Changes
        </button>
      </div>
    </Modal>
  );
};

export default SettingsModal;
