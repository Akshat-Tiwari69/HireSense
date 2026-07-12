import { lazy, Suspense } from 'react';
import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import LoadingScreen from "./components/common/LoadingScreen";
import { Toaster } from "./components/ui/sonner";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const ApplyPage = lazy(() => import("./pages/ApplyPage"));
const InterviewerDashboardPage = lazy(() => import("./pages/InterviewerDashboardPage"));
const AssessmentPage = lazy(() => import("./pages/AssessmentPage"));
const AdminDashboardPage = lazy(() => import("./pages/AdminDashboardPage"));
const ProctorDashboardPage = lazy(() => import("./pages/ProctorDashboardPage"));
const JobListingsPage = lazy(() => import("./pages/JobListingsPage"));
const NotFoundPage = lazy(() => import("./pages/NotFoundPage"));

function App() {
  return (
    <div className="App">
        <Router>
          <Suspense fallback={<LoadingScreen message="Loading page..." />}>
            <Routes>
            {/* Public routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/jobs" element={<JobListingsPage />} />
            <Route path="/apply" element={<ApplyPage />} />
            <Route path="/assessment" element={<AssessmentPage />} />
            <Route path="/assessment/:token" element={<AssessmentPage />} />

            {/* Protected routes — require a valid auth token */}
            <Route path="/dashboard" element={<ProtectedRoute element={<InterviewerDashboardPage />} allowedRoles={['interviewer']} />} />
            <Route path="/interviewer-dashboard" element={<ProtectedRoute element={<InterviewerDashboardPage />} allowedRoles={['interviewer']} />} />
            <Route path="/admin" element={<ProtectedRoute element={<AdminDashboardPage />} allowedRoles={['admin', 'super_admin']} />} />
            <Route path="/admin-dashboard" element={<ProtectedRoute element={<AdminDashboardPage />} allowedRoles={['admin', 'super_admin']} />} />
            <Route path="/proctor" element={<ProtectedRoute element={<ProctorDashboardPage />} allowedRoles={['proctor']} />} />
            <Route path="/proctor-dashboard" element={<ProtectedRoute element={<ProctorDashboardPage />} allowedRoles={['proctor']} />} />

            <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </Suspense>
        </Router>
        <Toaster />
    </div>
  );
}

export default App;
