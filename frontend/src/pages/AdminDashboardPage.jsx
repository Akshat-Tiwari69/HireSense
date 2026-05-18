import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Card, CardContent } from '../components/ui/card';
import {
  LogOut, Users, Database, Settings, RefreshCw,
  Shield, UserPlus, BarChart3, Eye, Mail, LayoutDashboard, Briefcase,
  AlertTriangle, Upload, BookOpen
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { api } from '../services/api';
import { useRealtimeTable } from '../hooks/useRealtimeTable';
import RealtimeIndicator from '../components/common/RealtimeIndicator';
import LoadingScreen from '../components/common/LoadingScreen';
import LoadingSpinner from '../components/common/LoadingSpinner';

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
import DatabaseTab from '../components/admin/tabs/DatabaseTab';
import SettingsTab from '../components/admin/tabs/SettingsTab';

// Modal components
import UserModal from '../components/admin/modals/UserModal';
import CandidateModal from '../components/admin/modals/CandidateModal';
import JobModal from '../components/admin/modals/JobModal';
import SectorModal from '../components/admin/modals/SectorModal';

const AdminDashboardPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Realtime subscriptions
  const {
    data: users,
    setData: setUsers,
    isConnected: usersConnected
  } = useRealtimeTable('users', [], {
    onInsert: (newUser) => {
      toast({
        title: " New User Added",
        description: `${newUser.name} (${newUser.role})`,
        duration: 3000
      });
    }
  });

  const {
    data: candidates,
    setData: setCandidates,
    isConnected: candidatesConnected
  } = useRealtimeTable('candidates', [], {
    onInsert: (newCandidate) => {
      toast({
        title: " New Candidate Registered",
        description: `${newCandidate.name} - ${newCandidate.email}`,
        duration: 3000
      });
    }
  });

  const {
    data: jobPostings,
    setData: setJobPostings,
    isConnected: jobsConnected
  } = useRealtimeTable('job_descriptions', [], {
    onInsert: (newJob) => {
      toast({
        title: " New Job Posted",
        description: newJob.title,
        duration: 3000
      });
    }
  });

  // Check if any realtime connection is active
  const isRealtimeConnected = usersConnected || candidatesConnected || jobsConnected;

  // State for other data (non-realtime)
  const [dbStats, setDbStats] = useState(null);
  const [dbTables, setDbTables] = useState([]);
  const [envStatus, setEnvStatus] = useState({});
  const [selectedTable, setSelectedTable] = useState(null);
  const [tableData, setTableData] = useState({ data: [], columns: [] });
  const [emailLogs, setEmailLogs] = useState([]);
  const [jobModalOpen, setJobModalOpen] = useState(false);
  const [jobForm, setJobForm] = useState({
    title: '', description: '', required_skills: '', preferred_skills: '',
    min_experience: 0, max_experience: '', department: '', location: '',
    sector_id: '', status: 'active', employment_type: 'full-time',
    experience_level: 'mid', salary_range: ''
  });
  const [editingJob, setEditingJob] = useState(null);
  const [sectors, setSectors] = useState([]);
  const [sectorModalOpen, setSectorModalOpen] = useState(false);
  const [sectorForm, setSectorForm] = useState({ name: '', description: '', email_alias: '' });
  const [candidateMatches, setCandidateMatches] = useState({});
  const [matchingCandidate, setMatchingCandidate] = useState(null);
  const [jobCandidates, setJobCandidates] = useState([]);
  const [selectedJobForCandidates, setSelectedJobForCandidates] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [analytics, setAnalytics] = useState({ candidates: {}, assessments: {} });
  const [loading, setLoading] = useState(true);

  // Modals
  const [userModalOpen, setUserModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({ name: '', email: '', password: '', role: 'interviewer' });

  const [candidateModalOpen, setCandidateModalOpen] = useState(false);
  const [editingCandidate, setEditingCandidate] = useState(null);
  const [candidateForm, setCandidateForm] = useState({ name: '', email: '', phone: '', status: 'Applied', match_score: 0 });

  // Environment variable editing state
  const [editingEnvVar, setEditingEnvVar] = useState(null);
  const [envVarValue, setEnvVarValue] = useState('');

  // Button loading states
  const [savingUser, setSavingUser] = useState(false);
  const [deletingUser, setDeletingUser] = useState(null);
  const [savingCandidate, setSavingCandidate] = useState(false);
  const [deletingCandidate, setDeletingCandidate] = useState(null);
  const [resettingStatus, setResettingStatus] = useState(null);
  const [savingJob, setSavingJob] = useState(false);
  const [deletingJob, setDeletingJob] = useState(null);
  const [savingEnvVar, setSavingEnvVar] = useState(false);
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
    return users.filter(user =>
      user.name.toLowerCase().includes(userSearch.toLowerCase()) ||
      user.email.toLowerCase().includes(userSearch.toLowerCase())
    );
  }, [users, userSearch]);

  const filteredCandidates = useMemo(() => {
    return candidates.filter(candidate => {
      const matchesSearch = candidate.name.toLowerCase().includes(candidateSearch.toLowerCase()) ||
        candidate.email.toLowerCase().includes(candidateSearch.toLowerCase());
      const matchesStatus = candidateStatusFilter === 'all' || (candidate.status || 'Applied') === candidateStatusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [candidates, candidateSearch, candidateStatusFilter]);

  const candidateStatuses = useMemo(() => {
    return [...new Set(candidates.map(c => c.status || 'Applied'))];
  }, [candidates]);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchAllData();
  }, [navigate]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [usersRes, candidatesRes, statsRes, tablesRes, envRes, jobsRes, sectorsRes] = await Promise.all([
        api.get('/api/admin/users'),
        api.get('/api/admin/candidates'),
        api.get('/api/admin/db/stats'),
        api.get('/api/admin/db/tables'),
        api.get('/api/admin/settings/env'),
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
      setDbTables(tablesRes.data.data || []);
      setEnvStatus(envRes.data.data || {});
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
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
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
      setUserForm({ name: '', email: '', password: '', role: 'interviewer' });
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
    setUserForm({ name: user.name, email: user.email, password: '', role: user.role });
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
    try {
      await api.delete(`/api/admin/candidates/${candidateId}`);
      toast({ title: 'Success', description: 'Candidate deleted successfully' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to delete candidate' });
    }
  };

  const handleResetCandidateStatus = async (candidateId) => {
    if (!confirm('Reset this candidate status to Applied?')) return;
    try {
      await api.post(`/api/admin/reset-candidate-status/${candidateId}`);
      toast({ title: 'Success', description: 'Candidate status reset to Applied' });
      fetchAllData();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to reset status' });
    }
  };

  const openEditCandidate = (candidate) => {
    setEditingCandidate(candidate);
    setCandidateForm({
      name: candidate.name,
      email: candidate.email,
      phone: candidate.phone || '',
      status: candidate.status || 'Applied',
      match_score: candidate.match_score || 0
    });
    setCandidateModalOpen(true);
  };

  // Database
  const fetchTableData = async (tableName) => {
    try {
      setSelectedTable(tableName);
      const res = await api.get(`/api/admin/db/tables/${tableName}`);
      setTableData({ data: res.data.data || [], columns: res.data.columns || [] });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load table data' });
    }
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
    } catch (err) {
      console.error('Failed to fetch absence-of-details:', err);
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
        status: 'Applied'
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
        title: ' Uploaded',
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
      setCandidateMatches(prev => ({ ...prev, [candidateId]: matches }));
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
        sector_id: jobForm.sector_id && jobForm.sector_id !== 'none' ? parseInt(jobForm.sector_id) : null
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
        min_experience: 0, max_experience: '', department: '', location: '',
        sector_id: '', status: 'active', employment_type: 'full-time',
        experience_level: 'mid', salary_range: ''
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
      department: job.department || '', location: job.location || '',
      sector_id: job.sector_id ? String(job.sector_id) : '',
      status: job.status || 'active', employment_type: job.employment_type || 'full-time',
      experience_level: job.experience_level || 'mid', salary_range: job.salary_range || ''
    });
    setJobModalOpen(true);
  };

  const handleDeleteJob = async (jobId) => {
    if (!confirm('Permanently delete this job posting? This cannot be undone.')) return;
    setDeletingJob(jobId);
    try {
      await api.delete(`/api/jobs/postings/${jobId}`);
      toast({ title: 'Success', description: 'Job posting deleted' });
      fetchJobPostings();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to delete job' });
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

  // Environment variable management
  const handleEditEnvVar = (key, currentValue) => {
    setEditingEnvVar(key);
    setEnvVarValue(''); // Don't pre-fill for security
  };

  const handleSaveEnvVar = async () => {
    if (!editingEnvVar) return;

    try {
      await api.post('/api/admin/settings/env', {
        name: editingEnvVar,
        value: envVarValue
      });

      toast({ title: 'Success', description: `${editingEnvVar} updated successfully. Restart backend to apply changes.` });
      setEditingEnvVar(null);
      setEnvVarValue('');
      fetchAllData(); // Refresh to show updated status
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to update environment variable' });
    }
  };

  const handleCancelEdit = () => {
    setEditingEnvVar(null);
    setEnvVarValue('');
  };


  if (loading) {
    return <LoadingScreen message="Loading Admin Dashboard" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Logo size="default" />
            <Badge className="bg-indigo-600 text-white border-indigo-500 shadow-sm">ADMIN</Badge>
          </div>
          <div className="flex gap-2">
            {/* Dashboard Navigation */}
            <Select value="/admin" onValueChange={(val) => navigate(val)}>
              <SelectTrigger className="w-[150px] bg-white border-slate-300 text-slate-700">
                <LayoutDashboard className="w-4 h-4 mr-2" />
                <SelectValue placeholder="Dashboards" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-200">
                <SelectItem value="/dashboard">
                  <div className="flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    Interviewer
                  </div>
                </SelectItem>
                <SelectItem value="/proctor">
                  <div className="flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    Proctor
                  </div>
                </SelectItem>
                <SelectItem value="/admin">
                  <div className="flex items-center gap-2">
                    <Shield className="w-4 h-4" />
                    Admin
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            <RealtimeIndicator isConnected={isRealtimeConnected} />
            <Button variant="outline" onClick={fetchAllData} className="border-slate-300 text-slate-700 hover:bg-slate-50">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button variant="ghost" onClick={handleLogout} className="text-slate-700 hover:text-red-600">
              <LogOut className="mr-2 w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50 border-blue-200 shadow-md hover:shadow-lg transition-all duration-300">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">Total Users</p>
                  <p className="text-4xl font-bold text-slate-900 mt-2">{dbStats?.total_users || 0}</p>
                  <p className="text-xs text-slate-500 mt-2">All system users</p>
                </div>
                <Users className="w-12 h-12 text-blue-400 opacity-80" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-green-100/50 border-green-200 shadow-md hover:shadow-lg transition-all duration-300">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">Total Candidates</p>
                  <p className="text-4xl font-bold text-slate-900 mt-2">{dbStats?.total_candidates || 0}</p>
                  <p className="text-xs text-slate-500 mt-2">Active candidates</p>
                </div>
                <UserPlus className="w-12 h-12 text-green-400 opacity-80" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-purple-100/50 border-purple-200 shadow-md hover:shadow-lg transition-all duration-300">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">Assessments</p>
                  <p className="text-4xl font-bold text-slate-900 mt-2">{dbStats?.total_assessments || 0}</p>
                  <p className="text-xs text-slate-500 mt-2">Total assessments</p>
                </div>
                <BarChart3 className="w-12 h-12 text-purple-400 opacity-80" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-amber-50 to-amber-100/50 border-amber-200 shadow-md hover:shadow-lg transition-all duration-300">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">DB Tables</p>
                  <p className="text-4xl font-bold text-slate-900 mt-2">{dbTables.length}</p>
                  <p className="text-xs text-slate-500 mt-2">Active tables</p>
                </div>
                <Database className="w-12 h-12 text-amber-400 opacity-80" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs defaultValue="users" className="space-y-6">
          <TabsList className="bg-white border-slate-200 shadow-md">
            <TabsTrigger value="users" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700">
              <Users className="w-4 h-4 mr-2" />
              Users
            </TabsTrigger>
            <TabsTrigger value="candidates" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700">
              <UserPlus className="w-4 h-4 mr-2" />
              Candidates
            </TabsTrigger>
            <TabsTrigger value="absence-details" className="data-[state=active]:bg-orange-50 data-[state=active]:text-orange-700" onClick={fetchAbsenceCandidates}>
              <AlertTriangle className="w-4 h-4 mr-2" />
              Absence of Details
            </TabsTrigger>
            <TabsTrigger value="email-logs" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchEmailLogs}>
              <Mail className="w-4 h-4 mr-2" />
              Email Logs
            </TabsTrigger>
            <TabsTrigger value="job-postings" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchJobPostings}>
              <Briefcase className="w-4 h-4 mr-2" />
              Job Postings
            </TabsTrigger>
            <TabsTrigger value="bulk-upload" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchJobPostings}>
              <Upload className="w-4 h-4 mr-2" />
              Bulk Upload
            </TabsTrigger>
            <TabsTrigger value="question-bank" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchQuestionBanks}>
              <BookOpen className="w-4 h-4 mr-2" />
              Question Bank
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchAnalytics}>
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="audit-log" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchAuditLog}>
              <Shield className="w-4 h-4 mr-2" />
              Audit Log
            </TabsTrigger>
            <TabsTrigger value="database" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700">
              <Database className="w-4 h-4 mr-2" />
              Database
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700">
              <Settings className="w-4 h-4 mr-2" />
              Settings
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

          <DatabaseTab
            dbTables={dbTables}
            selectedTable={selectedTable}
            tableData={tableData}
            fetchTableData={fetchTableData}
          />

          <SettingsTab
            envStatus={envStatus}
            editingEnvVar={editingEnvVar}
            envVarValue={envVarValue}
            setEnvVarValue={setEnvVarValue}
            handleEditEnvVar={handleEditEnvVar}
            handleSaveEnvVar={handleSaveEnvVar}
            handleCancelEdit={handleCancelEdit}
          />
        </Tabs>
      </main>

      <UserModal
        userModalOpen={userModalOpen}
        setUserModalOpen={setUserModalOpen}
        editingUser={editingUser}
        userForm={userForm}
        setUserForm={setUserForm}
        savingUser={savingUser}
        handleSaveUser={handleSaveUser}
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
    </div>
  );
};

export default AdminDashboardPage;