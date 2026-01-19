import { useUserStore, type User } from '@/stores/userStore';
import toast from 'react-hot-toast';
import storage from '@/utils/storage';

const API_BASE = '';

interface AuthResponse {
  success: boolean;
  message?: string;
  user?: User;
  token?: string;
}

interface StatusResponse {
  success: boolean;
  authenticated: boolean;
  user?: User;
}

class AuthService {
  private getHeaders(): HeadersInit {
    const token = storage.getAuthToken();
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async login(email: string, password: string): Promise<boolean> {
    const { setUser, setLoading, setError } = useUserStore.getState();

    console.log('🔐 AUTH: login() called with email:', email);

    try {
      setLoading(true);
      setError(null);

      console.log('🔐 AUTH: Sending login request to /auth/login');
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Conversation-ID': storage.ensureConversationId() },
        body: JSON.stringify({ email, password }),
        credentials: 'include',
      });

      console.log('🔐 AUTH: Login response status:', response.status);
      const data: AuthResponse = await response.json();
      console.log('🔐 AUTH: Login response data:', data);

      if (data.success && data.user && data.token) {
        console.log('🔐 AUTH: Login successful! Setting token and user');
        storage.setAuthToken(data.token);
        setUser(data.user);
        console.log('🔐 AUTH: User set in store:', data.user);
        console.log('🔐 AUTH: Store state after login:', useUserStore.getState());
        toast.success(`Welcome back, ${data.user.username}!`);
        return true;
      } else {
        console.log('🔐 AUTH: Login failed:', data.message);
        const errorMsg = data.message || 'Login failed';
        setError(errorMsg);
        toast.error(errorMsg);
        return false;
      }
    } catch (error) {
      console.error('🔐 AUTH: Login error:', error);
      const errorMsg = 'Network error. Please try again.';
      setError(errorMsg);
      toast.error(errorMsg);
      return false;
    } finally {
      setLoading(false);
    }
  }

  async signup(email: string, username: string, password: string): Promise<boolean> {
    const { setUser, setLoading, setError } = useUserStore.getState();

    console.log('🔐 AUTH: signup() called with email:', email, 'username:', username);

    try {
      setLoading(true);
      setError(null);

      console.log('🔐 AUTH: Sending signup request to /auth/signup');
      const response = await fetch(`${API_BASE}/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Conversation-ID': storage.ensureConversationId() },
        body: JSON.stringify({ email, username, password }),
        credentials: 'include',
      });

      console.log('🔐 AUTH: Signup response status:', response.status);
      const data: AuthResponse = await response.json();
      console.log('🔐 AUTH: Signup response data:', data);

      if (data.success && data.user && data.token) {
        console.log('🔐 AUTH: Signup successful! Setting token and user');
        storage.setAuthToken(data.token);
        setUser(data.user);
        console.log('🔐 AUTH: User set in store:', data.user);
        console.log('🔐 AUTH: Store state after signup:', useUserStore.getState());
        toast.success(`Account created! Welcome, ${data.user.username}!`);
        return true;
      } else {
        console.log('🔐 AUTH: Signup failed:', data.message);
        const errorMsg = data.message || 'Signup failed';
        setError(errorMsg);
        toast.error(errorMsg);
        return false;
      }
    } catch (error) {
      console.error('🔐 AUTH: Signup error:', error);
      const errorMsg = 'Network error. Please try again.';
      setError(errorMsg);
      toast.error(errorMsg);
      return false;
    } finally {
      setLoading(false);
    }
  }

  async logout(): Promise<void> {
    const { logout: clearUserState, setLoading } = useUserStore.getState();

    try {
      setLoading(true);

      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { ...this.getHeaders(), 'X-Conversation-ID': storage.ensureConversationId() },
        credentials: 'include',
      });

      clearUserState();
      storage.clearAuthToken();
      toast.success('Signed out successfully');
    } catch (error) {
      // Even if the API call fails, clear local state
      clearUserState();
      storage.clearAuthToken();
      toast.success('Signed out');
    } finally {
      setLoading(false);
    }
  }

  async checkAuth(): Promise<boolean> {
    const { setUser, setLoading } = useUserStore.getState();

    console.log('🔐 AUTH: checkAuth() called');
    const token = storage.getAuthToken();
    console.log('🔐 AUTH: Token in sessionStorage:', token ? 'EXISTS' : 'NONE');

    try {
      setLoading(true);

      console.log('🔐 AUTH: Checking auth status at /auth/status');
      const response = await fetch(`${API_BASE}/auth/status`, {
        method: 'GET',
        headers: { ...this.getHeaders(), 'X-Conversation-ID': storage.ensureConversationId() },
        credentials: 'include',
      });

      console.log('🔐 AUTH: Status response status:', response.status);
      const data: StatusResponse = await response.json();
      console.log('🔐 AUTH: Status response data:', data);

      if (data.success && data.authenticated && data.user) {
        console.log('🔐 AUTH: User authenticated! Setting user:', data.user);
        setUser(data.user);
        console.log('🔐 AUTH: Store state after checkAuth:', useUserStore.getState());
        return true;
      } else {
        console.log('🔐 AUTH: Not authenticated, clearing user');
        setUser(null);
        storage.clearAuthToken();
        return false;
      }
    } catch (error) {
      console.error('🔐 AUTH: checkAuth error:', error);
      setUser(null);
      storage.clearAuthToken();
      return false;
    } finally {
      setLoading(false);
    }
  }
}

export const authService = new AuthService();
