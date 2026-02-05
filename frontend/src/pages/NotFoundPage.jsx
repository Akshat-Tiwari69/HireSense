import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { FileQuestion, Home, ArrowLeft } from 'lucide-react';
import Logo from '../components/Logo';

const NotFoundPage = () => {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
            <Card className="w-full max-w-md shadow-2xl border-none text-center">
                <div className="p-12">
                    <div className="flex justify-center mb-6">
                        <div className="w-24 h-24 bg-indigo-100 rounded-full flex items-center justify-center">
                            <FileQuestion className="w-14 h-14 text-indigo-600" />
                        </div>
                    </div>

                    <h1 className="text-6xl font-bold text-indigo-600 mb-4">404</h1>
                    <h2 className="text-2xl font-bold text-slate-900 mb-3">Page Not Found</h2>
                    <p className="text-slate-600 mb-8">
                        Sorry, the page you're looking for doesn't exist or has been moved.
                    </p>

                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <Button
                            onClick={() => navigate(-1)}
                            variant="outline"
                            className="border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50"
                        >
                            <ArrowLeft className="w-4 h-4 mr-2" />
                            Go Back
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

export default NotFoundPage;
