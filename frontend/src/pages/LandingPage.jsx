import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { CheckCircle, Zap, Shield, BarChart3, Users, Award, Clock, TrendingUp, ArrowRight, Star } from 'lucide-react';
import Logo from '../components/Logo';

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <Logo size="default" />
          <Button
            variant="ghost"
            onClick={() => navigate('/login')}
            className="text-slate-700 hover:text-indigo-600 transition-colors text-sm sm:text-base"
          >
            Sign In
          </Button>
        </div>
      </header>

      {/* Hero Section - Mobile Optimized */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-12 sm:pt-20 pb-16 sm:pb-24">
        <div className="text-center max-w-4xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-indigo-100 rounded-full text-indigo-700 text-xs sm:text-sm font-medium mb-6 sm:mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
            <Zap className="w-3 h-3 sm:w-4 sm:h-4" />
            AI-Powered Hiring Platform
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 mb-4 sm:mb-6 leading-tight animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            Hire faster. Hire smarter.
            <span className="block text-indigo-600 mt-2">Powered by AI.</span>
          </h1>

          <p className="text-base sm:text-lg lg:text-xl text-slate-600 mb-8 sm:mb-12 leading-relaxed px-4 sm:px-0 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
            Automated resume screening, AI-driven assessments, and data-backed hiring decisions — all in one platform.
          </p>

          {/* Mobile-First CTAs */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-stretch sm:items-center animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300 px-4 sm:px-0">
            <Button
              size="lg"
              onClick={() => navigate('/login')}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 sm:px-8 py-5 sm:py-6 text-base sm:text-lg rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 w-full sm:w-auto"
            >
              I'm an Interviewer
              <ArrowRight className="ml-2 w-4 h-4 sm:w-5 sm:h-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/apply')}
              className="border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 px-6 sm:px-8 py-5 sm:py-6 text-base sm:text-lg rounded-lg transition-all duration-300 hover:scale-105 w-full sm:w-auto"
            >
              I'm a Candidate
              <ArrowRight className="ml-2 w-4 h-4 sm:w-5 sm:h-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Trust Indicators - Simplified for Mobile */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pb-12 sm:pb-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
          <Card className="p-4 sm:p-6 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="p-2 sm:p-3 bg-indigo-100 rounded-lg flex-shrink-0">
                <BarChart3 className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-1 sm:mb-2 text-sm sm:text-base">AI-Powered Scoring</h3>
                <p className="text-slate-600 text-xs sm:text-sm">Advanced algorithms analyze candidates objectively</p>
              </div>
            </div>
          </Card>

          <Card className="p-4 sm:p-6 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="p-2 sm:p-3 bg-emerald-100 rounded-lg flex-shrink-0">
                <Users className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-1 sm:mb-2 text-sm sm:text-base">Bias-Aware Hiring</h3>
                <p className="text-slate-600 text-xs sm:text-sm">Reduce unconscious bias with data-driven evaluation</p>
              </div>
            </div>
          </Card>

          <Card className="p-4 sm:p-6 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="p-2 sm:p-3 bg-blue-100 rounded-lg flex-shrink-0">
                <Shield className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-1 sm:mb-2 text-sm sm:text-base">Secure & GDPR-Ready</h3>
                <p className="text-slate-600 text-xs sm:text-sm">Enterprise-grade security with full compliance</p>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Stats Section - Desktop Only */}
      <section className="hidden lg:block bg-indigo-600 py-16">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-5xl font-bold text-white mb-2">85%</div>
              <div className="text-indigo-200">Faster Hiring</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-white mb-2">3x</div>
              <div className="text-indigo-200">Better Matches</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-white mb-2">50k+</div>
              <div className="text-indigo-200">Candidates Assessed</div>
            </div>
            <div className="text-center">
              <div className="text-5xl font-bold text-white mb-2">98%</div>
              <div className="text-indigo-200">Client Satisfaction</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="bg-white py-12 sm:py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-10 sm:mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3 sm:mb-4">How It Works</h2>
            <p className="text-base sm:text-xl text-slate-600">Three simple steps to smarter hiring</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 sm:gap-12">
            <div className="text-center">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-6">
                <span className="text-xl sm:text-2xl font-bold text-indigo-600">1</span>
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2 sm:mb-3">Upload Resume / Apply</h3>
              <p className="text-slate-600 text-sm sm:text-base">Candidates submit their resumes through our streamlined application process</p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-6">
                <span className="text-xl sm:text-2xl font-bold text-indigo-600">2</span>
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2 sm:mb-3">AI Assessment & Evaluation</h3>
              <p className="text-slate-600 text-sm sm:text-base">Our AI analyzes resumes, conducts assessments, and generates insights</p>
            </div>

            <div className="text-center">
              <div className="w-12 h-12 sm:w-16 sm:h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4 sm:mb-6">
                <span className="text-xl sm:text-2xl font-bold text-indigo-600">3</span>
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2 sm:mb-3">Hire with Confidence</h3>
              <p className="text-slate-600 text-sm sm:text-base">Make data-backed decisions with comprehensive AI-generated reports</p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid - Desktop Enhanced */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-20">
        <div className="text-center mb-10 sm:mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3 sm:mb-4">Why Choose HireSense?</h2>
          <p className="text-base sm:text-xl text-slate-600">Enterprise-grade features for modern hiring</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
            <div className="mb-4">
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                <Clock className="w-6 h-6 text-indigo-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Save 85% Time</h3>
            <p className="text-slate-600 text-sm sm:text-base">Automate resume screening and initial assessments</p>
          </Card>

          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
            <div className="mb-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Better Quality</h3>
            <p className="text-slate-600 text-sm sm:text-base">Data-driven insights lead to superior hiring decisions</p>
          </Card>

          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
            <div className="mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <Award className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Fair & Unbiased</h3>
            <p className="text-slate-600 text-sm sm:text-base">AI-powered evaluation reduces human bias</p>
          </Card>

          {/* Desktop Only Features */}
          <Card className="hidden lg:block p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
            <div className="mb-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <CheckCircle className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Comprehensive Tests</h3>
            <p className="text-slate-600 text-sm sm:text-base">MCQs, coding challenges, and psychometric assessments</p>
          </Card>

          <Card className="hidden lg:block p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
            <div className="mb-4">
              <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center">
                <Star className="w-6 h-6 text-amber-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Real-time Analytics</h3>
            <p className="text-slate-600 text-sm sm:text-base">Track hiring metrics and candidate performance instantly</p>
          </Card>

          <Card className="hidden lg:block p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
            <div className="mb-4">
              <div className="w-12 h-12 bg-rose-100 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-rose-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Enterprise Security</h3>
            <p className="text-slate-600 text-sm sm:text-base">SOC 2 Type II certified with end-to-end encryption</p>
          </Card>
        </div>
      </section>

      {/* CTA Section - Mobile Optimized */}
      <section className="bg-gradient-to-r from-indigo-600 to-indigo-700 py-12 sm:py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 sm:mb-6">Ready to Transform Your Hiring?</h2>
          <p className="text-lg sm:text-xl text-indigo-100 mb-8 sm:mb-10">Join hundreds of companies making smarter hiring decisions with AI</p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4 sm:px-0">
            <Button
              size="lg"
              onClick={() => navigate('/login')}
              className="bg-white text-indigo-600 hover:bg-slate-100 px-6 sm:px-8 py-5 sm:py-6 text-base sm:text-lg rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 w-full sm:w-auto"
            >
              Get Started Now
              <ArrowRight className="ml-2 w-4 h-4 sm:w-5 sm:h-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-8 sm:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <Logo size="default" className="text-white" />
            <div className="flex flex-wrap justify-center gap-4 sm:gap-8 text-xs sm:text-sm text-slate-400">
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>
          </div>
          <div className="mt-6 sm:mt-8 text-center text-xs sm:text-sm text-slate-500">
            © 2025 HireSense. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
