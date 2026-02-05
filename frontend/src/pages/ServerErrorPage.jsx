import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { ServerCrash, Home, RefreshCw } from 'lucide-react';

const ServerErrorPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
            <Card className="w-full max-w-md shadow-2xl border-none text-center">
                <div className="p-12">
                    <div className="flex justify-center mb-6">
                        <div className="w-24 h-24 bg-amber-100 rounded-full flex items-center justify-center">
                            <ServerCrash className="w-14 h-14 text-amber-600" />
                        </div>
                    </div>

                    <h1 className="text-6xl font-bold text-amber-600 mb-4">500</h1>
                    <h2 className="text-2xl font-bold text-slate-900 mb-3">Server Error</h2>
                    <p className="text-slate-600 mb-8">
                        Oops! Something went wrong on our end. Our team has been notified and we're working to fix it.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <Button
                            onClick={() => window.location.reload()}
                            variant="outline"
                            className="border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50"
                        >
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Try Again
                        </Button>
                        <Button
                            onClick={() => navigate('/')}
                            className="bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg"
                        >
                            <Home className="w-4 h-4 mr-2" />
                            Go Home
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
};

export default ServerErrorPage;
