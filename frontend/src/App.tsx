import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useEffect } from 'react';
import toast from 'react-hot-toast';
import { ThemeProvider } from './contexts/ThemeContext';
import MainInterface from './components/MainInterface';
import LandingPage from './components/Auth/LandingPage';
import { authService } from './services/auth';
import { useUserStore } from './stores/userStore';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: 1,
    },
  },
});

function App() {
  const { isAuthenticated, isLoading, user } = useUserStore();

  // TEMPORARY: Force authentication bypass for development
  const forceAuthenticated = true;

  console.log('🔵 APP: Render - isAuthenticated:', isAuthenticated, 'isLoading:', isLoading, 'user:', user, 'FORCED:', forceAuthenticated);

  // Check authentication status on app load
  useEffect(() => {
    console.log('🔵 APP: useEffect triggered');
    // Check for OAuth callback parameters in URL
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const username = urlParams.get('user');

    if (token && username) {
      console.log('🔵 APP: OAuth callback detected - token and username in URL');
      // Store the token from OAuth callback
      localStorage.setItem('auth_token', token);

      // Clean up URL
      window.history.replaceState({}, document.title, window.location.pathname);

      // Check auth status to load user data with a small delay to ensure token is stored
      setTimeout(() => {
        console.log('🔵 APP: Calling checkAuth for OAuth callback');
        authService.checkAuth().then((success) => {
          console.log('🔵 APP: OAuth checkAuth result:', success);
          if (success) {
            toast.success(`Welcome back, ${username}`);
          }
        });
      }, 100);
    } else {
      console.log('🔵 APP: No OAuth callback, checking persisted state');
      // Only check auth if we don't already have a user from persisted state
      // AND we have a token in localStorage
      const hasToken = !!localStorage.getItem('auth_token');
      const hasPersistedUser = !!user;

      console.log('🔵 APP: hasToken:', hasToken, 'hasPersistedUser:', hasPersistedUser);

      if (hasToken && !hasPersistedUser) {
        console.log('🔵 APP: Has token but no persisted user - validating');
        // We have a token but no user - validate it
        authService.checkAuth();
      } else if (!hasToken && hasPersistedUser) {
        console.log('🔵 APP: Has persisted user but no token - clearing stale state');
        // We have a persisted user but no token - clear the stale state
        useUserStore.getState().logout();
      } else if (hasToken && hasPersistedUser) {
        console.log('🔵 APP: Has both token and persisted user - trusting persisted state');
      } else {
        console.log('🔵 APP: No token and no persisted user - already logged out');
      }
    }
  }, [user]);

  console.log('🔵 APP: Rendering UI - isLoading:', isLoading, 'isAuthenticated:', isAuthenticated);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        {/* Show loading spinner during initial auth check */}
        {isLoading && !forceAuthenticated ? (
          (() => {
            console.log('🔵 APP: Showing loading spinner');
            return (
              <div className="min-h-screen flex items-center justify-center bg-white">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
              </div>
            );
          })()
        ) : (isAuthenticated || forceAuthenticated) ? (
          (() => {
            console.log('🔵 APP: Showing main interface (authenticated or forced)');
            return <MainInterface />;
          })()
        ) : (
          (() => {
            console.log('🔵 APP: Showing landing page (not authenticated)');
            return <LandingPage />;
          })()
        )}
      
      {/* Toast notifications */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            style: {
              background: '#10b981',
            },
          },
          error: {
            style: {
              background: '#ef4444',
            },
          },
        }}
      />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;