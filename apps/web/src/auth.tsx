import { API_BASE_URL, ROLE_HOME_ROUTE } from "@rtls/config";
import type { AuthTokenResponse, AuthenticatedUser, UserRole } from "@rtls/contracts";
import {
  createContext,
  useContext,
  useEffect,
  useState,
  type PropsWithChildren
} from "react";

const STORAGE_KEY = "rtls-auth-session";

type SessionState = {
  accessToken: string;
  refreshToken: string;
};

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  apiBaseUrl: string;
  status: AuthStatus;
  user: AuthenticatedUser | null;
  login: (email: string, password: string) => Promise<UserRole>;
  logout: () => Promise<void>;
  fetchWithAuth: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function getApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || API_BASE_URL;
}

function readStoredSession(): SessionState | null {
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as SessionState;
  } catch {
    window.localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

function writeStoredSession(session: SessionState | null) {
  if (session) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
    return;
  }

  window.localStorage.removeItem(STORAGE_KEY);
}

async function requestRefresh(apiBaseUrl: string, currentSession: SessionState) {
  const response = await fetch(`${apiBaseUrl}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: currentSession.refreshToken })
  });

  if (!response.ok) {
    throw new Error("Unable to refresh session");
  }

  return (await response.json()) as AuthTokenResponse;
}

async function requestCurrentUser(apiBaseUrl: string, currentSession: SessionState) {
  const response = await fetch(`${apiBaseUrl}/api/me`, {
    headers: { Authorization: `Bearer ${currentSession.accessToken}` }
  });

  if (response.status === 401) {
    throw new Error("SESSION_EXPIRED");
  }
  if (!response.ok) {
    throw new Error("Unable to load current user");
  }

  return (await response.json()) as AuthenticatedUser;
}

export function roleHomeRoute(role: UserRole) {
  return ROLE_HOME_ROUTE[role];
}

export function AuthProvider({ children }: PropsWithChildren) {
  const apiBaseUrl = getApiBaseUrl();
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [session, setSession] = useState<SessionState | null>(() => readStoredSession());
  const [user, setUser] = useState<AuthenticatedUser | null>(null);

  const clearSession = () => {
    setSession(null);
    setUser(null);
    setStatus("unauthenticated");
    writeStoredSession(null);
  };

  const persistSession = (nextSession: SessionState) => {
    setSession(nextSession);
    writeStoredSession(nextSession);
  };

  const refreshSession = async (currentSession: SessionState) => {
    const payload = await requestRefresh(apiBaseUrl, currentSession);
    const nextSession = {
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token
    };
    persistSession(nextSession);
    return nextSession;
  };

  const loadCurrentUser = async (currentSession: SessionState) => {
    const currentUser = await requestCurrentUser(apiBaseUrl, currentSession);
    setUser(currentUser);
    setStatus("authenticated");
    return currentUser;
  };

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      if (!session) {
        if (!cancelled) {
          setStatus("unauthenticated");
        }
        return;
      }

      try {
        const currentUser = await requestCurrentUser(apiBaseUrl, session);
        if (!cancelled) {
          setUser(currentUser);
          setStatus("authenticated");
        }
      } catch (error) {
        if ((error as Error).message === "SESSION_EXPIRED") {
          try {
            const payload = await requestRefresh(apiBaseUrl, session);
            const nextSession = {
              accessToken: payload.access_token,
              refreshToken: payload.refresh_token
            };
            if (!cancelled) {
              persistSession(nextSession);
            }
            const currentUser = await requestCurrentUser(apiBaseUrl, nextSession);
            if (!cancelled) {
              setUser(currentUser);
              setStatus("authenticated");
            }
          } catch {
            if (!cancelled) {
              clearSession();
            }
          }
          return;
        }

        if (!cancelled) {
          clearSession();
        }
      }
    }

    void bootstrap();

    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl, session]);

  const login = async (email: string, password: string) => {
    const response = await fetch(`${apiBaseUrl}/api/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      throw new Error("Invalid credentials");
    }

    const payload = (await response.json()) as AuthTokenResponse;
    const nextSession = {
      accessToken: payload.access_token,
      refreshToken: payload.refresh_token
    };
    persistSession(nextSession);
    const currentUser = await loadCurrentUser(nextSession);
    return currentUser.role;
  };

  const logout = async () => {
    if (session?.refreshToken) {
      await fetch(`${apiBaseUrl}/api/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: session.refreshToken })
      }).catch(() => undefined);
    }

    clearSession();
  };

  const fetchWithAuth = async (input: RequestInfo | URL, init?: RequestInit) => {
    if (!session) {
      throw new Error("Authentication required");
    }

    const makeRequest = (accessToken: string) =>
      fetch(resolveApiUrl(input), {
        ...init,
        headers: {
          ...(init?.headers || {}),
          Authorization: `Bearer ${accessToken}`
        }
      });

    let response = await makeRequest(session.accessToken);
    if (response.status !== 401) {
      return response;
    }

    try {
      const nextSession = await refreshSession(session);
      response = await makeRequest(nextSession.accessToken);
      return response;
    } catch {
      clearSession();
      return response;
    }
  };

  const value: AuthContextValue = {
    apiBaseUrl,
    status,
    user,
    login,
    logout,
    fetchWithAuth
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
  const resolveApiUrl = (input: RequestInfo | URL) => {
    if (typeof input === "string" && input.startsWith("/")) {
      return `${apiBaseUrl}${input}`;
    }

    return input;
  };
