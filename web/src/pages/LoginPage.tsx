import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { authService } from '@/services/authService'
import { useAuth } from '@/contexts/AuthContext'

export default function LoginPage() {
    const [phoneNumber, setPhoneNumber] = useState('')
    const [otp, setOtp] = useState('')
    const [step, setStep] = useState<'phone' | 'otp'>('phone')
    const [error, setError] = useState('')
    const navigate = useNavigate()
    const { login } = useAuth()

    const sendOTPMutation = useMutation({
        mutationFn: authService.sendOTP,
        onSuccess: () => {
            setStep('otp')
            setError('')
        },
        onError: (error: any) => {
            setError(error.response?.data?.detail || 'Failed to send OTP. Please try again.')
        },
    })

    const verifyOTPMutation = useMutation({
        mutationFn: authService.verifyOTP,
        onSuccess: (data) => {
            login(data.access_token, phoneNumber, data.expires_in)
            navigate('/')
        },
        onError: (error: any) => {
            setError(error.response?.data?.detail || 'Invalid OTP. Please try again.')
        },
    })

    const handleSendOTP = (e: React.FormEvent) => {
        e.preventDefault()
        setError('')

        if (!phoneNumber || phoneNumber.length < 10) {
            setError('Please enter a valid phone number')
            return
        }

        sendOTPMutation.mutate({ phone_number: phoneNumber })
    }

    const handleVerifyOTP = (e: React.FormEvent) => {
        e.preventDefault()
        setError('')

        if (!otp || otp.length !== 6) {
            setError('Please enter a valid 6-digit OTP')
            return
        }

        verifyOTPMutation.mutate({ phone_number: phoneNumber, otp })
    }

    const handleBack = () => {
        setStep('phone')
        setOtp('')
        setError('')
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle>MavunoSure Dashboard</CardTitle>
                    <CardDescription>
                        {step === 'phone'
                            ? 'Enter your phone number to receive an OTP'
                            : 'Enter the OTP sent to your phone'}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {step === 'phone' ? (
                        <form onSubmit={handleSendOTP} className="space-y-4">
                            <div className="space-y-2">
                                <label htmlFor="phone" className="text-sm font-medium">
                                    Phone Number
                                </label>
                                <Input
                                    id="phone"
                                    type="tel"
                                    placeholder="+254712345678"
                                    value={phoneNumber}
                                    onChange={(e) => setPhoneNumber(e.target.value)}
                                    disabled={sendOTPMutation.isPending}
                                />
                            </div>
                            {error && (
                                <p className="text-sm text-destructive">{error}</p>
                            )}
                            <Button
                                type="submit"
                                className="w-full"
                                disabled={sendOTPMutation.isPending}
                            >
                                {sendOTPMutation.isPending ? 'Sending...' : 'Send OTP'}
                            </Button>
                        </form>
                    ) : (
                        <form onSubmit={handleVerifyOTP} className="space-y-4">
                            <div className="space-y-2">
                                <label htmlFor="otp" className="text-sm font-medium">
                                    OTP Code
                                </label>
                                <Input
                                    id="otp"
                                    type="text"
                                    placeholder="123456"
                                    maxLength={6}
                                    value={otp}
                                    onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                                    disabled={verifyOTPMutation.isPending}
                                />
                                <p className="text-xs text-muted-foreground">
                                    OTP sent to {phoneNumber}
                                </p>
                            </div>
                            {error && (
                                <p className="text-sm text-destructive">{error}</p>
                            )}
                            <div className="space-y-2">
                                <Button
                                    type="submit"
                                    className="w-full"
                                    disabled={verifyOTPMutation.isPending}
                                >
                                    {verifyOTPMutation.isPending ? 'Verifying...' : 'Verify OTP'}
                                </Button>
                                <Button
                                    type="button"
                                    variant="outline"
                                    className="w-full"
                                    onClick={handleBack}
                                    disabled={verifyOTPMutation.isPending}
                                >
                                    Back
                                </Button>
                            </div>
                        </form>
                    )}
                </CardContent>
            </Card>
        </div>
    )
}
