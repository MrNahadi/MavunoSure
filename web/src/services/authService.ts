import { apiClient } from './api'
import {
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
} from '@/types/auth'

export const authService = {
    sendOTP: async (data: SendOTPRequest): Promise<SendOTPResponse> => {
        const response = await apiClient.post<SendOTPResponse>('/auth/send-otp', data)
        return response.data
    },

    verifyOTP: async (data: VerifyOTPRequest): Promise<VerifyOTPResponse> => {
        const response = await apiClient.post<VerifyOTPResponse>('/auth/verify-otp', data)
        return response.data
    },

    refreshToken: async (): Promise<VerifyOTPResponse> => {
        const response = await apiClient.post<VerifyOTPResponse>('/auth/refresh-token')
        return response.data
    },
}
