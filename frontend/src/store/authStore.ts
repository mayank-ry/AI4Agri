import { create } from 'zustand';

type AuthUser = {
  id?: string;
  email?: string;
  [key: string]: unknown;
};

interface AuthState {
  isAuthenticated: boolean;
  user: AuthUser | null;
  token: string | null;
  setAuth: (user: AuthUser, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  token: null,
  setAuth: (user, token) => set({ isAuthenticated: true, user, token }),
  logout: () => set({ isAuthenticated: false, user: null, token: null }),
}));
