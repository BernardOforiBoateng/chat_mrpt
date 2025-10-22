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
    // Not authenticated - ChatGPT style minimal button
    return (
      <div className="p-2 border-t border-gray-200">
        <button
          onClick={onLoginClick}
          className="w-full px-3 py-2 text-sm text-left text-gray-700 hover:bg-gray-100 rounded-lg transition-colors flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
          <span>Sign in</span>
        </button>
      </div>
    );
  }

  // Authenticated - ChatGPT style: just avatar, click for dropdown
  return (
    <div className="p-2 border-t border-gray-200 relative" ref={menuRef}>
      <button
        onClick={() => setIsMenuOpen(!isMenuOpen)}
        className="w-full p-2 rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-center"
        title={user.email}
      >
        <UserAvatar username={user.username} size="md" />
      </button>

      {/* Dropdown Menu - ChatGPT style popup */}
      {isMenuOpen && (
        <div className="absolute left-2 right-2 bottom-full mb-2 bg-white border border-gray-200 rounded-lg shadow-xl z-50 overflow-hidden py-1">
          {/* User info header */}
          <div className="px-3 py-2 border-b border-gray-100">
            <div className="text-sm font-medium text-gray-900">{user.email}</div>
          </div>

          {/* Sign out button */}
          <button
            onClick={handleLogout}
            className="w-full px-3 py-2.5 text-left hover:bg-gray-50 transition-colors flex items-center space-x-2 text-sm text-gray-700"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>Log out</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default ProfileSection;
