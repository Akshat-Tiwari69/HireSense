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
  TrendingUp, AlertCircle, CheckCircle, Search
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
        title: "👤 New User Added",
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
        title: "🎯 New Candidate Registered",
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
        title: "💼 New Job Posted",
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
  const [jobForm, setJobForm] = useState({ title: '', description: '', required_skills: '', min_experience: 0, department: '', location: '' });
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

  // Search & Filter State
  const [userSearch, setUserSearch] = useState('');
  const [candidateSearch, setCandidateSearch] = useState('');
  const [candidateStatusFilter, setCandidateStatusFilter] = useState('all');

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
      const [usersRes, candidatesRes, statsRes, tablesRes, envRes, jobsRes] = await Promise.all([
        api.get('/api/admin/users'),
        api.get('/api/admin/candidates'),
        api.get('/api/admin/db/stats'),
        api.get('/api/admin/db/tables'),
        api.get('/api/admin/settings/env'),
        api.get('/api/admin/job-postings').catch(() => ({ data: { data: [] } })) // Graceful fallback
      ]);

      // Set initial data for realtime hooks
      setUsers(usersRes.data.data || []);
      setCandidates(candidatesRes.data.data || []);
      setJobPostings(jobsRes.data.data || []);

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

  const fetchJobPostings = async () => {
    try {
      const res = await api.get('/api/admin/job-postings');
      setJobPostings(res.data.data || []);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load job postings' });
    }
  };

  const handleSaveJob = async () => {
    try {
      await api.post('/api/admin/job-postings', jobForm);
      toast({ title: 'Success', description: 'Job posting created successfully' });
      setJobModalOpen(false);
      setJobForm({ title: '', description: '', required_skills: '', min_experience: 0, department: '', location: '' });
      fetchJobPostings();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: err?.response?.data?.message || 'Failed to create job' });
    }
  };

  const handleDeleteJob = async (jobId) => {
    if (!confirm('Delete this job posting?')) return;
    try {
      await api.delete(`/api/admin/job-postings/${jobId}`);
      toast({ title: 'Success', description: 'Job posting deleted' });
      fetchJobPostings();
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to delete job' });
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
            <TabsTrigger value="email-logs" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchEmailLogs}>
              <Mail className="w-4 h-4 mr-2" />
              Email Logs
            </TabsTrigger>
            <TabsTrigger value="job-postings" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchJobPostings}>
              <Briefcase className="w-4 h-4 mr-2" />
              Job Postings
            </TabsTrigger>
            <TabsTrigger value="analytics" className="data-[state=active]:bg-indigo-50 data-[state=active]:text-indigo-700" onClick={fetchAnalytics}>
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
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
                  <CardDescription className="text-slate-600">Manage job openings</CardDescription>
                </div>
                <Button onClick={() => setJobModalOpen(true)} className="bg-indigo-600 hover:bg-indigo-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Job
                </Button>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow className="border-slate-200">
                      <TableHead className="text-slate-700">Title</TableHead>
                      <TableHead className="text-slate-700">Department</TableHead>
                      <TableHead className="text-slate-700">Location</TableHead>
                      <TableHead className="text-slate-700">Experience</TableHead>
                      <TableHead className="text-slate-700">Status</TableHead>
                      <TableHead className="text-slate-700">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobPostings.map((job) => (
                      <TableRow key={job.id} className="border-slate-200">
                        <TableCell className="text-slate-900 font-medium">{job.title}</TableCell>
                        <TableCell className="text-slate-700">{job.department || 'N/A'}</TableCell>
                        <TableCell className="text-slate-700">{job.location || 'N/A'}</TableCell>
                        <TableCell className="text-slate-700">{job.min_experience || 0} years</TableCell>
                        <TableCell>
                          <Badge className={job.status === 'active' ? 'bg-green-600' : 'bg-slate-600'}>
                            {job.status ? job.status.charAt(0).toUpperCase() + job.status.slice(1) : 'Active'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Button variant="ghost" size="sm" onClick={() => handleDeleteJob(job.id)} className="text-red-400 hover:text-red-300">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {jobPostings.length === 0 && (
                  <p className="text-slate-600 text-center py-8">No job postings found. Create one to get started.</p>
                )}
              </CardContent>
            </Card>
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

      {/* Job Posting Modal */}
      <Dialog open={jobModalOpen} onOpenChange={setJobModalOpen}>
        <DialogContent className="bg-white border-slate-200 shadow-md">
          <DialogHeader>
            <DialogTitle className="text-slate-900">Create Job Posting</DialogTitle>
            <DialogDescription className="text-slate-600">Add a new job opening</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-slate-700">Job Title *</Label>
              <Input
                value={jobForm.title}
                onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
                placeholder="e.g., Senior Software Engineer"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Description</Label>
              <Input
                value={jobForm.description}
                onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
                placeholder="Brief job description"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
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
                <Label className="text-slate-700">Location</Label>
                <Input
                  value={jobForm.location}
                  onChange={(e) => setJobForm({ ...jobForm, location: e.target.value })}
                  className="bg-white border-slate-300 text-slate-900"
                  placeholder="e.g., Remote"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label className="text-slate-700">Min. Experience (years)</Label>
                <Input
                  type="number"
                  value={jobForm.min_experience}
                  onChange={(e) => setJobForm({ ...jobForm, min_experience: parseInt(e.target.value) || 0 })}
                  className="bg-white border-slate-300 text-slate-900"
                  min="0"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-slate-700">Required Skills</Label>
                <Input
                  value={jobForm.required_skills}
                  onChange={(e) => setJobForm({ ...jobForm, required_skills: e.target.value })}
                  className="bg-white border-slate-300 text-slate-900"
                  placeholder="e.g., React, Node.js"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setJobModalOpen(false)} className="border-slate-300 text-slate-700">
              Cancel
            </Button>
            <Button onClick={handleSaveJob} className="bg-indigo-600 hover:bg-indigo-700">
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDashboardPage;
