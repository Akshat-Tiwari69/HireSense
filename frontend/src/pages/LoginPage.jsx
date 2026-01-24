import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Loader2 } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { login } from '../services/api';

const LoginPage = () => {
    const navigate = useNavigate();
    const { toast } = useToast();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});

    const validateForm = () => {
        const newErrors = {};
        if (!email) {
            newErrors.email = 'Email is required';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
            newErrors.email = 'Invalid email format';
        }
        if (!password) {
            newErrors.password = 'Password is required';
        } else if (password.length < 6) {
            newErrors.password = 'Password must be at least 6 characters';
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        if (!validateForm()) return;

        setLoading(true);

        try {
            const response = await login(email, password);

            // Check for token in response (adjust structure based on actual API response)
            // The mock in api.js returns { data: { token: ..., user: ... } }
            const data = response.data || response;

            if (data.token) {
                localStorage.setItem('authToken', data.token);
                localStorage.setItem('userEmail', email);
                if (data.user) {
                    localStorage.setItem('userData', JSON.stringify(data.user));
                }

                toast({
                    title: 'Login successful',
                    description: 'Welcome back!',
                });
                navigate('/dashboard');
            } else {
                throw new Error('No access token received');
            }
        } catch (error) {
            console.error("Login Error:", error);
            toast({
                variant: 'destructive',
                title: 'Login failed',
                description: error.message || 'Invalid email or password',
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4 sm:p-6">
            <Card className="w-full max-w-md shadow-2xl border-none">
                <CardHeader className="space-y-4 text-center pb-6">
                    <div className="flex justify-center">
                        <div className="p-3 bg-indigo-50 rounded-xl">
                            <Logo variant="icon" size="large" />
                        </div>
                    </div>
                    <div>
                        <CardTitle className="text-2xl sm:text-3xl font-bold text-slate-900">Welcome Back</CardTitle>
                        <CardDescription className="text-sm sm:text-base text-slate-600 mt-2">
                            Sign in to access your interviewer dashboard
                        </CardDescription>
                    </div>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleLogin} className="space-y-4">
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-slate-700">Email</Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="interviewer@company.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className={`h-11 ${errors.email ? 'border-red-500' : ''}`}
                            />
                            {errors.email && (
                                <p className="text-sm text-red-600">{errors.email}</p>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-slate-700">Password</Label>
                            <Input
                                id="password"
                                type="password"
                                placeholder="Enter your password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className={`h-11 ${errors.password ? 'border-red-500' : ''}`}
                            />
                            {errors.password && (
                                <p className="text-sm text-red-600">{errors.password}</p>
                            )}
                        </div>

                        <Button
                            type="submit"
                            className="w-full bg-indigo-600 hover:bg-indigo-700 h-11 text-base font-medium transition-all duration-300 hover:scale-[1.02]"
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                                    Signing in...
                                </>
                            ) : (
                                'Sign In'
                            )}
                        </Button>
                    </form>

                    <div className="mt-6 pt-6 border-t text-center">
                        <p className="text-sm text-slate-600">
                            Demo credentials: <span className="font-mono text-indigo-600">interviewer@company.com</span> / <span className="font-mono text-indigo-600">password123</span>
                        </p>
                    </div>

                    <div className="mt-4 text-center">
                        <Button
                            variant="link"
                            onClick={() => navigate('/')}
                            className="text-slate-600 hover:text-indigo-600"
                        >
                            ← Back to home
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default LoginPage;
