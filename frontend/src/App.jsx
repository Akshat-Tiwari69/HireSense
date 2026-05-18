import React from 'react';
import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ThemeProvider } from './context/ThemeProvider';
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import ApplyPage from "./pages/ApplyPage";
import InterviewerDashboardPage from "./pages/InterviewerDashboardPage";
import AssessmentPage from "./pages/AssessmentPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import ProctorDashboardPage from "./pages/ProctorDashboardPage";
import JobListingsPage from "./pages/JobListingsPage";
import NotFoundPage from "./pages/NotFoundPage";
import ProtectedRoute from "./components/ProtectedRoute";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <ThemeProvider>
      <div className="App">
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/jobs" element={<JobListingsPage />} />
            <Route path="/apply" element={<ApplyPage />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/assessment/:token" element={<AssessmentPage />} />

            {/* Protected routes — require a valid auth token */}
            <Route path="/dashboard" element={<ProtectedRoute element={<InterviewerDashboardPage />} requiredRole="interviewer" />} />
            <Route path="/interviewer-dashboard" element={<ProtectedRoute element={<InterviewerDashboardPage />} requiredRole="interviewer" />} />
            <Route path="/admin" element={<ProtectedRoute element={<AdminDashboardPage />} requiredRole="admin" />} />
            <Route path="/admin-dashboard" element={<ProtectedRoute element={<AdminDashboardPage />} requiredRole="admin" />} />
            <Route path="/proctor" element={<ProtectedRoute element={<ProctorDashboardPage />} requiredRole="proctor" />} />
            <Route path="/proctor-dashboard" element={<ProtectedRoute element={<ProctorDashboardPage />} requiredRole="proctor" />} />

            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Router>
        <Toaster />
      </div>
    </ThemeProvider>
  );
}

export default App;
