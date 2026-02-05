import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, CheckCircle, Shield, Zap, Target,
  Brain, Users, TrendingUp, Clock, Award, X, BarChart3, Star, LogIn,
  Menu, X as XIcon, Sparkles
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "../components/ui/Dialog";
import Logo from '../components/Logo';

const LandingPage = () => {
  const navigate = useNavigate();
  const [showPrivacy, setShowPrivacy] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const [showContact, setShowContact] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <Logo size="default" />
          <div className="hidden sm:flex gap-4">
            <Button
              variant="outline"
              onClick={() => navigate('/login')}
              className="border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 hover:border-indigo-700 transition-all duration-200 font-semibold px-4 sm:px-6 py-2 rounded-lg flex items-center gap-2 hover:shadow-lg"
            >
              <LogIn className="w-4 h-4" />
              <span>Sign In</span>
            </Button>
          </div>
          <button 
            className="sm:hidden p-2 hover:bg-indigo-50 rounded-lg transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? (
              <XIcon className="w-6 h-6 text-slate-900" />
            ) : (
              <Menu className="w-6 h-6 text-slate-900" />
            )}
          </button>
        </div>
        
        {/* Mobile Menu */}
        {mobileMenuOpen && (
          <div className="sm:hidden border-t bg-white animate-in fade-in slide-in-from-top-2 duration-300">
            <div className="px-4 py-4 flex flex-col gap-3">
              <Button
                size="sm"
                onClick={() => {
                  navigate('/login');
                  setMobileMenuOpen(false);
                }}
                className="bg-indigo-600 hover:bg-indigo-700 text-white w-full rounded-lg transition-all duration-200"
              >
                Sign In
              </Button>
            </div>
          </div>
        )}
      </header>

      {/* Hero Section - Mobile Optimized */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-12 sm:pt-20 pb-16 sm:pb-24 relative overflow-hidden">
        {/* Animated background elements */}
        <div className="absolute top-10 right-10 w-72 h-72 bg-indigo-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob hidden lg:block"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000 hidden lg:block"></div>
        
        <div className="text-center max-w-4xl mx-auto relative z-10">
          <div className="inline-flex items-center gap-2 px-3 sm:px-4 py-1.5 sm:py-2 bg-gradient-to-r from-indigo-100 to-blue-100 rounded-full text-indigo-700 text-xs sm:text-sm font-medium mb-6 sm:mb-8 animate-in fade-in slide-in-from-bottom-4 duration-700 border border-indigo-200">
            <Sparkles className="w-3 h-3 sm:w-4 sm:h-4" />
            AI-Powered Hiring Platform
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 mb-4 sm:mb-6 leading-tight animate-in fade-in slide-in-from-bottom-4 duration-700 delay-100">
            Hire faster. Hire smarter.
            <span className="block bg-gradient-to-r from-indigo-600 to-blue-600 text-transparent bg-clip-text mt-2">Powered by AI.</span>
          </h1>

          <p className="text-base sm:text-lg lg:text-xl text-slate-600 mb-8 sm:mb-12 leading-relaxed px-4 sm:px-0 animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200 max-w-2xl mx-auto">
            Automated resume screening, AI-driven assessments, and data-backed hiring decisions — all in one platform.
          </p>

          {/* Mobile-First CTAs */}
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center items-stretch sm:items-center animate-in fade-in slide-in-from-bottom-4 duration-700 delay-300 px-4 sm:px-0">
            <Button
              size="lg"
              onClick={() => navigate('/login')}
              className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-700 hover:to-blue-700 text-white px-6 sm:px-8 py-5 sm:py-6 text-base sm:text-lg rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105 w-full sm:w-auto font-semibold"
            >
              I'm an Interviewer
              <ArrowRight className="ml-2 w-4 h-4 sm:w-5 sm:h-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => navigate('/apply')}
              className="border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 px-6 sm:px-8 py-5 sm:py-6 text-base sm:text-lg rounded-lg transition-all duration-300 hover:scale-105 w-full sm:w-auto font-semibold hover:border-indigo-700 hover:shadow-md"
            >
              I'm a Candidate
              <ArrowRight className="ml-2 w-4 h-4 sm:w-5 sm:h-5" />
            </Button>
          </div>
        </div>
      </section>

      {/* Trust Indicators - Simplified for Mobile */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-20">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6">
          <Card className="p-4 sm:p-6 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border-l-4 border-indigo-600 group">
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="p-2 sm:p-3 bg-indigo-100 rounded-lg flex-shrink-0 group-hover:bg-indigo-200 transition-colors duration-300">
                <BarChart3 className="w-5 h-5 sm:w-6 sm:h-6 text-indigo-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-1 sm:mb-2 text-sm sm:text-base">AI-Powered Scoring</h3>
                <p className="text-slate-600 text-xs sm:text-sm">Advanced algorithms analyze candidates objectively</p>
              </div>
            </div>
          </Card>

          <Card className="p-4 sm:p-6 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border-l-4 border-emerald-600 group">
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="p-2 sm:p-3 bg-emerald-100 rounded-lg flex-shrink-0 group-hover:bg-emerald-200 transition-colors duration-300">
                <Users className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-600" />
              </div>
              <div>
                <h3 className="font-semibold text-slate-900 mb-1 sm:mb-2 text-sm sm:text-base">Bias-Aware Hiring</h3>
                <p className="text-slate-600 text-xs sm:text-sm">Reduce unconscious bias with data-driven evaluation</p>
              </div>
            </div>
          </Card>

          <Card className="p-4 sm:p-6 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border-l-4 border-blue-600 group">
            <div className="flex items-start gap-3 sm:gap-4">
              <div className="p-2 sm:p-3 bg-blue-100 rounded-lg flex-shrink-0 group-hover:bg-blue-200 transition-colors duration-300">
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

      {/* Stats Section - Responsive for All Devices */}
      <section className="bg-gradient-to-r from-indigo-600 via-indigo-600 to-blue-600 py-12 sm:py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8">
            <div className="text-center transform transition-transform duration-300 hover:scale-105">
              <div className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-2">85%</div>
              <div className="text-indigo-100 text-xs sm:text-sm lg:text-base font-medium">Faster Hiring</div>
            </div>
            <div className="text-center transform transition-transform duration-300 hover:scale-105">
              <div className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-2">3x</div>
              <div className="text-indigo-100 text-xs sm:text-sm lg:text-base font-medium">Better Matches</div>
            </div>
            <div className="text-center transform transition-transform duration-300 hover:scale-105">
              <div className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-2">50k+</div>
              <div className="text-indigo-100 text-xs sm:text-sm lg:text-base font-medium">Candidates Assessed</div>
            </div>
            <div className="text-center transform transition-transform duration-300 hover:scale-105">
              <div className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-2">98%</div>
              <div className="text-indigo-100 text-xs sm:text-sm lg:text-base font-medium">Client Satisfaction</div>
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
          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 group hover:-translate-y-1 border-t-4 border-indigo-600">
            <div className="mb-4">
              <div className="w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center group-hover:bg-indigo-200 group-hover:scale-110 transition-all duration-300">
                <Clock className="w-6 h-6 text-indigo-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Save 85% Time</h3>
            <p className="text-slate-600 text-sm sm:text-base">Automate resume screening and initial assessments</p>
          </Card>

          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 group hover:-translate-y-1 border-t-4 border-emerald-600">
            <div className="mb-4">
              <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center group-hover:bg-emerald-200 group-hover:scale-110 transition-all duration-300">
                <TrendingUp className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Better Quality</h3>
            <p className="text-slate-600 text-sm sm:text-base">Data-driven insights lead to superior hiring decisions</p>
          </Card>

          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 group hover:-translate-y-1 border-t-4 border-blue-600">
            <div className="mb-4">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center group-hover:bg-blue-200 group-hover:scale-110 transition-all duration-300">
                <Award className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Fair & Unbiased</h3>
            <p className="text-slate-600 text-sm sm:text-base">AI-powered evaluation reduces human bias</p>
          </Card>

          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 group hover:-translate-y-1 border-t-4 border-purple-600">
            <div className="mb-4">
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center group-hover:bg-purple-200 group-hover:scale-110 transition-all duration-300">
                <CheckCircle className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Comprehensive Tests</h3>
            <p className="text-slate-600 text-sm sm:text-base">MCQs, coding challenges, and psychometric assessments</p>
          </Card>

          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 group hover:-translate-y-1 border-t-4 border-amber-600">
            <div className="mb-4">
              <div className="w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center group-hover:bg-amber-200 group-hover:scale-110 transition-all duration-300">
                <Star className="w-6 h-6 text-amber-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Real-time Analytics</h3>
            <p className="text-slate-600 text-sm sm:text-base">Track hiring metrics and candidate performance instantly</p>
          </Card>

          <Card className="p-6 sm:p-8 bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 group hover:-translate-y-1 border-t-4 border-rose-600">
            <div className="mb-4">
              <div className="w-12 h-12 bg-rose-100 rounded-lg flex items-center justify-center group-hover:bg-rose-200 group-hover:scale-110 transition-all duration-300">
                <Shield className="w-6 h-6 text-rose-600" />
              </div>
            </div>
            <h3 className="text-lg sm:text-xl font-semibold text-slate-900 mb-2">Enterprise Security</h3>
            <p className="text-slate-600 text-sm sm:text-base">SOC 2 Type II certified with end-to-end encryption</p>
          </Card>
        </div>
      </section>

      {/* CTA Section - Mobile Optimized */}
      <section className="bg-gradient-to-r from-indigo-600 via-indigo-600 to-blue-600 py-12 sm:py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4 sm:mb-6">Ready to Transform Your Hiring?</h2>
          <p className="text-lg sm:text-xl text-indigo-100 mb-8 sm:mb-10 max-w-2xl mx-auto">Join hundreds of companies making smarter hiring decisions with AI</p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center px-4 sm:px-0">
            <Button
              size="lg"
              onClick={() => navigate('/login')}
              className="bg-white text-slate-900 hover:bg-indigo-50 font-bold px-8 sm:px-10 py-6 sm:py-7 text-lg sm:text-xl rounded-xl shadow-2xl hover:shadow-3xl transition-all duration-300 hover:scale-105 w-full sm:w-auto"
            >
              Get Started Now
              <ArrowRight className="ml-2 w-5 h-5 sm:w-6 sm:h-6" />
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 py-8 sm:py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <Logo size="default" className="text-white" />
            <div className="flex flex-wrap justify-center gap-4 sm:gap-8 text-sm sm:text-base">
              <button
                onClick={() => setShowPrivacy(true)}
                className="text-slate-300 hover:text-white transition-colors cursor-pointer"
              >
                Privacy Policy
              </button>
              <button
                onClick={() => setShowTerms(true)}
                className="text-slate-300 hover:text-white transition-colors cursor-pointer"
              >
                Terms of Service
              </button>
              <button
                onClick={() => setShowContact(true)}
                className="text-slate-300 hover:text-white transition-colors cursor-pointer"
              >
                Contact
              </button>
            </div>
          </div>
          <div className="mt-6 sm:mt-8 text-center text-sm sm:text-base text-slate-400">
            © 2025 HireSense. All rights reserved.
          </div>
        </div>
      </footer>

      {/* Privacy Policy Dialog */}
      <Dialog open={showPrivacy} onOpenChange={setShowPrivacy}>
        <DialogContent className="bg-white max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-slate-900 text-2xl">Privacy Policy</DialogTitle>
            <DialogDescription className="text-slate-600 text-base">
              Our privacy policy is currently being finalized
            </DialogDescription>
          </DialogHeader>
          <div className="py-6">
            <p className="text-slate-700 text-base leading-relaxed">
              The HireSense Privacy Policy is currently under development. We are committed to protecting your data and will publish our comprehensive privacy policy soon.
            </p>
            <p className="text-slate-700 text-base leading-relaxed mt-4">
              For any privacy-related questions, please contact our team using the Contact option in the footer.
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Terms of Service Dialog */}
      <Dialog open={showTerms} onOpenChange={setShowTerms}>
        <DialogContent className="bg-white max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-slate-900 text-2xl">Terms of Service</DialogTitle>
            <DialogDescription className="text-slate-600 text-base">
              Our terms of service are currently being finalized
            </DialogDescription>
          </DialogHeader>
          <div className="py-6">
            <p className="text-slate-700 text-base leading-relaxed">
              The HireSense Terms of Service are currently under development. We are working to provide clear and comprehensive terms for all our users.
            </p>
            <p className="text-slate-700 text-base leading-relaxed mt-4">
              For any questions about our service terms, please contact our team using the Contact option in the footer.
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Contact Dialog */}
      <Dialog open={showContact} onOpenChange={setShowContact}>
        <DialogContent className="bg-white max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-slate-900 text-2xl">Contact Us</DialogTitle>
            <DialogDescription className="text-slate-600 text-base">
              Meet the team behind HireSense
            </DialogDescription>
          </DialogHeader>
          <div className="py-6 space-y-6">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-900">Development Team</h3>

              <div className="flex items-center gap-3 p-4 bg-indigo-50 rounded-lg border border-indigo-100">
                <div className="w-10 h-10 bg-indigo-600 rounded-full flex items-center justify-center text-white font-bold">
                  AT
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Akshat Tiwari</p>
                  <p className="text-sm text-slate-600">Backend Developer</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg border border-blue-100">
                <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                  SP
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Shaivi Prasad</p>
                  <p className="text-sm text-slate-600">Frontend Developer</p>
                </div>
              </div>

              <div className="flex items-center gap-3 p-4 bg-emerald-50 rounded-lg border border-emerald-100">
                <div className="w-10 h-10 bg-emerald-600 rounded-full flex items-center justify-center text-white font-bold">
                  PR
                </div>
                <div>
                  <p className="font-semibold text-slate-900">Prashant Rao</p>
                  <p className="text-sm text-slate-600">Database Administrator</p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <p className="text-sm text-slate-600 text-center">
                For support or inquiries, reach out to any team member above.
              </p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LandingPage;
