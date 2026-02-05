import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { ShieldAlert, Home } from 'lucide-react';

const ForbiddenPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
            <Card className="w-full max-w-md shadow-2xl border-none text-center">
                <div className="p-12">
                    <div className="flex justify-center mb-6">
                        <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center">
                            <ShieldAlert className="w-14 h-14 text-red-600" />
                        </div>
                    </div>

                    <h1 className="text-6xl font-bold text-red-600 mb-4">403</h1>
                    <h2 className="text-2xl font-bold text-slate-900 mb-3">Access Denied</h2>
                    <p className="text-slate-600 mb-8">
                        You don't have permission to access this resource. Please contact your administrator if you believe this is an error.
                    </p>

                    <Button
                        onClick={() => navigate('/')}
                        className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg"
                    >
                        <Home className="w-4 h-4 mr-2" />
                        Go Home
                    </Button>
                </div>
            </Card>
        </div>
    );
};

export default ForbiddenPage;
