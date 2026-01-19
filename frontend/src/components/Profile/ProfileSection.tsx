import React, { useState, useRef, useEffect } from 'react';
import { useUserStore } from '@/stores/userStore';
import { authService } from '@/services/auth';
import UserAvatar from './UserAvatar';

interface ProfileSectionProps {
  onLoginClick: () => void;
  onSignupClick: () => void;
}

const ProfileSection: React.FC<ProfileSectionProps> = ({ onLoginClick, onSignupClick }) => {
  const { user, isAuthenticated } = useUserStore();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsMenuOpen(false);
      }
    };

    if (isMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isMenuOpen]);

  const handleLogout = async () => {
    setIsMenuOpen(false);
    await authService.logout();
  };

  if (!isAuthenticated || !user) {
    // Not authenticated - show sign in button
    return (
      <div className="p-6 border-b border-gray-100">
        <button
          onClick={onLoginClick}
          className="w-full px-4 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl hover:from-blue-700 hover:to-blue-800 transition-all duration-200 font-medium shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
        >
          Sign In
        </button>
        <button
          onClick={onSignupClick}
          className="w-full mt-3 px-4 py-2.5 bg-white text-gray-700 border border-gray-200 rounded-xl hover:bg-gray-50 hover:border-gray-300 transition-all duration-200 font-medium shadow-sm"
        >
          Sign Up
        </button>
      </div>
    );
  }

  // Authenticated - show profile
  return (
    <div className="p-6 border-b border-gray-100 relative" ref={menuRef}>
      <button
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        className="w-full flex items-center space-x-3 p-3 rounded-xl hover:bg-gray-50 transition-all duration-200 group"
      >
        <UserAvatar username={user.username} size="md" />
        <div className="flex-1 text-left min-w-0">
          <div className="font-semibold text-gray-900 truncate text-sm">{user.username}</div>
          <div className="text-xs text-gray-500 truncate">{user.email}</div>
        </div>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 group-hover:text-gray-600 ${isMenuOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Dropdown Menu */}
      {isMenuOpen && (
        <div className="absolute left-6 right-6 mt-2 bg-white border border-gray-100 rounded-xl shadow-xl z-50 overflow-hidden animate-fadeIn">
          <button
            onClick={() => {
              setIsMenuOpen(false);
              // TODO: Add settings modal
            }}
            className="w-full px-4 py-3 text-left hover:bg-gray-50 transition-all duration-150 flex items-center space-x-3 group"
          >
            <svg className="w-4 h-4 text-gray-400 group-hover:text-blue-600 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <span className="text-sm text-gray-700 group-hover:text-gray-900 font-medium">Settings</span>
          </button>

          <div className="border-t border-gray-100"></div>

          <button
            onClick={handleLogout}
            className="w-full px-4 py-3 text-left hover:bg-red-50 transition-all duration-150 flex items-center space-x-3 text-red-600 group"
          >
            <svg className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span className="text-sm font-semibold">Sign Out</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default ProfileSection;
