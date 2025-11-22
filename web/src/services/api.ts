import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
    (config) => {
        const storedAuth = localStorage.getItem('mavunosure_auth')
        if (storedAuth) {
            const auth = JSON.parse(storedAuth)
            config.headers.Authorization = `Bearer ${auth.token}`
        }
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// Response interceptor to handle auth errors
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('mavunosure_auth')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)
