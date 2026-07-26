import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import LoadingScreen from "./components/common/LoadingScreen";
import { Toaster } from "./components/ui/sonner";
import { HIRING_REVIEW_ROLES } from './services/session';

const LandingPage = lazy(() => import("./pages/LandingPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const ApplyPage = lazy(() => import("./pages/ApplyPage"));
const InterviewerDashboardPage = lazy(() => import("./pages/InterviewerDashboardPage"));
const AssessmentPage = lazy(() => import("./pages/AssessmentPage"));
const AdminDashboardPage = lazy(() => import("./pages/AdminDashboardPage"));
const ProctorDashboardPage = lazy(() => import("./pages/ProctorDashboardPage"));
const JobListingsPage = lazy(() => import("./pages/JobListingsPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));
const LegalPage = lazy(() => import("./pages/LegalPage"));

function App() {
  return (
    <Router>
      <Suspense fallback={<LoadingScreen message="Loading page..." />}>
        <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/jobs" element={<JobListingsPage />} />
            <Route path="/careers" element={<Navigate to="/jobs" replace />} />
            <Route path="/apply" element={<ApplyPage />} />
            <Route path="/apply/:jobId" element={<ApplyPage />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/privacy" element={<LegalPage document="privacy" />} />
            <Route path="/terms" element={<LegalPage document="terms" />} />

            {/* Protected routes — require a valid auth token */}
            <Route path="/dashboard" element={<ProtectedRoute element={<InterviewerDashboardPage />} allowedRoles={HIRING_REVIEW_ROLES} />} />
            <Route path="/interviewer-dashboard" element={<Navigate to="/dashboard" replace />} />
            <Route path="/admin" element={<ProtectedRoute element={<AdminDashboardPage />} allowedRoles={['admin', 'super_admin']} />} />
            <Route path="/admin-dashboard" element={<Navigate to="/admin" replace />} />
            <Route path="/proctor" element={<ProtectedRoute element={<ProctorDashboardPage />} allowedRoles={['proctor']} />} />
            <Route path="/proctor-dashboard" element={<Navigate to="/proctor" replace />} />

            <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>
      <Toaster closeButton richColors />
    </Router>
  );
}

export default App;
