import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Users, Shield, UserPlus, BarChart3, Mail, Briefcase,
  AlertTriangle, Upload, BookOpen,
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { toJobClosingInputValue } from '../lib/jobs';
import { api } from '../services/api';
import LoadingScreen from '../components/common/LoadingScreen';
import { useAuth } from '../contexts/AuthContext';
import WorkspaceShell from '../components/workspace/WorkspaceShell';
import MetricCard from '../components/workspace/MetricCard';

// Tab components
import UsersTab from '../components/admin/tabs/UsersTab';
import CandidatesTab from '../components/admin/tabs/CandidatesTab';
import AbsenceTab from '../components/admin/tabs/AbsenceTab';
import EmailLogsTab from '../components/admin/tabs/EmailLogsTab';
import JobPostingsTab from '../components/admin/tabs/JobPostingsTab';
import BulkUploadTab from '../components/admin/tabs/BulkUploadTab';
import QuestionBankTab from '../components/admin/tabs/QuestionBankTab';
import AnalyticsTab from '../components/admin/tabs/AnalyticsTab';
import AuditLogTab from '../components/admin/tabs/AuditLogTab';

// Modal components
import UserModal from '../components/admin/modals/UserModal';
import CandidateModal from '../components/admin/modals/CandidateModal';
import JobModal from '../components/admin/modals/JobModal';
import SectorModal from '../components/admin/modals/SectorModal';

const AdminDashboardPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { signOut, user } = useAuth();

  // All privileged data is loaded through the authenticated backend API.
  const [users, setUsers] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [jobPostings, setJobPostings] = useState([]);

  const [dbStats, setDbStats] = useState(null);
  const [emailLogs, setEmailLogs] = useState([]);
  const [jobModalOpen, setJobModalOpen] = useState(false);
  const [jobForm, setJobForm] = useState({
    title: '', description: '', required_skills: '', preferred_skills: '',
    min_experience: 0, max_experience: '', department: '', work_mode: 'On-Site',
    sector_id: '', status: 'active', employment_type: 'full-time',
    experience_level: 'mid', salary_range: '', closes_at: '',
    role_complexity_level: 'intermediate'
  });
  const [editingJob, setEditingJob] = useState(null);
  const [sectors, setSectors] = useState([]);
  const [sectorModalOpen, setSectorModalOpen] = useState(false);
  const [sectorForm, setSectorForm] = useState({ name: '', description: '', email_alias: '' });
  const [matchingCandidate, setMatchingCandidate] = useState(null);
  const [jobCandidates, setJobCandidates] = useState([]);
  const [selectedJobForCandidates, setSelectedJobForCandidates] = useState(null);
  const [reviewingMatch, setReviewingMatch] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [analytics, setAnalytics] = useState({ candidates: {}, assessments: {} });
  const [loading, setLoading] = useState(true);
  const fetchAllDataRef = useRef(null);

  // Modals
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({ name: '', email: '', password: '', role: 'interviewer', sector_id: '' });

  const [candidateModalOpen, setCandidateModalOpen] = useState(false);
  const [editingCandidate, setEditingCandidate] = useState(null);
  const [candidateForm, setCandidateForm] = useState({ name: '', email: '', phone: '', status: 'applied', match_score: 0 });

  // Button loading states
  const [savingUser, setSavingUser] = useState(false);
  const [deletingUser, setDeletingUser] = useState(null);
  const [savingCandidate, setSavingCandidate] = useState(false);
  const [deletingCandidate, setDeletingCandidate] = useState(null);
  const [resettingStatus, setResettingStatus] = useState(null);
  const [savingJob, setSavingJob] = useState(false);
  const [deletingJob, setDeletingJob] = useState(null);
  const [enhancingJob, setEnhancingJob] = useState(false);
  const [enhancingSector, setEnhancingSector] = useState(false);
  const [expandedJob, setExpandedJob] = useState(null);

  // Search & Filter State
  const [userSearch, setUserSearch] = useState('');
  const [candidateSearch, setCandidateSearch] = useState('');
  const [candidateStatusFilter, setCandidateStatusFilter] = useState('all');

  // Bulk Upload State
  const [bulkFile, setBulkFile] = useState(null);
  const [bulkJobId, setBulkJobId] = useState('');
  const [bulkUploading, setBulkUploading] = useState(false);
  const [bulkProgress, setBulkProgress] = useState(null);
  const [bulkResults, setBulkResults] = useState(null);

  // Absence of Details State
  const [absenceCandidates, setAbsenceCandidates] = useState([]);
  const [absenceLoading, setAbsenceLoading] = useState(false);
  const [absenceEditing, setAbsenceEditing] = useState(null);
  const [absenceForm, setAbsenceForm] = useState({ name: '', email: '', phone: '' });
  const [absenceSaving, setAbsenceSaving] = useState(false);

  // Question Bank State
  const [questionBanks, setQuestionBanks] = useState([]);
  const [qbLoading, setQbLoading] = useState(false);
  const [qbUploading, setQbUploading] = useState(false);
  const [qbFile, setQbFile] = useState(null);
  const [qbDescription, setQbDescription] = useState('');
  const [qbTags, setQbTags] = useState('');
  const [qbPreview, setQbPreview] = useState(null);
  const [qbPreviewLoading, setQbPreviewLoading] = useState(false);

  // Memoized filtered data
  const filteredUsers = useMemo(() => {
    const query = userSearch.trim().toLowerCase();
    return users.filter(user =>
      String(user.name || '').toLowerCase().includes(query) ||
      String(user.email || '').toLowerCase().includes(query)
    );
  }, [users, userSearch]);

  const filteredCandidates = useMemo(() => {
    const query = candidateSearch.trim().toLowerCase();
    return candidates.filter(candidate => {
      const matchesSearch = String(candidate.name || '').toLowerCase().includes(query) ||
        String(candidate.email || '').toLowerCase().includes(query);
      const matchesStatus = candidateStatusFilter === 'all' || (candidate.status || 'applied') === candidateStatusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [candidates, candidateSearch, candidateStatusFilter]);

  const candidateStatuses = useMemo(() => {
    return [...new Set(candidates.map(c => c.status || 'applied'))];
  }, [candidates]);

  useEffect(() => {
    fetchAllDataRef.current?.();
  }, []);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    try {
      const [usersRes, candidatesRes, statsRes, jobsRes, sectorsRes] = await Promise.all([
        api.get('/api/admin/users'),
        api.get('/api/admin/candidates'),
        api.get('/api/admin/db/stats'),
        api.get('/api/jobs/postings?status=all').catch(() => ({ data: { data: [] } })),
        api.get('/api/jobs/sectors').catch(() => ({ data: { data: [] } }))
      ]);

      // Set initial data for realtime hooks
      setUsers(usersRes.data.data || []);
      setCandidates(candidatesRes.data.data || []);
      setJobPostings(jobsRes.data.data || []);
      setSectors(sectorsRes.data.data || []);

      // Set non-realtime data
      setDbStats(statsRes.data.data || {});
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to load admin data';
      if (err?.response?.status === 403) {
        toast({ variant: 'destructive', title: 'Access Denied', description: 'Admin role required' });
        navigate('/dashboard');
      } else {
        toast({ variant: 'destructive', title: 'Error', description: message });
      }
    } finally {
      setLoading(false);
    }
  }, [navigate, setCandidates, setJobPostings, setUsers, toast]);
  fetchAllDataRef.current = fetchAllData;

  const handleLogout = () => {
    signOut();
    navigate('/login');
  };

  // User Management
  const handleSaveUser = async () => {
    setSavingUser(true);
    try {
      if (editingUser) {
        await api.put(`/api/admin/users/${editingUser.id}`, userForm);
        toast({ title: 'Success', description: 'User updated successfully' });
      } else {
        await api.post('/api/admin/users', userForm);
        toast({ title: 'Success', description: 'User created successfully' });
      }
      setUserModalOpen(false);
      setEditingUser(null);
      setUserForm({ name: '', email: '', password: '', role: 'interviewer', sector_id: '' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to save user' });
    } finally {
      setSavingUser(false);
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm('Are you sure you want to delete this user?')) return;
    setDeletingUser(userId);
    try {
      await api.delete(`/api/admin/users/${userId}`);
      toast({ title: 'Success', description: 'User deleted successfully' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to delete user' });
    } finally {
      setDeletingUser(null);
    }
  };

  const openEditUser = (user) => {
    setEditingUser(user);
    setUserForm({ name: user.name, email: user.email, password: '', role: user.role, sector_id: user.sector_id || '' });
    setUserModalOpen(true);
  };

  // Candidate Management
  const handleSaveCandidate = async () => {
    setSavingCandidate(true);
    try {
      await api.put(`/api/admin/candidates/${editingCandidate.id}`, candidateForm);
      toast({ title: 'Success', description: 'Candidate updated successfully' });
      setCandidateModalOpen(false);
      setEditingCandidate(null);
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to save candidate' });
    } finally {
      setSavingCandidate(false);
    }
  };

  const handleDeleteCandidate = async (candidateId) => {
    if (!confirm('Are you sure you want to delete this candidate? This will also delete all their assessments.')) return;
    setDeletingCandidate(candidateId);
    try {
      await api.delete(`/api/admin/candidates/${candidateId}`);
      toast({ title: 'Success', description: 'Candidate deleted successfully' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to delete candidate' });
    } finally {
      setDeletingCandidate(null);
    }
  };

  const handleResetCandidateStatus = async (candidateId) => {
    if (!confirm('Reset this candidate status to Applied?')) return;
    setResettingStatus(candidateId);
    try {
      await api.post(`/api/admin/reset-candidate-status/${candidateId}`);
      toast({ title: 'Success', description: 'Candidate status reset to Applied' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to reset status' });
    } finally {
      setResettingStatus(null);
    }
  };

  const openEditCandidate = (candidate) => {
    setEditingCandidate(candidate);
    setCandidateForm({
      name: candidate.name,
      email: candidate.email,
      phone: candidate.phone || '',
      status: candidate.status || 'applied',
      match_score: candidate.match_score || 0
    });
    setCandidateModalOpen(true);
  };

  const fetchEmailLogs = async () => {
    try {
      const res = await api.get('/api/admin/email-logs');
      setEmailLogs(res.data.data || []);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load email logs' });
    }
  };

  // ── Absence of Details Handlers ──
  const fetchAbsenceCandidates = async () => {
    setAbsenceLoading(true);
    try {
      const res = await api.get('/api/admin/absence-of-details');
      setAbsenceCandidates(res.data.data || []);
    } catch {
      toast({ variant: 'destructive', title: 'Unable to load candidates', description: 'Missing-detail records could not be retrieved.' });
    } finally {
      setAbsenceLoading(false);
    }
  };

  const startEditAbsence = (candidate) => {
    setAbsenceEditing(candidate.id);
    setAbsenceForm({ name: candidate.name || '', email: candidate.email || '', phone: candidate.phone || '' });
  };

  const cancelEditAbsence = () => {
    setAbsenceEditing(null);
    setAbsenceForm({ name: '', email: '', phone: '' });
  };

  const saveAbsenceDetails = async (candidateId) => {
    if (!absenceForm.name?.trim() || !absenceForm.email?.trim()) {
      toast({ variant: 'destructive', title: 'Name and Email are required' });
      return;
    }
    setAbsenceSaving(true);
    try {
      await api.put(`/api/admin/candidates/${candidateId}`, {
        name: absenceForm.name.trim(),
        email: absenceForm.email.trim(),
        phone: absenceForm.phone?.trim() || '',
        status: 'applied'
      });
      toast({ title: 'Candidate updated', description: 'Status changed to Applied' });
      setAbsenceEditing(null);
      fetchAbsenceCandidates();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Update failed', description: err?.response?.data?.message || 'Error' });
    } finally {
      setAbsenceSaving(false);
    }
  };

  // ── Question Bank Functions ──
  const fetchQuestionBanks = async () => {
    setQbLoading(true);
    try {
      const res = await api.get('/api/admin/question-bank');
      setQuestionBanks(res.data.data || []);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load question banks' });
    } finally {
      setQbLoading(false);
    }
  };

  const handleQbUpload = async () => {
    if (!qbFile) {
      toast({ variant: 'destructive', title: 'No file', description: 'Please select a PDF or DOCX file' });
      return;
    }
    setQbUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', qbFile);
      formData.append('description', qbDescription);
      formData.append('tags', qbTags);
      const res = await api.post('/api/admin/question-bank/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast({
        title: 'Uploaded',
        description: res.data.message || 'Question bank uploaded successfully'
      });
      setQbFile(null);
      setQbDescription('');
      setQbTags('');
      fetchQuestionBanks();
    } catch (err) {
      const msg = err?.response?.data?.message || 'Upload failed';
      toast({ variant: 'destructive', title: 'Upload Error', description: msg });
    } finally {
      setQbUploading(false);
    }
  };

  const handleQbDelete = async (id) => {
    if (!window.confirm('Permanently delete this question bank?')) return;
    try {
      await api.delete(`/api/admin/question-bank/${id}`);
      setQuestionBanks(prev => prev.filter(q => q.id !== id));
      toast({ title: 'Deleted', description: 'Question bank removed' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to delete' });
    }
  };

  const handleQbToggle = async (id) => {
    try {
      const res = await api.patch(`/api/admin/question-bank/${id}/toggle`);
      setQuestionBanks(prev => prev.map(q => q.id === id ? { ...q, is_active: res.data.is_active } : q));
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to toggle status' });
    }
  };

  const handleQbPreview = async (id) => {
    if (qbPreview?.id === id) { setQbPreview(null); return; }
    setQbPreviewLoading(true);
    try {
      const res = await api.get(`/api/admin/question-bank/${id}`);
      setQbPreview(res.data.data);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load preview' });
    } finally {
      setQbPreviewLoading(false);
    }
  };

  const fetchJobPostings = async () => {
    try {
      const res = await api.get('/api/jobs/postings?status=all');
      setJobPostings(res.data.data || []);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load job postings' });
    }
  };

  const fetchSectors = async () => {
    try {
      const res = await api.get('/api/jobs/sectors');
      setSectors(res.data.data || []);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load sectors' });
    }
  };

  const handleSaveSector = async () => {
    try {
      await api.post('/api/jobs/sectors', sectorForm);
      toast({ title: 'Success', description: 'Sector created successfully' });
      setSectorModalOpen(false);
      setSectorForm({ name: '', description: '', email_alias: '' });
      fetchSectors();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to create sector' });
    }
  };

  const handleMatchCandidate = async (candidateId) => {
    setMatchingCandidate(candidateId);
    try {
      const res = await api.post('/api/jobs/match-candidate', { candidate_id: candidateId });
      const matches = res.data.data?.matches || [];
      toast({
        title: 'AI Matching Complete',
        description: `Found ${matches.length} job match(es). Best: ${matches[0]?.job_title || 'N/A'} (${matches[0]?.match_score || 0}%)`,
      });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Matching Failed', description: err?.response?.data?.message || 'Could not match candidate' });
    } finally {
      setMatchingCandidate(null);
    }
  };

  const fetchJobCandidates = async (jobId) => {
    try {
      setSelectedJobForCandidates(jobId);
      const res = await api.get(`/api/jobs/postings/${jobId}/candidates`);
      setJobCandidates(res.data.data || []);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load matched candidates' });
    }
  };

  const handleReviewCandidateMatch = async (candidateId, jobId, status) => {
    const reviewKey = `${candidateId}:${jobId}`;
    setReviewingMatch(reviewKey);
    try {
      await api.patch(`/api/jobs/matches/${candidateId}/${jobId}`, { status });
      toast({ title: 'Match reviewed', description: `Candidate match ${status}.` });
      await fetchJobCandidates(jobId);
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Review failed',
        description: err?.response?.data?.message || 'Could not save the match decision',
      });
    } finally {
      setReviewingMatch(null);
    }
  };

  const fetchAuditLog = async () => {
    try {
      const res = await api.get('/api/jobs/audit-log?limit=50');
      setAuditLogs(res.data.data || []);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load audit log' });
    }
  };

  const handleSaveJob = async () => {
    if (!jobForm.required_skills || !jobForm.required_skills.trim()) {
      toast({ variant: 'destructive', title: 'Validation Error', description: 'Required skills must be specified for the job posting' });
      return;
    }
    setSavingJob(true);
    try {
      const payload = {
        ...jobForm,
        min_experience: parseInt(jobForm.min_experience) || 0,
        max_experience: jobForm.max_experience ? parseInt(jobForm.max_experience) : null,
        sector_id: jobForm.sector_id && jobForm.sector_id !== 'none' ? parseInt(jobForm.sector_id) : null,
        closes_at: jobForm.closes_at || null
      };
      if (editingJob) {
        await api.put(`/api/jobs/postings/${editingJob.id}`, payload);
        toast({ title: 'Success', description: 'Job posting updated successfully' });
      } else {
        await api.post('/api/jobs/postings', payload);
        toast({ title: 'Success', description: 'Job posting created successfully' });
      }
      setJobModalOpen(false);
      setEditingJob(null);
      setJobForm({
        title: '', description: '', required_skills: '', preferred_skills: '',
        min_experience: 0, max_experience: '', department: '', work_mode: 'On-Site',
        sector_id: '', status: 'active', employment_type: 'full-time',
        experience_level: 'mid', salary_range: '', closes_at: '',
        role_complexity_level: 'intermediate'
      });
      fetchJobPostings();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to save job' });
    } finally {
      setSavingJob(false);
    }
  };

  const openEditJob = (job) => {
    setEditingJob(job);
    setJobForm({
      title: job.title || '', description: job.description || '',
      required_skills: job.required_skills || '', preferred_skills: job.preferred_skills || '',
      min_experience: job.min_experience || 0, max_experience: job.max_experience || '',
      department: job.department || '', work_mode: job.work_mode || 'On-Site',
      sector_id: job.sector_id ? String(job.sector_id) : '',
      status: job.status || 'active', employment_type: job.employment_type || 'full-time',
      experience_level: job.experience_level || 'mid', salary_range: job.salary_range || '',
      closes_at: toJobClosingInputValue(job.closes_at),
      role_complexity_level: job.role_complexity_level || 'intermediate'
    });
    setJobModalOpen(true);
  };

  const handleDeleteJob = async (jobId) => {
    if (!confirm('Remove this job posting? Jobs with hiring history will be closed and preserved.')) return;
    setDeletingJob(jobId);
    try {
      const response = await api.delete(`/api/jobs/postings/${jobId}`);
      toast({
        title: response.data?.data?.action === 'archived' ? 'Job closed' : 'Job removed',
        description: response.data?.message || 'Job posting updated',
      });
      fetchJobPostings();
    } catch (err) {
      toast({
        variant: 'destructive',
        title: 'Unable to remove job',
        description: err?.response?.data?.message || 'Please try again.',
      });
    } finally {
      setDeletingJob(null);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const res = await api.get('/api/admin/analytics');
      setAnalytics(res.data.data || { candidates: {}, assessments: {} });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load analytics' });
    }
  };

  if (loading) {
    return <LoadingScreen message="Loading Admin Dashboard" />;
  }

  return (
    <WorkspaceShell
      role="admin"
      title="Hiring operations"
      description="Manage staff access, applicants, open roles, assessment content, and the system audit trail."
      user={user}
      onRefresh={fetchAllData}
      refreshing={loading}
      onSignOut={handleLogout}
    >
        <div className="mb-6 grid gap-4 sm:grid-cols-3">
          <MetricCard label="Staff accounts" value={dbStats?.total_users || 0} hint="All authorized users" icon={Users} />
          <MetricCard label="Candidates" value={dbStats?.total_candidates || 0} hint="Across the hiring lifecycle" icon={UserPlus} tone="success" />
          <MetricCard label="Assessments" value={dbStats?.total_assessments || 0} hint="Created assessment sessions" icon={BarChart3} tone="neutral" />
        </div>

        {/* Main Tabs */}
        <Tabs defaultValue="users" className="space-y-5">
          <TabsList className="w-full justify-start" aria-label="Admin workspace sections">
            <TabsTrigger value="users">
              <Users className="mr-2 h-4 w-4" />
              Staff
            </TabsTrigger>
            <TabsTrigger value="candidates">
              <UserPlus className="mr-2 h-4 w-4" />
              Candidates
            </TabsTrigger>
            <TabsTrigger value="absence-details" onClick={fetchAbsenceCandidates}>
              <AlertTriangle className="mr-2 h-4 w-4" />
              Missing details
            </TabsTrigger>
            <TabsTrigger value="email-logs" onClick={fetchEmailLogs}>
              <Mail className="mr-2 h-4 w-4" />
              Email activity
            </TabsTrigger>
            <TabsTrigger value="job-postings" onClick={fetchJobPostings}>
              <Briefcase className="mr-2 h-4 w-4" />
              Roles
            </TabsTrigger>
            <TabsTrigger value="bulk-upload" onClick={fetchJobPostings}>
              <Upload className="mr-2 h-4 w-4" />
              Resume import
            </TabsTrigger>
            <TabsTrigger value="question-bank" onClick={fetchQuestionBanks}>
              <BookOpen className="mr-2 h-4 w-4" />
              Questions
            </TabsTrigger>
            <TabsTrigger value="analytics" onClick={fetchAnalytics}>
              <BarChart3 className="mr-2 h-4 w-4" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="audit-log" onClick={fetchAuditLog}>
              <Shield className="mr-2 h-4 w-4" />
              Audit trail
            </TabsTrigger>
          </TabsList>

          <UsersTab
            filteredUsers={filteredUsers}
            userSearch={userSearch}
            setUserSearch={setUserSearch}
            deletingUser={deletingUser}
            openEditUser={openEditUser}
            handleDeleteUser={handleDeleteUser}
            setEditingUser={setEditingUser}
            setUserForm={setUserForm}
            setUserModalOpen={setUserModalOpen}
            currentUserRole={user?.role}
          />

          <CandidatesTab
            filteredCandidates={filteredCandidates}
            candidateSearch={candidateSearch}
            setCandidateSearch={setCandidateSearch}
            candidateStatusFilter={candidateStatusFilter}
            setCandidateStatusFilter={setCandidateStatusFilter}
            candidateStatuses={candidateStatuses}
            deletingCandidate={deletingCandidate}
            resettingStatus={resettingStatus}
            matchingCandidate={matchingCandidate}
            openEditCandidate={openEditCandidate}
            handleResetCandidateStatus={handleResetCandidateStatus}
            handleMatchCandidate={handleMatchCandidate}
            handleDeleteCandidate={handleDeleteCandidate}
          />

          <AbsenceTab
            absenceCandidates={absenceCandidates}
            absenceLoading={absenceLoading}
            absenceEditing={absenceEditing}
            absenceForm={absenceForm}
            setAbsenceForm={setAbsenceForm}
            absenceSaving={absenceSaving}
            fetchAbsenceCandidates={fetchAbsenceCandidates}
            startEditAbsence={startEditAbsence}
            cancelEditAbsence={cancelEditAbsence}
            saveAbsenceDetails={saveAbsenceDetails}
            handleDeleteCandidate={handleDeleteCandidate}
          />

          <EmailLogsTab
            emailLogs={emailLogs}
          />

          <JobPostingsTab
            jobPostings={jobPostings}
            sectors={sectors}
            expandedJob={expandedJob}
            setExpandedJob={setExpandedJob}
            deletingJob={deletingJob}
            selectedJobForCandidates={selectedJobForCandidates}
            jobCandidates={jobCandidates}
            setSectorModalOpen={setSectorModalOpen}
            setEditingJob={setEditingJob}
            setJobForm={setJobForm}
            setJobModalOpen={setJobModalOpen}
            openEditJob={openEditJob}
            handleDeleteJob={handleDeleteJob}
            fetchJobCandidates={fetchJobCandidates}
            handleReviewCandidateMatch={handleReviewCandidateMatch}
            reviewingMatch={reviewingMatch}
          />

          <BulkUploadTab
            jobPostings={jobPostings}
            bulkFile={bulkFile}
            setBulkFile={setBulkFile}
            bulkJobId={bulkJobId}
            setBulkJobId={setBulkJobId}
            bulkUploading={bulkUploading}
            setBulkUploading={setBulkUploading}
            bulkProgress={bulkProgress}
            setBulkProgress={setBulkProgress}
            bulkResults={bulkResults}
            setBulkResults={setBulkResults}
          />

          <QuestionBankTab
            questionBanks={questionBanks}
            qbLoading={qbLoading}
            qbUploading={qbUploading}
            qbFile={qbFile}
            setQbFile={setQbFile}
            qbDescription={qbDescription}
            setQbDescription={setQbDescription}
            qbTags={qbTags}
            setQbTags={setQbTags}
            qbPreview={qbPreview}
            qbPreviewLoading={qbPreviewLoading}
            fetchQuestionBanks={fetchQuestionBanks}
            handleQbUpload={handleQbUpload}
            handleQbDelete={handleQbDelete}
            handleQbToggle={handleQbToggle}
            handleQbPreview={handleQbPreview}
          />

          <AnalyticsTab
            analytics={analytics}
          />

          <AuditLogTab
            auditLogs={auditLogs}
          />

        </Tabs>

      <UserModal
        userModalOpen={userModalOpen}
        setUserModalOpen={setUserModalOpen}
        editingUser={editingUser}
        userForm={userForm}
        setUserForm={setUserForm}
        savingUser={savingUser}
        handleSaveUser={handleSaveUser}
        sectors={sectors}
        currentUserRole={user?.role}
      />

      <CandidateModal
        candidateModalOpen={candidateModalOpen}
        setCandidateModalOpen={setCandidateModalOpen}
        candidateForm={candidateForm}
        setCandidateForm={setCandidateForm}
        savingCandidate={savingCandidate}
        handleSaveCandidate={handleSaveCandidate}
      />

      <JobModal
        jobModalOpen={jobModalOpen}
        setJobModalOpen={setJobModalOpen}
        editingJob={editingJob}
        jobForm={jobForm}
        setJobForm={setJobForm}
        savingJob={savingJob}
        enhancingJob={enhancingJob}
        setEnhancingJob={setEnhancingJob}
        sectors={sectors}
        handleSaveJob={handleSaveJob}
      />

      <SectorModal
        sectorModalOpen={sectorModalOpen}
        setSectorModalOpen={setSectorModalOpen}
        sectorForm={sectorForm}
        setSectorForm={setSectorForm}
        enhancingSector={enhancingSector}
        setEnhancingSector={setEnhancingSector}
        handleSaveSector={handleSaveSector}
      />
    </WorkspaceShell>
  );
};

export default AdminDashboardPage;
