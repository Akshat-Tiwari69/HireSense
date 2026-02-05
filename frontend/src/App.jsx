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
import NotFoundPage from "./pages/NotFoundPage";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <ThemeProvider>
      <div className="App">
        <Router>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/apply" element={<ApplyPage />} />
            <Route path="/dashboard" element={<InterviewerDashboardPage />} />
            <Route path="/admin" element={<AdminDashboardPage />} />
            <Route path="/proctor" element={<ProctorDashboardPage />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/assessment/:token" element={<AssessmentPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </Router>
        <Toaster />
      </div>
    </ThemeProvider>
  );
}

export default App;
