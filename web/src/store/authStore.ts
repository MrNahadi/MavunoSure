import { create } from 'zustand'

interface AuthState {
    isAuthenticated: boolean
    token: string | null
    phoneNumber: string | null
    setAuth: (token: string, phoneNumber: string) => void
    clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
    isAuthenticated: false,
    token: null,
    phoneNumber: null,
    setAuth: (token: string, phoneNumber: string) =>
        set({ isAuthenticated: true, token, phoneNumber }),
    clearAuth: () =>
        set({ isAuthenticated: false, token: null, phoneNumber: null }),
}))
