import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuthStore } from '@/store/authStore'

export default function DashboardPage() {
    const { phoneNumber } = useAuthStore()

    return (
        <div className="space-y-6">
            <Card>
                <CardHeader>
                    <CardTitle>Welcome to MavunoSure</CardTitle>
                    <CardDescription>
                        Logged in as {phoneNumber}
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-gray-600">
                        Claim verification dashboard components will be implemented in subsequent tasks.
                    </p>
                </CardContent>
            </Card>
        </div>
    )
}
