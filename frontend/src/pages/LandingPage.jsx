import React from 'react';
import { useNavigate } from 'react-router-dom';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-900 text-white overflow-hidden relative selection:bg-indigo-500 selection:text-white">
      {/* Background Gradients */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-purple-700/20 rounded-full blur-[120px]"></div>
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-indigo-700/20 rounded-full blur-[120px]"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-16 flex flex-col items-center justify-center min-h-screen">
        
        {/* Header */}
        <div className="text-center mb-16 space-y-4">
          <h1 className="text-5xl md:text-7xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 animate-fade-in-up">
            Cygnusa Elite-Hire
          </h1>
          <p className="text-slate-400 text-xl md:text-2xl max-w-2xl mx-auto font-light">
            The next generation AI-enabled hiring platform.
          </p>
        </div>

        {/* Action Cards */}
        <div className="grid md:grid-cols-2 gap-8 w-full max-w-4xl">
          
          {/* Candidate Card */}
          <div 
            onClick={() => navigate('/upload')}
            className="group relative bg-slate-800/50 hover:bg-slate-800/80 backdrop-blur-xl border border-slate-700 hover:border-indigo-500/50 rounded-2xl p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/20 transform hover:-translate-y-1"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl"></div>
            
            <div className="relative z-10 flex flex-col items-center text-center space-y-6">
              <div className="w-16 h-16 bg-gradient-to-br from-indigo-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              
              <div className="space-y-2">
                <h2 className="text-3xl font-semibold text-white group-hover:text-indigo-400 transition-colors">I'm a Candidate</h2>
                <p className="text-slate-400">
                  Upload your resume, take assessments, and track your application status.
                </p>
              </div>

              <div className="pt-4">
                <span className="inline-flex items-center text-indigo-400 font-medium group-hover:translate-x-1 transition-transform">
                  Get Started 
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </span>
              </div>
            </div>
          </div>

          {/* Recruiter Card */}
          <div 
            onClick={() => navigate('/login')}
            className="group relative bg-slate-800/50 hover:bg-slate-800/80 backdrop-blur-xl border border-slate-700 hover:border-pink-500/50 rounded-2xl p-8 cursor-pointer transition-all duration-300 hover:shadow-2xl hover:shadow-pink-500/20 transform hover:-translate-y-1"
          >
             <div className="absolute inset-0 bg-gradient-to-br from-pink-600/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-2xl"></div>

            <div className="relative z-10 flex flex-col items-center text-center space-y-6">
              <div className="w-16 h-16 bg-gradient-to-br from-pink-500 to-rose-600 rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              
              <div className="space-y-2">
                <h2 className="text-3xl font-semibold text-white group-hover:text-pink-400 transition-colors">I'm a Recruiter</h2>
                <p className="text-slate-400">
                  Manage candidates, review AI insights, and make hiring decisions.
                </p>
              </div>

               <div className="pt-4">
                <span className="inline-flex items-center text-pink-400 font-medium group-hover:translate-x-1 transition-transform">
                  Login to Dashboard 
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </span>
              </div>
            </div>
          </div>

        </div>

        {/* Footer */}
        <div className="mt-20 text-slate-500 text-sm">
          &copy; {new Date().getFullYear()} Cygnusa Elite-Hire. All rights reserved.
        </div>
      </div>
    </div>
  );
};

export default LandingPage;
