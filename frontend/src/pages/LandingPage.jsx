import React from 'react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-900 to-blue-900 flex flex-col justify-center items-center px-4 relative overflow-hidden">
            {/* Background Decorative Elements */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
                <div className="absolute top-10 left-10 w-64 h-64 bg-purple-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
                <div className="absolute top-10 right-10 w-64 h-64 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
                <div className="absolute -bottom-32 left-1/2 w-96 h-96 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
            </div>

            <div className="z-10 text-center max-w-4xl">
                <h1 className="text-5xl md:text-7xl font-bold text-white mb-6 tracking-tight">
                    CYGNUSA <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-teal-300">ELITE-HIRE</span>
                </h1>
                <p className="text-xl md:text-2xl text-blue-100 mb-16 font-light">
                    The Next-Generation AI Hiring & Evaluation Platform
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full max-w-2xl mx-auto">
                    {/* Candidate Card */}
                    <Link to="/upload" className="group relative bg-white bg-opacity-10 backdrop-filter backdrop-blur-lg border border-white border-opacity-20 rounded-2xl p-8 hover:bg-opacity-20 transition-all duration-300 transform hover:-translate-y-2 hover:shadow-2xl">
                        <div className="absolute -top-6 -left-6 w-16 h-16 bg-blue-500 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-4 mt-2">I'm a Candidate</h2>
                        <p className="text-blue-100">Submit your resume, complete AI assessments, and show your true potential.</p>
                        <div className="mt-6 flex items-center text-blue-300 font-semibold group-hover:text-white transition-colors">
                            Get Started <span className="ml-2">→</span>
                        </div>
                    </Link>

                    {/* Recruiter Card */}
                    <Link to="/dashboard" className="group relative bg-white bg-opacity-10 backdrop-filter backdrop-blur-lg border border-white border-opacity-20 rounded-2xl p-8 hover:bg-opacity-20 transition-all duration-300 transform hover:-translate-y-2 hover:shadow-2xl">
                        <div className="absolute -top-6 -right-6 w-16 h-16 bg-purple-500 rounded-2xl flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path></svg>
                        </div>
                        <h2 className="text-2xl font-bold text-white mb-4 mt-2">I'm a Recruiter</h2>
                        <p className="text-blue-100">Review top talent, track assessment scores, and make data-driven hiring decisions.</p>
                        <div className="mt-6 flex items-center text-purple-300 font-semibold group-hover:text-white transition-colors">
                            View Dashboard <span className="ml-2">→</span>
                        </div>
                    </Link>
                </div>

                <footer className="mt-20 text-blue-200 opacity-60 text-sm">
                    © 2026 Cygnusa Elite-Hire. Powered by AI.
                </footer>
            </div>
        </div>
    );
};

export default LandingPage;
