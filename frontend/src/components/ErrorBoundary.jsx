import { Component } from 'react';
import { AlertTriangle, Home, RefreshCw } from 'lucide-react';
import Logo from './Logo';
import { Button } from './ui/button';

class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Error caught by boundary:', error, errorInfo);
        this.setState({ hasError: true, error, errorInfo });
    }

    handleReset = () => {
        this.setState({ hasError: false, error: null, errorInfo: null });
        window.location.href = '/';
    };

    render() {
        if (this.state.hasError) {
            return (
                <main className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
                    <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm sm:p-10">
                            <Logo size="large" />
                            <div className="mt-8 flex justify-center">
                                <div className="flex h-12 w-12 items-center justify-center rounded-full bg-red-50">
                                    <AlertTriangle className="h-6 w-6 text-red-700" aria-hidden="true" />
                                </div>
                            </div>

                            <h1 className="mt-5 text-2xl font-semibold tracking-tight text-slate-950">Something went wrong</h1>
                            <p className="mt-3 text-sm leading-6 text-slate-600">
                                The page could not finish loading. Reload it once, or return to the home page and try again.
                            </p>

                            {import.meta.env.DEV && this.state.error && (
                                <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-left">
                                    <p className="break-all font-mono text-xs text-red-800">
                                        {this.state.error.toString()}
                                    </p>
                                </div>
                            )}

                            <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
                                <Button
                                    type="button"
                                    onClick={() => window.location.reload()}
                                    variant="outline"
                                >
                                    <RefreshCw className="mr-2 h-4 w-4" />
                                    Reload page
                                </Button>
                                <Button
                                    type="button"
                                    onClick={this.handleReset}
                                >
                                    <Home className="mr-2 h-4 w-4" />
                                    Go home
                                </Button>
                            </div>
                    </div>
                </main>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;
