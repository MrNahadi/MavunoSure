import React, { createContext, useContext, useEffect, useState } from 'react'
import { useAuthStore } from '@/store/authStore'
import { StoredAuth } from '@/types/auth'

interface AuthContextType {
    isAuthenticated: boolean
    isLoading: boolean
    login: (token: string, phoneNumber: string, expiresIn: number) => void
    logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const AUTH_STORAGE_KEY = 'mavunosure_auth'

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { isAuthenticated, setAuth, clearAuth } = useAuthStore()
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        // Check for stored auth on mount
        const storedAuthStr = localStorage.getItem(AUTH_STORAGE_KEY)
        if (storedAuthStr) {
            try {
                const storedAuth: StoredAuth = JSON.parse(storedAuthStr)
                const now = Date.now()

                // Check if token is still valid
                if (storedAuth.expiresAt > now) {
                    setAuth(storedAuth.token, storedAuth.phoneNumber)
                } else {
                    // Token expired, clear storage
                    localStorage.removeItem(AUTH_STORAGE_KEY)
                }
            } catch (error) {
                console.error('Failed to parse stored auth:', error)
                localStorage.removeItem(AUTH_STORAGE_KEY)
            }
        }
        setIsLoading(false)
    }, [setAuth])

    const login = (token: string, phoneNumber: string, expiresIn: number) => {
        const expiresAt = Date.now() + expiresIn * 1000
        const authData: StoredAuth = {
            token,
            phoneNumber,
            expiresAt,
        }
        localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(authData))
        setAuth(token, phoneNumber)
    }

    const logout = () => {
        localStorage.removeItem(AUTH_STORAGE_KEY)
        clearAuth()
    }

    return (
        <AuthContext.Provider value={{ isAuthenticated, isLoading, login, logout }}>
            {children}
        </AuthContext.Provider>
    )
}

export const useAuth = () => {
    const context = useContext(AuthContext)
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider')
    }
    return context
}
