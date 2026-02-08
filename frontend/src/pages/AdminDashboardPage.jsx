import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  LogOut, Users, Database, Settings, Trash2, Edit, Plus, RefreshCw,
  Shield, UserPlus, BarChart3, Table as TableIcon, Eye, RotateCcw, Mail, LayoutDashboard, Briefcase,
  TrendingUp, AlertCircle, CheckCircle, Search, Loader2,
  Upload, FileArchive, XCircle, AlertTriangle, CheckCircle2, Sparkles,
  MapPin, IndianRupee, Clock, ChevronDown, ChevronUp, Building2,
  FileText, BookOpen, ToggleLeft, ToggleRight, FileQuestion
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { api } from '../services/api';
import { useRealtimeTable } from '../hooks/useRealtimeTable';
import RealtimeIndicator from '../components/common/RealtimeIndicator';
import LoadingScreen from '../components/common/LoadingScreen';
import LoadingSpinner from '../components/common/LoadingSpinner';

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

          {/* Users Tab */}
          <TabsContent value="users">
            <Card className="bg-white border-none shadow-md hover:shadow-lg transition-all duration-300">
              <CardHeader className="flex flex-row items-center justify-between border-b border-slate-200 pb-4">
                <div>
                  <CardTitle className="text-slate-900">User Management</CardTitle>
                  <CardDescription className="text-slate-600">Manage system users and their roles</CardDescription>
                </div>
                <Button onClick={() => { setEditingUser(null); setUserForm({ name: '', email: '', password: '', role: 'interviewer' }); setUserModalOpen(true); }} className="bg-indigo-600 hover:bg-indigo-700 shadow-md">
                  <Plus className="w-4 h-4 mr-2" />
                  Add User
                </Button>
              </CardHeader>
              <CardContent className="pt-6">
                <div className="mb-4 flex items-center gap-2 bg-slate-50 rounded-lg p-3">
                  <Search className="w-4 h-4 text-slate-500" />
                  <Input
                    placeholder="Search users by name or email..."
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    className="bg-transparent border-0 focus:ring-0 text-slate-900 placeholder:text-slate-500"
                  />
                </div>

                {filteredUsers.length === 0 ? (
                  <div className="text-center py-12">
                    <Users className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <p className="text-slate-500">No users found</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-200 bg-slate-50 hover:bg-slate-50">
                          <TableHead className="text-slate-700 font-semibold">Name</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Email</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Role</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredUsers.map((user) => (
                          <TableRow key={user.id} className="border-slate-100 hover:bg-slate-50 transition-colors">
                            <TableCell className="text-slate-900 font-medium">{user.name}</TableCell>
                            <TableCell className="text-slate-600">{user.email}</TableCell>
                            <TableCell>
                              <Badge className={`${
                                user.role === 'admin' ? 'bg-red-600' :
                                  user.role === 'proctor' ? 'bg-purple-600' :
                                    'bg-blue-600'
                              } text-white shadow-sm`}>
                                {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-2">
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  onClick={() => openEditUser(user)} 
                                  className="border-slate-300 text-slate-700 hover:bg-slate-50"
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant="destructive" 
                                  onClick={() => handleDeleteUser(user.id)}
                                  disabled={deletingUser === user.id}
                                  className="opacity-90 hover:opacity-100"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Candidates Tab */}
          <TabsContent value="candidates">
            <Card className="bg-white border-none shadow-md hover:shadow-lg transition-all duration-300">
              <CardHeader className="flex flex-row items-center justify-between border-b border-slate-200 pb-4">
                <div>
                  <CardTitle className="text-slate-900">Candidate Management</CardTitle>
                  <CardDescription className="text-slate-600">View, edit, or manage candidate applications</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="pt-6">                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-6">
                  <div className="col-span-2 flex items-center gap-2 bg-slate-50 rounded-lg p-3">
                    <Search className="w-4 h-4 text-slate-500" />
                    <Input
                      placeholder="Search candidates..."
                      value={candidateSearch}
                      onChange={(e) => setCandidateSearch(e.target.value)}
                      className="bg-transparent border-0 focus:ring-0 text-slate-900 placeholder:text-slate-500"
                    />
                  </div>
                  <Select value={candidateStatusFilter} onValueChange={setCandidateStatusFilter}>
                    <SelectTrigger className="bg-slate-50 border-slate-200">
                      <SelectValue placeholder="Filter by status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Statuses</SelectItem>
                      {candidateStatuses.map(status => (
                        <SelectItem key={status} value={status}>{status}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {filteredCandidates.length === 0 ? (
                  <div className="text-center py-12">
                    <UserPlus className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <p className="text-slate-500">No candidates found</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-200 bg-slate-50 hover:bg-slate-50">
                          <TableHead className="text-slate-700 font-semibold">Name</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Email</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Score</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Status</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredCandidates.map((candidate) => (
                          <TableRow key={candidate.id} className="border-slate-100 hover:bg-slate-50 transition-colors">
                            <TableCell className="text-slate-900 font-medium">{candidate.name}</TableCell>
                            <TableCell className="text-slate-600">{candidate.email}</TableCell>
                            <TableCell>
                              <span className={`font-semibold ${
                                (candidate.match_score || 0) >= 75 ? 'text-green-600' :
                                (candidate.match_score || 0) >= 50 ? 'text-amber-600' :
                                'text-slate-600'
                              }`}>
                                {candidate.match_score || 0}%
                              </span>
                            </TableCell>
                            <TableCell>
                              <Badge className={`${
                                candidate.status === 'Applied' ? 'bg-blue-600' :
                                  candidate.status === 'Scheduled' ? 'bg-purple-600' :
                                    candidate.status === 'Completed' ? 'bg-green-600' :
                                      candidate.status === 'Rejected' ? 'bg-red-600' : 'bg-slate-600'
                              } text-white shadow-sm`}>
                                {(candidate.status || 'Applied').charAt(0).toUpperCase() + (candidate.status || 'Applied').slice(1)}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <div className="flex gap-2">
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  onClick={() => openEditCandidate(candidate)} 
                                  className="border-slate-300 text-slate-700 hover:bg-slate-50"
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  onClick={() => handleResetCandidateStatus(candidate.id)}
                                  disabled={resettingStatus === candidate.id}
                                  className="border-amber-600 text-amber-600 hover:bg-amber-50"
                                >
                                  <RotateCcw className="w-4 h-4" />
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant="outline" 
                                  onClick={() => handleMatchCandidate(candidate.id)}
                                  disabled={matchingCandidate === candidate.id}
                                  className="border-indigo-600 text-indigo-600 hover:bg-indigo-50"
                                  title="AI Match to Jobs"
                                >
                                  {matchingCandidate === candidate.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Briefcase className="w-4 h-4" />}
                                </Button>
                                <Button 
                                  size="sm" 
                                  variant="destructive" 
                                  onClick={() => handleDeleteCandidate(candidate.id)}
                                  disabled={deletingCandidate === candidate.id}
                                  className="opacity-90 hover:opacity-100"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Absence of Details Tab */}
          <TabsContent value="absence-details">
            <Card className="bg-white border-none shadow-md">
              <CardHeader className="border-b border-slate-200 pb-4 flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2 text-slate-900">
                    <AlertTriangle className="w-5 h-5 text-orange-500" />
                    Candidates with Missing Details ({absenceCandidates.length})
                  </CardTitle>
                  <CardDescription className="text-slate-600">These candidates were uploaded but had critical information missing from their resume. Click Edit to fill in the details and move them to Applied status.</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={fetchAbsenceCandidates} disabled={absenceLoading}>
                  <RefreshCw className={`w-4 h-4 mr-1 ${absenceLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </CardHeader>
              <CardContent className="pt-4">
                {absenceLoading ? (
                  <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-orange-500" /></div>
                ) : absenceCandidates.length === 0 ? (
                  <div className="text-center py-12 text-slate-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-300" />
                    <p className="font-medium text-green-700">All good!</p>
                    <p className="text-sm mt-1">No candidates with missing details</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {absenceCandidates.map(c => (
                      <div key={c.id} className="border border-orange-200 rounded-lg p-4 bg-orange-50/30 hover:shadow-md transition-all">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start gap-3 flex-1">
                            <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center text-orange-600 font-bold text-sm">
                              #{c.id}
                            </div>
                            <div className="flex-1">
                              {absenceEditing === c.id ? (
                                <div className="space-y-3">
                                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                    <div className="space-y-1">
                                      <Label className="text-xs font-medium text-slate-600">Name *</Label>
                                      <Input
                                        value={absenceForm.name}
                                        onChange={e => setAbsenceForm(f => ({ ...f, name: e.target.value }))}
                                        placeholder="Full name"
                                        className={`h-8 text-sm ${c.missing_fields?.includes('name') ? 'border-orange-300 bg-orange-50' : ''}`}
                                      />
                                    </div>
                                    <div className="space-y-1">
                                      <Label className="text-xs font-medium text-slate-600">Email *</Label>
                                      <Input
                                        value={absenceForm.email}
                                        onChange={e => setAbsenceForm(f => ({ ...f, email: e.target.value }))}
                                        placeholder="email@example.com"
                                        className={`h-8 text-sm ${c.missing_fields?.includes('email') ? 'border-orange-300 bg-orange-50' : ''}`}
                                      />
                                    </div>
                                    <div className="space-y-1">
                                      <Label className="text-xs font-medium text-slate-600">Phone</Label>
                                      <Input
                                        value={absenceForm.phone}
                                        onChange={e => setAbsenceForm(f => ({ ...f, phone: e.target.value }))}
                                        placeholder="+91 98765 43210"
                                        className="h-8 text-sm"
                                      />
                                    </div>
                                  </div>
                                  <div className="flex gap-2">
                                    <Button size="sm" onClick={() => saveAbsenceDetails(c.id)} disabled={absenceSaving}
                                      className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 h-7 text-xs">
                                      {absenceSaving ? <Loader2 className="w-3 h-3 animate-spin mr-1" /> : <CheckCircle className="w-3 h-3 mr-1" />}
                                      Save & Mark Applied
                                    </Button>
                                    <Button variant="ghost" size="sm" onClick={cancelEditAbsence} className="h-7 text-xs">Cancel</Button>
                                  </div>
                                </div>
                              ) : (
                                <div>
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <span className="font-semibold text-slate-800">{c.name}</span>
                                    <span className="text-sm text-slate-500">{c.email}</span>
                                    {c.job_title && c.job_title !== 'N/A' && (
                                      <Badge variant="outline" className="text-xs border-indigo-200 text-indigo-600">{c.job_title}</Badge>
                                    )}
                                    {c.match_score > 0 && (
                                      <Badge variant="outline" className="text-xs">{c.match_score}% match</Badge>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                                    <span className="text-xs font-medium text-orange-700">Missing:</span>
                                    {c.missing_fields?.map(field => (
                                      <Badge key={field} className="bg-orange-100 text-orange-800 text-xs capitalize hover:bg-orange-100">
                                        {field}
                                      </Badge>
                                    ))}
                                    {c.created_at && (
                                      <span className="text-xs text-slate-400 ml-2">
                                        Uploaded {new Date(c.created_at).toLocaleDateString()}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                          {absenceEditing !== c.id && (
                            <div className="flex items-center gap-1 ml-3">
                              <Button variant="outline" size="sm" onClick={() => startEditAbsence(c)}
                                className="h-8 text-xs border-orange-200 text-orange-700 hover:bg-orange-50">
                                <Edit className="w-3.5 h-3.5 mr-1" />
                                Edit & Fix
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleDeleteCandidate(c.id)}
                                className="h-8 text-xs hover:text-red-600" title="Delete candidate">
                                <Trash2 className="w-3.5 h-3.5" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Email Logs Tab */}
          <TabsContent value="email-logs">
            <Card className="bg-white border-none shadow-md hover:shadow-lg transition-all duration-300">
              <CardHeader>
                <CardTitle className="text-slate-900">Email Logs</CardTitle>
                <CardDescription className="text-slate-600">History of system emails sent to candidates and users</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-200">
                      <TableHead className="text-slate-700">Time</TableHead>
                      <TableHead className="text-slate-700">Recipient</TableHead>
                      <TableHead className="text-slate-700">Type</TableHead>
                      <TableHead className="text-slate-700">Subject</TableHead>
                      <TableHead className="text-slate-700">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {emailLogs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-slate-500">
                          No email logs found
                        </TableCell>
                      </TableRow>
                    ) : (
                      emailLogs.map((log) => (
                        <TableRow key={log.id} className="border-slate-200">
                          <TableCell className="text-slate-600 text-xs">
                            {new Date(log.sent_at).toLocaleString()}
                          </TableCell>
                          <TableCell className="text-slate-700">
                            <div className="flex flex-col">
                              <span className="text-slate-900">{log.recipient_name}</span>
                              <span className="text-xs text-slate-500">{log.recipient_email}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-slate-700">
                            <Badge variant="outline" className="border-slate-300 text-slate-700">
                              {log.email_type
                                ? log.email_type
                                  .split('_')
                                  .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                                  .join(' ')
                                : 'Unknown'}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-slate-700 max-w-xs truncate" title={log.subject}>
                            {log.subject}
                          </TableCell>
                          <TableCell>
                            {log.status === 'sent' ? (
                              <Badge className="bg-green-900 text-green-200 hover:bg-green-800">
                                Sent
                              </Badge>
                            ) : (
                              <div className="flex flex-col items-start gap-1">
                                <Badge className="bg-red-900 text-red-200 hover:bg-red-800">
                                  Failed
                                </Badge>
                                <span className="text-xs text-red-400 max-w-[150px] truncate" title={log.error_message}>
                                  {log.error_message}
                                </span>
                              </div>
                            )}
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Database Tab */}
          <TabsContent value="database">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
                <CardHeader>
                  <CardTitle className="text-slate-900 text-lg">Tables</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {dbTables.map((table) => (
                    <Button
                      key={table}
                      variant={selectedTable === table ? 'default' : 'outline'}
                      className={`w-full justify-start ${selectedTable === table ? 'bg-indigo-600' : 'border-slate-300 text-slate-700 hover:bg-slate-50'}`}
                      onClick={() => fetchTableData(table)}
                    >
                      <TableIcon className="w-4 h-4 mr-2" />
                      {table}
                    </Button>
                  ))}
                </CardContent>
              </Card>

              <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 lg:col-span-3">
                <CardHeader>
                  <CardTitle className="text-slate-900">
                    {selectedTable ? `Table: ${selectedTable}` : 'Select a table'}
                  </CardTitle>
                  <CardDescription className="text-slate-600">
                    {selectedTable ? `Showing ${tableData.data.length} rows` : 'Click a table to view its data'}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {selectedTable && tableData.columns.length > 0 ? (
                    <div className="overflow-x-auto">
                      <Table>
                        <TableHeader>
                          <TableRow className="border-slate-200">
                            {tableData.columns.map((col) => (
                              <TableHead key={col} className="text-slate-700 whitespace-nowrap">{col}</TableHead>
                            ))}
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {tableData.data.map((row, idx) => (
                            <TableRow key={idx} className="border-slate-200">
                              {tableData.columns.map((col) => (
                                <TableCell key={col} className="text-slate-700 max-w-xs truncate">
                                  {row[col] !== null ? String(row[col]).substring(0, 50) : 'NULL'}
                                  {String(row[col] || '').length > 50 && '...'}
                                </TableCell>
                              ))}
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </div>
                  ) : (
                    <p className="text-slate-600 text-center py-8">Select a table from the left to view its data</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Job Postings Tab */}
          <TabsContent value="job-postings">
            <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-slate-900">Job Postings</CardTitle>
                  <CardDescription className="text-slate-600">Manage job openings with required/preferred skills. AI will match candidates to the best-fit role.</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setSectorModalOpen(true)} className="border-slate-300 text-slate-700">
                    <Plus className="w-4 h-4 mr-2" />
                    Add Sector
                  </Button>
                  <Button onClick={() => { setEditingJob(null); setJobForm({ title: '', description: '', required_skills: '', preferred_skills: '', min_experience: 0, max_experience: '', department: '', location: '', sector_id: '', status: 'active', employment_type: 'full-time', experience_level: 'mid', salary_range: '' }); setJobModalOpen(true); }} className="bg-indigo-600 hover:bg-indigo-700">
                    <Plus className="w-4 h-4 mr-2" />
                    Create Job
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {/* Sectors overview */}
                {sectors.length > 0 && (
                  <div className="mb-6">
                    <p className="text-sm font-semibold text-slate-700 mb-2">Sectors</p>
                    <div className="flex flex-wrap gap-2">
                      {sectors.map(s => (
                        <Badge key={s.id} className="bg-indigo-100 text-indigo-800 border-indigo-200">
                          {s.name} {s.email_alias && <span className="ml-1 opacity-70">({s.email_alias})</span>}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-200">
                      <TableHead className="text-slate-700 w-8"></TableHead>
                      <TableHead className="text-slate-700">Title</TableHead>
                      <TableHead className="text-slate-700">Department</TableHead>
                      <TableHead className="text-slate-700">Sector</TableHead>
                      <TableHead className="text-slate-700">Work Mode</TableHead>
                      <TableHead className="text-slate-700">Level / Type</TableHead>
                      <TableHead className="text-slate-700">Experience</TableHead>
                      <TableHead className="text-slate-700">Salary</TableHead>
                      <TableHead className="text-slate-700">Status</TableHead>
                      <TableHead className="text-slate-700">Candidates</TableHead>
                      <TableHead className="text-slate-700">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobPostings.map((job) => (
                      <React.Fragment key={job.id}>
                        <TableRow className="border-slate-200 cursor-pointer hover:bg-slate-50" onClick={() => setExpandedJob(expandedJob === job.id ? null : job.id)}>
                          <TableCell className="text-slate-400 px-2">
                            {expandedJob === job.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </TableCell>
                          <TableCell className="text-slate-900 font-medium">{job.title}</TableCell>
                          <TableCell className="text-slate-700 text-sm">{job.department || <span className="text-slate-400">—</span>}</TableCell>
                          <TableCell className="text-slate-700 text-sm">{job.sector_name || <span className="text-slate-400">Unassigned</span>}</TableCell>
                          <TableCell className="text-slate-700 text-sm">
                            {job.location ? (
                              <span className="flex items-center gap-1"><MapPin className="w-3 h-3 text-slate-400" />{job.location}</span>
                            ) : <span className="text-slate-400">—</span>}
                          </TableCell>
                          <TableCell>
                            <div className="flex flex-col gap-1">
                              <Badge className={`text-xs ${
                                job.experience_level === 'senior' ? 'bg-purple-600' :
                                job.experience_level === 'lead' ? 'bg-red-600' :
                                job.experience_level === 'principal' ? 'bg-amber-700' :
                                job.experience_level === 'junior' ? 'bg-green-600' :
                                'bg-blue-600'
                              } text-white`}>
                                {(job.experience_level || 'mid').charAt(0).toUpperCase() + (job.experience_level || 'mid').slice(1)}
                              </Badge>
                              <span className="text-xs text-slate-500">{(job.employment_type || 'full-time').replace('-', ' ')}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-slate-700 text-sm">
                            {job.min_experience || 0}{job.max_experience ? `–${job.max_experience}` : '+'} yrs
                          </TableCell>
                          <TableCell className="text-slate-700 text-sm">
                            {job.salary_range ? (
                              <span className="flex items-center gap-1"><IndianRupee className="w-3 h-3 text-slate-400" />{job.salary_range}</span>
                            ) : <span className="text-slate-400">—</span>}
                          </TableCell>
                          <TableCell>
                            <Badge className={job.status === 'active' ? 'bg-green-600' : job.status === 'closed' ? 'bg-red-600' : 'bg-slate-600'}>
                              {job.status ? job.status.charAt(0).toUpperCase() + job.status.slice(1) : 'Active'}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); fetchJobCandidates(job.id); }} className="text-indigo-600 hover:text-indigo-800 text-xs">
                              <Eye className="w-3 h-3 mr-1" /> View
                            </Button>
                          </TableCell>
                          <TableCell>
                            <div className="flex gap-1">
                              <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); openEditJob(job); }} className="text-slate-600 hover:text-indigo-600">
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleDeleteJob(job.id); }} disabled={deletingJob === job.id} className="text-red-400 hover:text-red-600">
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                        {/* Expanded detail row */}
                        {expandedJob === job.id && (
                          <TableRow className="bg-slate-50/80 border-slate-200">
                            <TableCell colSpan={11} className="py-4 px-6">
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {/* Left: Description */}
                                <div>
                                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Description</p>
                                  {job.description ? (
                                    <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed">{job.description}</p>
                                  ) : (
                                    <p className="text-sm text-slate-400 italic">No description provided</p>
                                  )}
                                </div>
                                {/* Right: Skills & Details */}
                                <div className="space-y-4">
                                  <div>
                                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Required Skills</p>
                                    <div className="flex flex-wrap gap-1">
                                      {(job.required_skills_list || []).length > 0 ? (
                                        job.required_skills_list.map((skill, i) => (
                                          <Badge key={i} className="bg-blue-100 text-blue-800 text-xs">{skill}</Badge>
                                        ))
                                      ) : <span className="text-sm text-slate-400">None specified</span>}
                                    </div>
                                  </div>
                                  {job.preferred_skills_list?.length > 0 && (
                                    <div>
                                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Preferred Skills</p>
                                      <div className="flex flex-wrap gap-1">
                                        {job.preferred_skills_list.map((skill, i) => (
                                          <Badge key={i} variant="outline" className="text-xs border-green-300 text-green-700">{skill}</Badge>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-200">
                                    <div className="flex items-center gap-2 text-sm text-slate-600">
                                      <Building2 className="w-4 h-4 text-slate-400" />
                                      <span><span className="font-medium">Dept:</span> {job.department || '—'}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-slate-600">
                                      <MapPin className="w-4 h-4 text-slate-400" />
                                      <span><span className="font-medium">Work Mode:</span> {job.location || '—'}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-slate-600">
                                      <Clock className="w-4 h-4 text-slate-400" />
                                      <span><span className="font-medium">Type:</span> {(job.employment_type || 'full-time').replace('-', ' ')}</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-sm text-slate-600">
                                      <IndianRupee className="w-4 h-4 text-slate-400" />
                                      <span><span className="font-medium">Salary:</span> {job.salary_range || '—'}</span>
                                    </div>
                                  </div>
                                </div>
                              </div>
                            </TableCell>
                          </TableRow>
                        )}
                      </React.Fragment>
                    ))}
                  </TableBody>
                </Table>
                {jobPostings.length === 0 && (
                  <p className="text-slate-600 text-center py-8">No job postings found. Create one with required skills to enable AI candidate matching.</p>
                )}

                {/* Matched candidates for selected job */}
                {selectedJobForCandidates && jobCandidates.length > 0 && (
                  <div className="mt-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                    <h4 className="font-semibold text-indigo-900 mb-3">
                      Matched Candidates for Job #{selectedJobForCandidates}
                    </h4>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="text-indigo-800">Candidate</TableHead>
                          <TableHead className="text-indigo-800">Match Score</TableHead>
                          <TableHead className="text-indigo-800">Skill Match</TableHead>
                          <TableHead className="text-indigo-800">Exp Match</TableHead>
                          <TableHead className="text-indigo-800">AI Reasoning</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {jobCandidates.map((c) => (
                          <TableRow key={c.id}>
                            <TableCell className="font-medium text-slate-900">{c.name} <span className="text-xs text-slate-500">({c.email})</span></TableCell>
                            <TableCell>
                              <span className={`font-bold ${c.match_score >= 75 ? 'text-green-600' : c.match_score >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                                {c.match_score}%
                              </span>
                            </TableCell>
                            <TableCell className="text-slate-700">{c.skill_match_score}%</TableCell>
                            <TableCell className="text-slate-700">{c.experience_match_score}%</TableCell>
                            <TableCell className="text-slate-600 text-xs max-w-[250px] truncate" title={c.ai_reasoning}>{c.ai_reasoning || 'N/A'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Bulk Upload Tab */}
          <TabsContent value="bulk-upload">
            <Card className="bg-white border-none shadow-md hover:shadow-lg transition-all duration-300">
              <CardHeader className="border-b border-slate-200 pb-4">
                <div>
                  <CardTitle className="text-slate-900 flex items-center gap-2">
                    <FileArchive className="w-5 h-5 text-indigo-600" />
                    Bulk Resume Upload
                  </CardTitle>
                  <CardDescription className="text-slate-600">
                    Upload a ZIP archive containing PDF/DOCX resumes. All resumes will be processed in parallel by multiple AI agents and scored against the selected job.
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="pt-6 space-y-6">
                {/* Step 1: Select Job */}
                <div className="space-y-2">
                  <Label className="text-slate-700 font-semibold">1. Select Target Job</Label>
                  <p className="text-xs text-slate-500">All resumes will be AI-scored against this job position</p>
                  <Select value={bulkJobId} onValueChange={setBulkJobId}>
                    <SelectTrigger className="w-full max-w-md">
                      <SelectValue placeholder="Choose a job posting..." />
                    </SelectTrigger>
                    <SelectContent position="popper">
                      {jobPostings.filter(j => j.status === 'active').map(job => (
                        <SelectItem key={job.id} value={String(job.id)}>
                          {job.title} — {job.department || 'General'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Step 2: Upload ZIP */}
                <div className="space-y-2">
                  <Label className="text-slate-700 font-semibold">2. Upload Resume Archive</Label>
                  <div
                    className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                      bulkFile
                        ? 'border-indigo-400 bg-indigo-50'
                        : 'border-slate-300 hover:border-indigo-400 hover:bg-slate-50'
                    }`}
                    onClick={() => document.getElementById('bulk-zip-input').click()}
                    onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                    onDrop={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      const file = e.dataTransfer.files[0];
                      const name = file?.name?.toLowerCase() || '';
                      if (file && (name.endsWith('.zip') || name.endsWith('.rar'))) {
                        setBulkFile(file);
                        setBulkResults(null);
                      } else {
                        toast({ title: 'Invalid file', description: 'Please drop a .zip or .rar file', variant: 'destructive' });
                      }
                    }}
                  >
                    <input
                      id="bulk-zip-input"
                      type="file"
                      accept=".zip,.rar"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files[0]) {
                          setBulkFile(e.target.files[0]);
                          setBulkResults(null);
                        }
                      }}
                    />
                    {bulkFile ? (
                      <div className="space-y-2">
                        <FileArchive className="w-12 h-12 mx-auto text-indigo-600" />
                        <p className="text-lg font-medium text-indigo-700">{bulkFile.name}</p>
                        <p className="text-sm text-slate-500">{(bulkFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                        <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setBulkFile(null); setBulkResults(null); }}>
                          Change file
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Upload className="w-12 h-12 mx-auto text-slate-400" />
                        <p className="text-lg font-medium text-slate-600">Drop ZIP or RAR file here or click to browse</p>
                        <p className="text-sm text-slate-400">Supports .zip and .rar archives containing .pdf and .docx resumes</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Upload Button */}
                <Button
                  className="bg-indigo-600 hover:bg-indigo-700 shadow-md px-8"
                  disabled={!bulkFile || !bulkJobId || bulkUploading}
                  onClick={async () => {
                    setBulkUploading(true);
                    setBulkResults(null);
                    setBulkProgress('Uploading archive and extracting resumes...');
                    try {
                      const formData = new FormData();
                      formData.append('file', bulkFile);
                      formData.append('job_id', bulkJobId);
                      const res = await api.post('/api/admin/bulk-upload', formData, {
                        headers: { 'Content-Type': 'multipart/form-data' },
                        timeout: 600000 // 10 min timeout for large batches
                      });
                      setBulkResults(res.data);
                      setBulkProgress(null);
                      toast({
                        title: 'Bulk Upload Complete',
                        description: res.data.message,
                        duration: 5000
                      });
                    } catch (err) {
                      const msg = err.response?.data?.message || err.message;
                      setBulkProgress(null);
                      toast({ title: 'Bulk Upload Failed', description: msg, variant: 'destructive' });
                    } finally {
                      setBulkUploading(false);
                    }
                  }}
                >
                  {bulkUploading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Processing Resumes...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 mr-2" />
                      Upload & Process All
                    </>
                  )}
                </Button>

                {/* Progress Indicator */}
                {bulkUploading && bulkProgress && (
                  <div className="flex items-center gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin flex-shrink-0" />
                    <div>
                      <p className="font-medium text-blue-800">{bulkProgress}</p>
                      <p className="text-xs text-blue-600 mt-1">Multiple AI agents are processing resumes in parallel. This may take a few minutes for large batches.</p>
                    </div>
                  </div>
                )}

                {/* Results */}
                {bulkResults && bulkResults.summary && (
                  <div className="space-y-4">
                    {/* Summary Cards */}
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="bg-slate-50 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-slate-800">{bulkResults.summary.total}</p>
                        <p className="text-sm text-slate-500">Total Resumes</p>
                      </div>
                      <div className="bg-green-50 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-green-700">{bulkResults.summary.success}</p>
                        <p className="text-sm text-green-600">Successfully Added</p>
                      </div>
                      <div className="bg-orange-50 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-orange-700">{bulkResults.results?.filter(r => r.missing?.length > 0 && r.status === 'success').length || 0}</p>
                        <p className="text-sm text-orange-600">Absence of Details</p>
                      </div>
                      <div className="bg-amber-50 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-amber-700">{bulkResults.summary.duplicates}</p>
                        <p className="text-sm text-amber-600">Duplicates Skipped</p>
                      </div>
                      <div className="bg-red-50 rounded-lg p-4 text-center">
                        <p className="text-3xl font-bold text-red-700">{bulkResults.summary.errors}</p>
                        <p className="text-sm text-red-600">Failed</p>
                      </div>
                    </div>

                    <p className="text-sm text-slate-500">
                      Job: <span className="font-medium text-slate-700">{bulkResults.summary.job?.title}</span>
                      {bulkResults.summary.job?.department && <span> — {bulkResults.summary.job.department}</span>}
                    </p>

                    {/* Detailed Results Table */}
                    {bulkResults.results && bulkResults.results.length > 0 && (
                      <div className="overflow-x-auto rounded-lg border border-slate-200">
                        <Table>
                          <TableHeader>
                            <TableRow className="bg-slate-50">
                              <TableHead className="text-slate-700">Status</TableHead>
                              <TableHead className="text-slate-700">File</TableHead>
                              <TableHead className="text-slate-700">Name</TableHead>
                              <TableHead className="text-slate-700">Email</TableHead>
                              <TableHead className="text-slate-700">Match Score</TableHead>
                              <TableHead className="text-slate-700">AI Recommendation</TableHead>
                              <TableHead className="text-slate-700">Details</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {bulkResults.results.map((r, idx) => (
                              <TableRow key={idx} className={
                                r.status === 'success' && r.missing?.length > 0 ? 'bg-orange-50/50' :
                                r.status === 'success' ? 'bg-green-50/50' :
                                r.status === 'duplicate' ? 'bg-amber-50/50' : 'bg-red-50/50'
                              }>
                                <TableCell>
                                  {r.status === 'success' && r.missing?.length > 0 && <AlertTriangle className="w-5 h-5 text-orange-500" />}
                                  {r.status === 'success' && (!r.missing || r.missing.length === 0) && <CheckCircle2 className="w-5 h-5 text-green-600" />}
                                  {r.status === 'duplicate' && <AlertTriangle className="w-5 h-5 text-amber-500" />}
                                  {r.status === 'error' && <XCircle className="w-5 h-5 text-red-500" />}
                                </TableCell>
                                <TableCell className="text-sm text-slate-700 max-w-[200px] truncate" title={r.filename}>
                                  {r.filename}
                                </TableCell>
                                <TableCell className="text-sm font-medium text-slate-800">{r.name || '—'}</TableCell>
                                <TableCell className="text-sm text-slate-600">{r.email || '—'}</TableCell>
                                <TableCell>
                                  {r.match_score > 0 ? (
                                    <Badge className={
                                      r.match_score >= 70 ? 'bg-green-100 text-green-800' :
                                      r.match_score >= 40 ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'
                                    }>
                                      {r.match_score}%
                                    </Badge>
                                  ) : '—'}
                                </TableCell>
                                <TableCell className="text-sm text-slate-600">
                                  {r.recommendation || '—'}
                                  {r.missing?.length > 0 && (
                                    <Badge className="ml-2 bg-orange-100 text-orange-800 text-xs">Absence of Details</Badge>
                                  )}
                                </TableCell>
                                <TableCell className="text-sm text-slate-500 max-w-[250px]">
                                  <span className="truncate block" title={r.error || ''}>
                                    {r.missing?.length > 0 && (
                                      <span className="text-orange-600">Missing: {r.missing.join(', ')}. </span>
                                    )}
                                    {r.error || (r.candidate_id ? `ID: ${r.candidate_id}` : '')}
                                  </span>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Question Bank Tab */}
          <TabsContent value="question-bank">
            <div className="space-y-6">
              {/* Upload Section */}
              <Card className="bg-white border-none shadow-md">
                <CardHeader className="border-b border-slate-200 pb-4">
                  <CardTitle className="flex items-center gap-2 text-slate-900">
                    <FileQuestion className="w-5 h-5 text-indigo-600" />
                    Upload Custom Questions
                  </CardTitle>
                  <CardDescription>Upload a PDF or DOCX file containing your own questions. AI will parse them and blend them into future assessments.</CardDescription>
                </CardHeader>
                <CardContent className="pt-6 space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-sm font-medium text-slate-700">File (PDF / DOCX)</Label>
                      <div
                        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${qbFile ? 'border-indigo-400 bg-indigo-50' : 'border-slate-300 hover:border-indigo-400 bg-slate-50'}`}
                        onClick={() => document.getElementById('qb-file-input').click()}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={(e) => {
                          e.preventDefault();
                          const f = e.dataTransfer.files[0];
                          if (f && (f.name.endsWith('.pdf') || f.name.endsWith('.docx'))) setQbFile(f);
                        }}
                      >
                        <input
                          id="qb-file-input"
                          type="file"
                          accept=".pdf,.docx"
                          className="hidden"
                          onChange={(e) => setQbFile(e.target.files[0] || null)}
                        />
                        {qbFile ? (
                          <div className="flex items-center justify-center gap-2 text-indigo-700">
                            <FileText className="w-5 h-5" />
                            <span className="font-medium">{qbFile.name}</span>
                            <button onClick={(e) => { e.stopPropagation(); setQbFile(null); }} className="ml-2 text-slate-400 hover:text-red-500">
                              <XCircle className="w-4 h-4" />
                            </button>
                          </div>
                        ) : (
                          <div>
                            <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                            <p className="text-sm text-slate-500">Drop a PDF/DOCX here or click to browse</p>
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-slate-700">Description (Optional)</Label>
                        <Input
                          placeholder="e.g. Java & Spring Boot questions from 2024 exam"
                          value={qbDescription}
                          onChange={(e) => setQbDescription(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label className="text-sm font-medium text-slate-700">Tags (Optional)</Label>
                        <Input
                          placeholder="e.g. java, spring, backend"
                          value={qbTags}
                          onChange={(e) => setQbTags(e.target.value)}
                        />
                      </div>
                    </div>
                  </div>
                  <Button
                    onClick={handleQbUpload}
                    disabled={!qbFile || qbUploading}
                    className="bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 shadow-md"
                  >
                    {qbUploading ? (
                      <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Parsing & Uploading...</>
                    ) : (
                      <><Upload className="w-4 h-4 mr-2" /> Upload & Parse Questions</>
                    )}
                  </Button>
                </CardContent>
              </Card>

              {/* Question Banks List */}
              <Card className="bg-white border-none shadow-md">
                <CardHeader className="border-b border-slate-200 pb-4 flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-slate-900 flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-indigo-600" />
                      Uploaded Question Banks ({questionBanks.length})
                    </CardTitle>
                  </div>
                  <Button variant="outline" size="sm" onClick={fetchQuestionBanks} disabled={qbLoading}>
                    <RefreshCw className={`w-4 h-4 mr-1 ${qbLoading ? 'animate-spin' : ''}`} />
                    Refresh
                  </Button>
                </CardHeader>
                <CardContent className="pt-4">
                  {qbLoading ? (
                    <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-indigo-500" /></div>
                  ) : questionBanks.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <BookOpen className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                      <p className="font-medium">No question banks uploaded yet</p>
                      <p className="text-sm mt-1">Upload a PDF or DOCX to get started</p>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {questionBanks.map(qb => (
                        <div key={qb.id} className="border border-slate-200 rounded-lg p-4 hover:shadow-md transition-all">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${qb.is_active ? 'bg-green-100 text-green-600' : 'bg-slate-100 text-slate-400'}`}>
                                <FileText className="w-5 h-5" />
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-semibold text-slate-800">{qb.filename}</span>
                                  <Badge variant={qb.is_active ? 'default' : 'secondary'} className={qb.is_active ? 'bg-green-100 text-green-700 hover:bg-green-100' : ''}>
                                    {qb.is_active ? 'Active' : 'Inactive'}
                                  </Badge>
                                  <Badge variant="outline" className="text-indigo-600 border-indigo-200">
                                    {qb.questions_count} questions
                                  </Badge>
                                </div>
                                <div className="text-xs text-slate-500 mt-0.5">
                                  {qb.description && <span>{qb.description} · </span>}
                                  Uploaded by {qb.uploaded_by || 'Unknown'} · {qb.created_at ? new Date(qb.created_at).toLocaleDateString() : ''}
                                  {qb.tags && <span className="ml-2 text-indigo-500">{qb.tags}</span>}
                                </div>
                              </div>
                            </div>
                            <div className="flex items-center gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleQbPreview(qb.id)}
                                title="Preview questions"
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleQbToggle(qb.id)}
                                title={qb.is_active ? 'Deactivate' : 'Activate'}
                              >
                                {qb.is_active ? <ToggleRight className="w-4 h-4 text-green-600" /> : <ToggleLeft className="w-4 h-4 text-slate-400" />}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleQbDelete(qb.id)}
                                className="hover:text-red-600"
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          {/* Expandable Preview */}
                          {qbPreview?.id === qb.id && (
                            <div className="mt-4 border-t border-slate-100 pt-4">
                              {qbPreviewLoading ? (
                                <div className="flex items-center gap-2 text-slate-500"><Loader2 className="w-4 h-4 animate-spin" /> Loading...</div>
                              ) : (
                                <div className="space-y-3">
                                  <div className="text-sm font-medium text-slate-700">Parsed Questions ({qbPreview.questions_count}):</div>
                                  <div className="max-h-80 overflow-y-auto space-y-2">
                                    {(qbPreview.parsed_questions || []).map((q, i) => (
                                      <div key={i} className="bg-slate-50 rounded-lg p-3 text-sm">
                                        <div className="font-medium text-slate-800">Q{i + 1}: {q.question}</div>
                                        {q.options && (
                                          <div className="mt-2 grid grid-cols-2 gap-1">
                                            {q.options.map((opt, j) => (
                                              <div key={j} className={`px-2 py-1 rounded text-xs ${opt === q.correct_answer ? 'bg-green-100 text-green-700 font-medium' : 'text-slate-600'}`}>
                                                {String.fromCharCode(65 + j)}. {opt}
                                              </div>
                                            ))}
                                          </div>
                                        )}
                                        {q.correct_answer && !q.options && (
                                          <div className="mt-1 text-xs text-green-600">Answer: {q.correct_answer}</div>
                                        )}
                                        <div className="mt-1 flex gap-2">
                                          {q.category && <Badge variant="outline" className="text-xs">{q.category}</Badge>}
                                          {q.difficulty && <Badge variant="outline" className="text-xs">{q.difficulty}</Badge>}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                  {qbPreview.raw_text_preview && (
                                    <details className="text-xs text-slate-500">
                                      <summary className="cursor-pointer hover:text-slate-700">Raw text preview</summary>
                                      <pre className="mt-2 p-2 bg-slate-100 rounded text-xs whitespace-pre-wrap max-h-40 overflow-y-auto">{qbPreview.raw_text_preview}</pre>
                                    </details>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Analytics Tab */}
          <TabsContent value="analytics">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Candidate Analytics */}
              <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
                <CardHeader>
                  <CardTitle className="text-slate-900">Candidate Statistics</CardTitle>
                  <CardDescription className="text-slate-600">Overview of candidate pipeline</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/50 p-4 rounded-lg">
                      <div className="text-3xl font-bold text-slate-900">{analytics.candidates?.total || 0}</div>
                      <div className="text-sm text-slate-600">Total Candidates</div>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-lg">
                      <div className="text-3xl font-bold text-blue-400">{analytics.candidates?.this_month || 0}</div>
                      <div className="text-sm text-slate-600">This Month</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Pending</span>
                      <Badge className="bg-yellow-600">{analytics.candidates?.pending || 0}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Under Review</span>
                      <Badge className="bg-blue-600">{analytics.candidates?.under_review || 0}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Hired</span>
                      <Badge className="bg-green-600">{analytics.candidates?.hired || 0}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Rejected</span>
                      <Badge className="bg-red-600">{analytics.candidates?.rejected || 0}</Badge>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-slate-200">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Avg. Match Score</span>
                      <span className="text-2xl font-bold text-indigo-400">{analytics.candidates?.avg_match_score || 0}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Assessment Analytics */}
              <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
                <CardHeader>
                  <CardTitle className="text-slate-900">Assessment Statistics</CardTitle>
                  <CardDescription className="text-slate-600">Assessment performance metrics</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-slate-900/50 p-4 rounded-lg">
                      <div className="text-3xl font-bold text-slate-900">{analytics.assessments?.total || 0}</div>
                      <div className="text-sm text-slate-600">Total Assessments</div>
                    </div>
                    <div className="bg-slate-900/50 p-4 rounded-lg">
                      <div className="text-3xl font-bold text-purple-400">{analytics.assessments?.this_month || 0}</div>
                      <div className="text-sm text-slate-600">This Month</div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Scheduled</span>
                      <Badge className="bg-yellow-600">{analytics.assessments?.scheduled || 0}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">In Progress</span>
                      <Badge className="bg-blue-600">{analytics.assessments?.in_progress || 0}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Completed</span>
                      <Badge className="bg-green-600">{analytics.assessments?.completed || 0}</Badge>
                    </div>
                  </div>
                  <div className="pt-4 border-t border-slate-200 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Avg. Technical Score</span>
                      <span className="text-xl font-bold text-green-400">{analytics.assessments?.avg_technical_score || 0}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-700">Avg. Psychometric Score</span>
                      <span className="text-xl font-bold text-purple-400">{analytics.assessments?.avg_psychometric_score || 0}%</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Audit Log Tab */}
          <TabsContent value="audit-log">
            <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
              <CardHeader>
                <CardTitle className="text-slate-900">Audit Log</CardTitle>
                <CardDescription className="text-slate-600">Track all user actions — job postings, candidate matching, status changes</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-200">
                      <TableHead className="text-slate-700">Time</TableHead>
                      <TableHead className="text-slate-700">User</TableHead>
                      <TableHead className="text-slate-700">Action</TableHead>
                      <TableHead className="text-slate-700">Entity</TableHead>
                      <TableHead className="text-slate-700">Details</TableHead>
                      <TableHead className="text-slate-700">IP</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {auditLogs.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-slate-500">
                          No audit log entries found
                        </TableCell>
                      </TableRow>
                    ) : (
                      auditLogs.map((log) => (
                        <TableRow key={log.id} className="border-slate-200">
                          <TableCell className="text-slate-600 text-xs">
                            {new Date(log.created_at).toLocaleString()}
                          </TableCell>
                          <TableCell className="text-slate-700 text-sm">{log.user_email || 'System'}</TableCell>
                          <TableCell>
                            <Badge variant="outline" className="border-slate-300 text-slate-700">
                              {(log.action || '').replace(/_/g, ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-slate-700 text-sm">
                            {log.entity_type && `${log.entity_type} #${log.entity_id}`}
                          </TableCell>
                          <TableCell className="text-slate-600 text-xs max-w-[200px] truncate" title={JSON.stringify(log.details)}>
                            {log.details ? JSON.stringify(log.details).substring(0, 60) : '—'}
                          </TableCell>
                          <TableCell className="text-slate-500 text-xs">{log.ip_address || '—'}</TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Settings Tab */}
          <TabsContent value="settings">
            <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
              <CardHeader>
                <CardTitle className="text-slate-900">Environment Variables</CardTitle>
                <CardDescription className="text-slate-600">
                  Configure environment variables. Changes are persisted to .env file and require backend restart to take effect.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(envStatus).map(([key, value]) => (
                    <div key={key} className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-slate-900 font-mono text-sm font-semibold">{key}</span>
                            {value ? (
                              <Badge className="bg-green-600">
                                <Shield className="w-3 h-3 mr-1" />
                                Configured
                              </Badge>
                            ) : (
                              <Badge className="bg-red-600">Not Set</Badge>
                            )}
                          </div>

                          {editingEnvVar === key ? (
                            <div className="space-y-2">
                              <Input
                                type="text"
                                placeholder={`Enter ${key} value`}
                                value={envVarValue}
                                onChange={(e) => setEnvVarValue(e.target.value)}
                                className="font-mono text-sm"
                              />
                              <div className="flex gap-2">
                                <Button
                                  size="sm"
                                  onClick={handleSaveEnvVar}
                                  className="bg-green-600 hover:bg-green-700"
                                >
                                  Save
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={handleCancelEdit}
                                  className="border-slate-300"
                                >
                                  Cancel
                                </Button>
                              </div>
                            </div>
                          ) : (
                            <div className="flex items-center gap-2">
                              {value && (
                                <span className="text-xs text-slate-500 font-mono">{value}</span>
                              )}
                            </div>
                          )}
                        </div>

                        {editingEnvVar !== key && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleEditEnvVar(key, value)}
                            className="border-indigo-300 text-indigo-700 hover:bg-indigo-50"
                          >
                            <Edit className="w-4 h-4 mr-1" />
                            Edit
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>

      {/* User Modal */}
      <Dialog open={userModalOpen} onOpenChange={setUserModalOpen}>
        <DialogContent className="bg-white border-slate-200 shadow-md">
          <DialogHeader>
            <DialogTitle className="text-slate-900">{editingUser ? 'Edit User' : 'Add New User'}</DialogTitle>
            <DialogDescription className="text-slate-600">
              {editingUser ? 'Update user details' : 'Create a new user account'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-700">Name</Label>
              <Input
                value={userForm.name}
                onChange={(e) => setUserForm({ ...userForm, name: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Email</Label>
              <Input
                type="email"
                value={userForm.email}
                onChange={(e) => setUserForm({ ...userForm, email: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Password {editingUser && '(leave blank to keep current)'}</Label>
              <Input
                type="password"
                value={userForm.password}
                onChange={(e) => setUserForm({ ...userForm, password: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Role</Label>
              <Select value={userForm.role} onValueChange={(v) => setUserForm({ ...userForm, role: v })}>
                <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-slate-200 shadow-md">
                  <SelectItem value="interviewer">Interviewer</SelectItem>
                  <SelectItem value="proctor">Proctor</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUserModalOpen(false)} className="border-slate-300 text-slate-700">
              Cancel
            </Button>
            <Button onClick={handleSaveUser} className="bg-indigo-600 hover:bg-indigo-700">
              {editingUser ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Candidate Modal */}
      <Dialog open={candidateModalOpen} onOpenChange={setCandidateModalOpen}>
        <DialogContent className="bg-white border-slate-200 shadow-md">
          <DialogHeader>
            <DialogTitle className="text-slate-900">Edit Candidate</DialogTitle>
            <DialogDescription className="text-slate-600">Update candidate details</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-700">Name</Label>
              <Input
                value={candidateForm.name}
                onChange={(e) => setCandidateForm({ ...candidateForm, name: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Email</Label>
              <Input
                type="email"
                value={candidateForm.email}
                onChange={(e) => setCandidateForm({ ...candidateForm, email: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Phone</Label>
              <Input
                value={candidateForm.phone}
                onChange={(e) => setCandidateForm({ ...candidateForm, phone: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Status</Label>
              <Select value={candidateForm.status} onValueChange={(v) => setCandidateForm({ ...candidateForm, status: v })}>
                <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-slate-200 shadow-md">
                  <SelectItem value="Applied">Applied</SelectItem>
                  <SelectItem value="Scheduled">Scheduled</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                  <SelectItem value="Rejected">Rejected</SelectItem>
                  <SelectItem value="Hired">Hired</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Match Score (%)</Label>
              <Input
                type="number"
                min="0"
                max="100"
                value={candidateForm.match_score}
                onChange={(e) => setCandidateForm({ ...candidateForm, match_score: parseInt(e.target.value) || 0 })}
                className="bg-white border-slate-300 text-slate-900"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCandidateModalOpen(false)} className="border-slate-300 text-slate-700">
              Cancel
            </Button>
            <Button onClick={handleSaveCandidate} className="bg-indigo-600 hover:bg-indigo-700">
              Update
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Job Posting Modal — Enhanced */}
      <Dialog open={jobModalOpen} onOpenChange={setJobModalOpen}>
        <DialogContent className="bg-white border-slate-200 shadow-md max-w-2xl max-h-[90vh] overflow-y-auto [&_input]:caret-slate-900 [&_textarea]:caret-slate-900" onPointerDownOutside={(e) => e.preventDefault()}>
          <DialogHeader>
            <DialogTitle className="text-slate-900">{editingJob ? 'Edit Job Posting' : 'Create Job Posting'}</DialogTitle>
            <DialogDescription className="text-slate-600">
              {editingJob ? 'Update job details and skill requirements' : 'Define a new job with required skills. AI will match incoming candidates automatically.'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-700">Job Title *</Label>
              <Input
                autoFocus
                value={jobForm.title}
                onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })}
                className="bg-white border-slate-300 text-slate-900 focus:ring-2 focus:ring-indigo-500"
                placeholder="e.g., Senior Software Engineer"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Description</Label>
              <textarea
                value={jobForm.description}
                onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
                className="w-full bg-white border border-slate-300 text-slate-900 rounded-md p-2 text-sm min-h-[80px]"
                placeholder="Detailed job description..."
              />
            </div>
            {/* AI Enhance Button */}
            {(jobForm.title || jobForm.description) && (
              <Button
                type="button"
                variant="outline"
                className="border-purple-300 text-purple-700 hover:bg-purple-50"
                disabled={enhancingJob}
                onClick={async () => {
                  setEnhancingJob(true);
                  try {
                    const res = await api.post('/api/admin/ai-enhance', {
                      type: 'job',
                      title: jobForm.title,
                      description: jobForm.description
                    });
                    if (res.data.status === 'success') {
                      setJobForm(prev => ({
                        ...prev,
                        title: res.data.enhanced_title || prev.title,
                        description: res.data.enhanced_description || prev.description,
                        required_skills: res.data.required_skills || prev.required_skills,
                        preferred_skills: res.data.preferred_skills || prev.preferred_skills
                      }));
                      toast({ title: 'Enhanced', description: 'Title, description & skills polished by AI', duration: 3000 });
                    } else {
                      toast({ title: 'AI Error', description: res.data.message, variant: 'destructive' });
                    }
                  } catch (err) {
                    toast({ title: 'AI Error', description: err.response?.data?.message || err.message, variant: 'destructive' });
                  } finally {
                    setEnhancingJob(false);
                  }
                }}
              >
                {enhancingJob ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
                {enhancingJob ? 'Enhancing...' : 'Enhance with AI'}
              </Button>
            )}

            {/* Skills Section — THE KEY IMPROVEMENT */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
              <p className="text-sm font-semibold text-blue-900"> Skill Requirements (Critical for AI Matching)</p>
              <div className="space-y-2">
                <Label className="text-blue-800 font-medium">Required Skills * <span className="font-normal text-xs">(comma-separated)</span></Label>
                <Input
                  value={jobForm.required_skills}
                  onChange={(e) => setJobForm({ ...jobForm, required_skills: e.target.value })}
                  className="bg-white border-blue-300 text-slate-900"
                  placeholder="e.g., Python, React, PostgreSQL, Docker"
                />
                <p className="text-xs text-blue-700">These skills are mandatory. Candidates missing required skills will score lower.</p>
              </div>
              <div className="space-y-2">
                <Label className="text-blue-800 font-medium">Preferred Skills <span className="font-normal text-xs">(comma-separated)</span></Label>
                <Input
                  value={jobForm.preferred_skills}
                  onChange={(e) => setJobForm({ ...jobForm, preferred_skills: e.target.value })}
                  className="bg-white border-blue-300 text-slate-900"
                  placeholder="e.g., Kubernetes, AWS, GraphQL, TypeScript"
                />
                <p className="text-xs text-blue-700">Nice-to-have skills that boost match scores.</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-slate-700">Experience Level</Label>
                <Select value={jobForm.experience_level} onValueChange={(v) => setJobForm({ ...jobForm, experience_level: v })}>
                  <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-slate-200 shadow-md" position="popper" sideOffset={4}>
                    <SelectItem value="junior">Junior (0-2 years)</SelectItem>
                    <SelectItem value="mid">Mid-Level (2-5 years)</SelectItem>
                    <SelectItem value="senior">Senior (5-10 years)</SelectItem>
                    <SelectItem value="lead">Lead (8-15 years)</SelectItem>
                    <SelectItem value="principal">Principal (12+ years)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-slate-700">Employment Type</Label>
                <Select value={jobForm.employment_type} onValueChange={(v) => setJobForm({ ...jobForm, employment_type: v })}>
                  <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-slate-200 shadow-md" position="popper" sideOffset={4}>
                    <SelectItem value="full-time">Full-time</SelectItem>
                    <SelectItem value="part-time">Part-time</SelectItem>
                    <SelectItem value="contract">Contract</SelectItem>
                    <SelectItem value="internship">Internship</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label className="text-slate-700">Min Experience (yrs)</Label>
                <Input
                  type="number" min="0"
                  value={jobForm.min_experience}
                  onChange={(e) => setJobForm({ ...jobForm, min_experience: e.target.value })}
                  className="bg-white border-slate-300 text-slate-900"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-slate-700">Max Experience (yrs)</Label>
                <Input
                  type="number" min="0"
                  value={jobForm.max_experience}
                  onChange={(e) => setJobForm({ ...jobForm, max_experience: e.target.value })}
                  className="bg-white border-slate-300 text-slate-900"
                  placeholder="Optional"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-slate-700">Salary Range</Label>
                <Input
                  value={jobForm.salary_range}
                  onChange={(e) => setJobForm({ ...jobForm, salary_range: e.target.value })}
                  className="bg-white border-slate-300 text-slate-900"
                  placeholder="e.g., ₹8L-₹12L per annum"
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label className="text-slate-700">Department</Label>
                <Input
                  value={jobForm.department}
                  onChange={(e) => setJobForm({ ...jobForm, department: e.target.value })}
                  className="bg-white border-slate-300 text-slate-900"
                  placeholder="e.g., Engineering"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-slate-700">Work Mode</Label>
                <Select value={jobForm.location} onValueChange={(v) => setJobForm({ ...jobForm, location: v })}>
                  <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                    <SelectValue placeholder="Select work mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Remote">Remote</SelectItem>
                    <SelectItem value="On-Site">On-Site</SelectItem>
                    <SelectItem value="Hybrid">Hybrid</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-slate-700">Sector</Label>
                <Select value={jobForm.sector_id} onValueChange={(v) => setJobForm({ ...jobForm, sector_id: v })}>
                  <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                    <SelectValue placeholder="Select sector" />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-slate-200 shadow-md" position="popper" sideOffset={4}>
                    <SelectItem value="none">No Sector</SelectItem>
                    {sectors.map(s => (
                      <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {editingJob && (
              <div className="space-y-2">
                <Label className="text-slate-700">Status</Label>
                <Select value={jobForm.status} onValueChange={(v) => setJobForm({ ...jobForm, status: v })}>
                  <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-white border-slate-200 shadow-md" position="popper" sideOffset={4}>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setJobModalOpen(false)} className="border-slate-300 text-slate-700">
              Cancel
            </Button>
            <Button onClick={handleSaveJob} disabled={savingJob} className="bg-indigo-600 hover:bg-indigo-700">
              {savingJob ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              {editingJob ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Sector Modal */}
      <Dialog open={sectorModalOpen} onOpenChange={setSectorModalOpen}>
        <DialogContent className="bg-white border-slate-200 shadow-md">
          <DialogHeader>
            <DialogTitle className="text-slate-900">Create Sector</DialogTitle>
            <DialogDescription className="text-slate-600">Add a new organizational sector for job postings and access control</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-700">Sector Name *</Label>
              <Input
                value={sectorForm.name}
                onChange={(e) => setSectorForm({ ...sectorForm, name: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
                placeholder="e.g., Product Engineering"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Description</Label>
              <Input
                value={sectorForm.description}
                onChange={(e) => setSectorForm({ ...sectorForm, description: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
                placeholder="Brief description of the sector"
              />
            </div>
            {/* AI Enhance Button */}
            {(sectorForm.name || sectorForm.description) && (
              <Button
                type="button"
                variant="outline"
                className="border-purple-300 text-purple-700 hover:bg-purple-50"
                disabled={enhancingSector}
                onClick={async () => {
                  setEnhancingSector(true);
                  try {
                    const res = await api.post('/api/admin/ai-enhance', {
                      type: 'sector',
                      title: sectorForm.name,
                      description: sectorForm.description
                    });
                    if (res.data.status === 'success') {
                      setSectorForm(prev => ({
                        ...prev,
                        name: res.data.enhanced_title || prev.name,
                        description: res.data.enhanced_description || prev.description
                      }));
                      toast({ title: 'Enhanced', description: 'Sector name and description polished by AI', duration: 3000 });
                    } else {
                      toast({ title: 'AI Error', description: res.data.message, variant: 'destructive' });
                    }
                  } catch (err) {
                    toast({ title: 'AI Error', description: err.response?.data?.message || err.message, variant: 'destructive' });
                  } finally {
                    setEnhancingSector(false);
                  }
                }}
              >
                {enhancingSector ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
                {enhancingSector ? 'Enhancing...' : 'Enhance with AI'}
              </Button>
            )}
            <div className="space-y-2">
              <Label className="text-slate-700">Email Alias</Label>
              <Input
                value={sectorForm.email_alias}
                onChange={(e) => setSectorForm({ ...sectorForm, email_alias: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
                placeholder="e.g., eng@company.com"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSectorModalOpen(false)} className="border-slate-300 text-slate-700">Cancel</Button>
            <Button onClick={handleSaveSector} className="bg-indigo-600 hover:bg-indigo-700">Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDashboardPage;
