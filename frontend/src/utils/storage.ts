const AUTH_TOKEN_KEY = 'auth_token';
const SESSION_ID_KEY = 'session_id';
const CONVERSATION_ID_KEY = 'conversation_id';

type StorageLike = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>;

const getSessionStorage = (): StorageLike | null => {
  if (typeof window === 'undefined') return null;
  try {
    return window.sessionStorage;
  } catch (err) {
    console.warn('Session storage unavailable', err);
    return null;
  }
};

const getLocalStorage = (): StorageLike | null => {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage;
  } catch (err) {
    console.warn('Local storage unavailable', err);
    return null;
  }
};

export const storage = {
  setAuthToken(token: string) {
    const sessionStore = getSessionStorage();
    sessionStore?.setItem(AUTH_TOKEN_KEY, token);

    // Remove any legacy value that might still live in localStorage
    getLocalStorage()?.removeItem(AUTH_TOKEN_KEY);
  },

  getAuthToken(): string | null {
    const sessionStore = getSessionStorage();
    const existing = sessionStore?.getItem(AUTH_TOKEN_KEY);
    if (existing) {
      return existing;
    }

    // Migrate legacy token from localStorage if present
    const localStore = getLocalStorage();
    const legacy = localStore?.getItem(AUTH_TOKEN_KEY) ?? null;
    if (legacy && sessionStore) {
      sessionStore.setItem(AUTH_TOKEN_KEY, legacy);
      localStore?.removeItem(AUTH_TOKEN_KEY);
    }

    return legacy;
  },

  clearAuthToken() {
    getSessionStorage()?.removeItem(AUTH_TOKEN_KEY);
    getLocalStorage()?.removeItem(AUTH_TOKEN_KEY);
  },

  setSessionId(sessionId: string) {
    const sessionStore = getSessionStorage();
    sessionStore?.setItem(SESSION_ID_KEY, sessionId);
  },

  getSessionId(): string | null {
    const sessionStore = getSessionStorage();
    const existing = sessionStore?.getItem(SESSION_ID_KEY);
    if (existing) {
      return existing;
    }

    // Clear any legacy session id in localStorage to prevent reuse
    const localStore = getLocalStorage();
    const legacy = localStore?.getItem(SESSION_ID_KEY) ?? null;
    if (legacy) {
      localStore?.removeItem(SESSION_ID_KEY);
    }

    return legacy;
  },

  clearSessionId() {
    getSessionStorage()?.removeItem(SESSION_ID_KEY);
    getLocalStorage()?.removeItem(SESSION_ID_KEY);
  },

  setConversationId(conversationId: string) {
    const sessionStore = getSessionStorage();
    sessionStore?.setItem(CONVERSATION_ID_KEY, conversationId);
  },

  getConversationId(): string | null {
    const sessionStore = getSessionStorage();
    return sessionStore?.getItem(CONVERSATION_ID_KEY) ?? null;
  },

  clearConversationId() {
    getSessionStorage()?.removeItem(CONVERSATION_ID_KEY);
  },

  ensureConversationId(): string {
    if (typeof window === 'undefined') {
      return 'default';
    }

    const sessionStore = getSessionStorage();
    let conversationId = sessionStore?.getItem(CONVERSATION_ID_KEY) ?? null;

    if (!conversationId && typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      conversationId = crypto.randomUUID();
      sessionStore?.setItem(CONVERSATION_ID_KEY, conversationId);
    }

    if (!conversationId) {
      conversationId = `conv_${Date.now()}`;
      sessionStore?.setItem(CONVERSATION_ID_KEY, conversationId);
    }

    return conversationId;
  },
};

export default storage;
