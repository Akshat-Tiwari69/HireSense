import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import ApplyPage from "./pages/ApplyPage";
import InterviewerDashboardPage from "./pages/InterviewerDashboardPage";
import AssessmentPage from "./pages/AssessmentPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import ProctorDashboardPage from "./pages/ProctorDashboardPage";
import { Toaster } from "./components/ui/sonner";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/apply" element={<ApplyPage />} />
          <Route path="/dashboard" element={<InterviewerDashboardPage />} />
          <Route path="/admin" element={<AdminDashboardPage />} />
          <Route path="/proctor" element={<ProctorDashboardPage />} />
          <Route path="/assessment" element={<AssessmentPage />} />
          <Route path="/assessment/:token" element={<AssessmentPage />} />
        </Routes>
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;
