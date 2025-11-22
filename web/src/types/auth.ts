export interface AuthToken {
    access_token: string
    token_type: string
    expires_in: number
}

export interface SendOTPRequest {
    phone_number: string
}

export interface SendOTPResponse {
    message: string
    expires_in: number
}

export interface VerifyOTPRequest {
    phone_number: string
    otp: string
}

export interface VerifyOTPResponse {
    access_token: string
    token_type: string
    expires_in: number
}

export interface StoredAuth {
    token: string
    phoneNumber: string
    expiresAt: number
}
