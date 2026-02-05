import React from 'react';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
        this.state = { hasError: true, error, errorInfo };
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
        window.location.href = '/';
    };

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4">
                    <Card className="w-full max-w-md shadow-2xl border-none text-center">
                        <div className="p-12">
                            <div className="flex justify-center mb-6">
                                <div className="w-24 h-24 bg-red-100 rounded-full flex items-center justify-center">
                                    <AlertTriangle className="w-14 h-14 text-red-600" />
                                </div>
                            </div>

                            <h1 className="text-2xl font-bold text-slate-900 mb-3">Oops! Something went wrong</h1>
                            <p className="text-slate-600 mb-6">
                                An unexpected error occurred. Don't worry, we've logged it and our team will look into it.
                            </p>

                            {process.env.NODE_ENV === 'development' && this.state.error && (
                                <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
                                    <p className="text-xs font-mono text-red-800 break-all">
                                        {this.state.error.toString()}
                                    </p>
                                </div>
                            )}

                            <div className="flex flex-col sm:flex-row gap-3 justify-center">
                                <Button
                                    onClick={() => window.location.reload()}
                                    variant="outline"
                                    className="border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50"
                                >
                                    <RefreshCw className="w-4 h-4 mr-2" />
                                    Reload Page
                                </Button>
                                <Button
                                    onClick={this.handleReset}
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
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
