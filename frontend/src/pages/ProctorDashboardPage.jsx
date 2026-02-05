import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { io } from 'socket.io-client';
import { Button } from '../components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/Card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/Table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/Select';
import { Badge } from '../components/ui/Badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/Dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  LogOut, Eye, Users, Clock, CheckCircle, AlertTriangle, RefreshCw,
  Video, Calendar, Activity, Shield, LayoutDashboard, Search, TrendingUp, Zap
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { api, API_BASE_URL } from '../services/api';
import ProctorMonitor from '../components/ProctorMonitor';
import LoadingScreen from '../components/common/LoadingScreen';

const ProctorDashboardPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [stats, setStats] = useState({
    scheduled_count: 0,
    active_count: 0,
    completed_today: 0,
    violations_today: 0
  });
  const [scheduledAssessments, setScheduledAssessments] = useState([]);
  const [activeAssessments, setActiveAssessments] = useState([]);
  const [completedAssessments, setCompletedAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Violations Modal State
  const [violationsModalOpen, setViolationsModalOpen] = useState(false);
  const [selectedViolations, setSelectedViolations] = useState([]);
  const [loadingViolations, setLoadingViolations] = useState(false);

  // Live monitoring state
  const [monitoringAssessmentId, setMonitoringAssessmentId] = useState(null);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [violationFilter, setViolationFilter] = useState('all');

  // Socket.IO ref for real-time violation notifications
  const socketRef = useRef(null);

  // Memoized filtered data
  const filteredScheduled = useMemo(() => {
    return scheduledAssessments.filter(a =>
      a.candidate_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.email?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [scheduledAssessments, searchQuery]);

  const filteredActive = useMemo(() => {
    return activeAssessments.filter(a =>
      a.candidate_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.email?.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [activeAssessments, searchQuery]);

  const filteredCompleted = useMemo(() => {
    let result = completedAssessments.filter(a =>
      a.candidate_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      a.email?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (violationFilter === 'flagged') {
      result = result.filter(a => (a.proctoring_violations || 0) > 0);
    } else if (violationFilter === 'clean') {
      result = result.filter(a => (a.proctoring_violations || 0) === 0);
    }

    return result;
  }, [completedAssessments, searchQuery, violationFilter]);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      navigate('/login');
      return;
    }
    fetchAllData();
  }, [navigate]);

  // Auto-refresh every 10 seconds for active monitoring
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAllData(true);
    }, 10000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Socket.IO for real-time violation notifications
  useEffect(() => {
    // Connect to Socket.IO server
    const socket = io(API_BASE_URL, {
      transports: ['websocket', 'polling']
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('[PROCTOR DASHBOARD] Connected to violations socket');
      // Join proctor room for violation notifications
      socket.emit('join_proctor_room');
    });

    socket.on('violation_detected', (data) => {
      console.log('[PROCTOR DASHBOARD] Violation detected:', data);

      // Show toast notification
      const violationType = data.violation_type?.replace('_', ' ') || 'Unknown';
      const candidateName = data.candidate_name || 'Candidate';

      toast({
        variant: 'destructive',
        title: '⚠️ Violation Detected',
        description: `${candidateName}: ${violationType}`,
        duration: 5000,
      });

      // Increment violation count in stats
      setStats(prev => ({
        ...prev,
        violations_today: (prev.violations_today || 0) + 1
      }));

      // Refresh data to update UI
      fetchAllData(true);
    });

    socket.on('disconnect', () => {
      console.log('[PROCTOR DASHBOARD] Disconnected from violations socket');
    });

    return () => {
      socket.disconnect();
    };
  }, [toast]);

  const fetchAllData = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      console.log('[PROCTOR] Fetching all proctor data...');
      const [statsRes, scheduledRes, activeRes, completedRes] = await Promise.all([
        api.get('/api/proctor/stats'),
        api.get('/api/proctor/assessments/scheduled'),
        api.get('/api/proctor/assessments/active'),
        api.get('/api/proctor/assessments/completed')
      ]);

      console.log('[PROCTOR] Stats response:', statsRes.data);
      console.log('[PROCTOR] Scheduled response:', scheduledRes.data);
      console.log('[PROCTOR] Active response:', activeRes.data);
      console.log('[PROCTOR] Completed response:', completedRes.data);

      setStats(statsRes.data.data || {});
      setScheduledAssessments(scheduledRes.data.data || []);
      setActiveAssessments(activeRes.data.data || []);
      setCompletedAssessments(completedRes.data.data || []);

      console.log('[PROCTOR] State updated - scheduled count:', scheduledRes.data.data?.length || 0);
    } catch (err) {
      console.error('[PROCTOR] Error fetching data:', err);
      const message = err?.response?.data?.message || 'Failed to load proctor data';
      if (err?.response?.status === 403) {
        toast({ variant: 'destructive', title: 'Access Denied', description: 'Proctor role required' });
        navigate('/dashboard');
      } else if (!silent) {
        toast({ variant: 'destructive', title: 'Error', description: message });
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userRole');
    navigate('/login');
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleString();
  };

  const getTimeUntil = (dateStr) => {
    if (!dateStr) return '';
    const scheduled = new Date(dateStr);
    const now = new Date();
    const diffMs = scheduled - now;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 0) return 'Overdue';
    if (diffMins < 60) return `${diffMins} min`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hr`;
    return `${Math.floor(diffMins / 1440)} days`;
  };

  const handleViewViolations = async (assessmentId) => {
    setLoadingViolations(true);
    setViolationsModalOpen(true);
    setSelectedViolations([]); // Reset

    try {
      const res = await api.get(`/api/proctor/assessments/${assessmentId}/violations`);
      setSelectedViolations(res.data.data || []);
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to load violations' });
    } finally {
      setLoadingViolations(false);
    }
  };

  if (loading) {
    return <LoadingScreen message="Loading Proctor Dashboard" />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="border-b border-slate-200 bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Logo size="default" />
            <Badge className="bg-purple-600 text-white">PROCTOR</Badge>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-white/80 px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
              <RefreshCw className={`w-4 h-4 text-slate-600 ${autoRefresh ? 'animate-spin' : ''}`} style={{ animationDuration: '3s' }} />
              <span className="text-slate-700 text-sm font-medium">Auto-refresh</span>
              <Button
                size="sm"
                variant={autoRefresh ? 'default' : 'outline'}
                onClick={() => setAutoRefresh(!autoRefresh)}
                className="h-7 px-3 text-xs font-semibold"
              >
                {autoRefresh ? 'ON' : 'OFF'}
              </Button>
            </div>
            <Button variant="ghost" size="sm" onClick={handleLogout} className="text-slate-700 hover:text-red-600 hover:bg-red-50">
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Card className="bg-gradient-to-br from-blue-50 to-blue-100/50 shadow-md hover:shadow-lg transition-all duration-300 border-blue-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">Scheduled</p>
                  <p className="text-4xl font-bold text-blue-600 mt-2">{stats.scheduled_count || 0}</p>
                  <p className="text-xs text-slate-500 mt-2">Coming soon</p>
                </div>
                <Calendar className="w-12 h-12 text-blue-400 opacity-80" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-green-50 to-green-100/50 shadow-md hover:shadow-lg transition-all duration-300 border-green-200 border-2">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">Active Now</p>
                  <p className="text-4xl font-bold text-green-600 mt-2 flex items-center gap-2">
                    {stats.active_count}
                    {stats.active_count > 0 && <span className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>}
                  </p>
                  <p className="text-xs text-slate-500 mt-2">Live assessments</p>
                </div>
                <Zap className="w-12 h-12 text-green-400 opacity-80" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100/50 shadow-md hover:shadow-lg transition-all duration-300 border-emerald-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">Completed Today</p>
                  <p className="text-4xl font-bold text-emerald-600 mt-2">{stats.completed_today || 0}</p>
                  <p className="text-xs text-slate-500 mt-2">Finished</p>
                </div>
                <CheckCircle className="w-12 h-12 text-emerald-400 opacity-80" />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-red-50 to-red-100/50 shadow-md hover:shadow-lg transition-all duration-300 border-red-200">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-600 text-sm font-medium">Violations Today</p>
                  <p className="text-4xl font-bold text-red-600 mt-2">{stats.violations_today}</p>
                  <p className="text-xs text-slate-500 mt-2">Flagged</p>
                </div>
                <AlertTriangle className="w-12 h-12 text-red-400 opacity-80" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs defaultValue="active" className="space-y-6">
          <TabsList className="bg-white shadow-md border-slate-200">
            <TabsTrigger value="active" className="data-[state=active]:bg-green-600 data-[state=active]:text-white relative">
              <Activity className="w-4 h-4 mr-2" />
              Active
              {stats.active_count > 0 && (
                <span className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                  {stats.active_count}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="scheduled" className="data-[state=active]:bg-blue-600 data-[state=active]:text-white">
              <Calendar className="w-4 h-4 mr-2" />
              Scheduled ({scheduledAssessments.length})
            </TabsTrigger>
            <TabsTrigger value="completed" className="data-[state=active]:bg-emerald-600 data-[state=active]:text-white">
              <CheckCircle className="w-4 h-4 mr-2" />
              Completed
            </TabsTrigger>
          </TabsList>

          {/* Global Search & Filter */}
          <div className="flex gap-3 flex-col md:flex-row md:items-center">
            <div className="flex-1 flex items-center gap-2 bg-slate-50 rounded-lg p-3 border border-slate-200">
              <Search className="w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search candidates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-transparent border-0 focus:ring-0 flex-1 text-slate-900 placeholder:text-slate-500 outline-none"
              />
            </div>
          </div>

          {/* Active Assessments Tab */}
          <TabsContent value="active">
            <Card className="bg-white shadow-md hover:shadow-xl transition-all duration-300 border-slate-200">
              <CardHeader>
                <CardTitle className="text-slate-900 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-green-400 animate-pulse" />
                  Live Assessments
                </CardTitle>
                <CardDescription className="text-slate-600">
                  Currently active assessments being monitored
                </CardDescription>
              </CardHeader>
              <CardContent>
                {activeAssessments.length === 0 ? (
                  <div className="text-center py-12">
                    <Video className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-600 text-lg">No active assessments at the moment</p>
                    <p className="text-slate-500 text-sm mt-2">Active assessments will appear here for monitoring</p>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {activeAssessments.map((assessment) => (
                      <Card key={assessment.id} className="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50/50 border-green-500/30 border-2">
                        <CardContent className="pt-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-12 h-12 bg-green-600/20 rounded-full flex items-center justify-center">
                                <Video className="w-6 h-6 text-green-400" />
                              </div>
                              <div>
                                <h3 className="text-slate-900 font-semibold text-lg">{assessment.candidate_name}</h3>
                                <p className="text-slate-600 text-sm">{assessment.candidate_email}</p>
                                <p className="text-slate-500 text-xs mt-1">
                                  Started: {formatDateTime(assessment.started_at)}
                                </p>
                              </div>
                            </div>
                            <div className="flex flex-col items-end gap-3">
                              <div className="flex items-center gap-2">
                                <Badge className="bg-green-600 animate-pulse">
                                  <Activity className="w-3 h-3 mr-1" />
                                  LIVE
                                </Badge>
                                {assessment.proctoring_violations > 0 && (
                                  <Badge className="bg-amber-600">
                                    <AlertTriangle className="w-3 h-3 mr-1" />
                                    {assessment.proctoring_violations} violations
                                  </Badge>
                                )}
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  size="sm"
                                  className="bg-purple-600 hover:bg-purple-700 text-white h-8 text-xs px-3"
                                  onClick={() => setMonitoringAssessmentId(assessment.assessment_id)}
                                >
                                  <Video className="w-3 h-3 mr-1" />
                                  Monitor Live
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-8 text-xs px-3 border-slate-300 hover:bg-white shadow-md text-slate-700"
                                  onClick={() => handleViewViolations(assessment.assessment_id)}
                                >
                                  <Eye className="w-3 h-3 mr-1" />
                                  View
                                </Button>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Scheduled Tab */}
          <TabsContent value="scheduled">
            <Card className="bg-white shadow-md hover:shadow-lg transition-all duration-300 border-slate-200">
              <CardHeader className="border-b border-slate-200 pb-4">
                <CardTitle className="text-slate-900">Upcoming Assessments</CardTitle>
                <CardDescription className="text-slate-600 mt-1">
                  {filteredScheduled.length} assessment{filteredScheduled.length !== 1 ? 's' : ''} scheduled
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {filteredScheduled.length === 0 ? (
                  <div className="text-center py-12">
                    <Calendar className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-600 text-lg font-medium">No scheduled assessments</p>
                    <p className="text-slate-500 text-sm mt-2">Scheduled assessments will appear here soon</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-200 bg-slate-50 hover:bg-slate-50">
                          <TableHead className="text-slate-700 font-semibold">Candidate</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Email</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Scheduled Time</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Starts In</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredScheduled.map((assessment) => (
                          <TableRow key={assessment.id} className="border-slate-100 hover:bg-slate-50 transition-colors">
                            <TableCell className="text-slate-900 font-medium">{assessment.candidate_name}</TableCell>
                            <TableCell className="text-slate-600">{assessment.candidate_email}</TableCell>
                            <TableCell className="text-slate-600">{formatDateTime(assessment.scheduled_time)}</TableCell>
                            <TableCell>
                              <Badge className={`${getTimeUntil(assessment.scheduled_time) === 'Overdue'
                                ? 'bg-red-600'
                                : 'bg-blue-600'
                                } text-white shadow-sm`}>
                                {getTimeUntil(assessment.scheduled_time)}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              <Badge className="bg-slate-600 text-white shadow-sm">{assessment.status}</Badge>
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

          {/* Completed Tab */}
          <TabsContent value="completed">
            <Card className="bg-white shadow-md hover:shadow-lg transition-all duration-300 border-slate-200">
              <CardHeader className="border-b border-slate-200 pb-4">
                <CardTitle className="text-slate-900">Completed Assessments</CardTitle>
                <CardDescription className="text-slate-600 mt-1">
                  {filteredCompleted.length} assessment{filteredCompleted.length !== 1 ? 's' : ''} completed
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-6">
                {filteredCompleted.length === 0 ? (
                  <div className="text-center py-12">
                    <CheckCircle className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-600 text-lg font-medium">No completed assessments</p>
                    <p className="text-slate-500 text-sm mt-2">Completed assessments will appear here</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-slate-200 bg-slate-50 hover:bg-slate-50">
                          <TableHead className="text-slate-700 font-semibold">Candidate</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Completed At</TableHead>
                          <TableHead className="text-slate-700 font-semibold">MCQ</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Coding</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Overall</TableHead>
                          <TableHead className="text-slate-700 font-semibold">Violations</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredCompleted.map((assessment) => (
                          <TableRow key={assessment.id} className="border-slate-100 hover:bg-slate-50 transition-colors">
                            <TableCell className="text-slate-900 font-medium">{assessment.candidate_name}</TableCell>
                            <TableCell className="text-slate-600 text-sm">{formatDateTime(assessment.completed_at)}</TableCell>
                            <TableCell className="text-slate-600">{assessment.mcq_score || 0}%</TableCell>
                            <TableCell className="text-slate-600">{assessment.coding_score || 0}%</TableCell>
                            <TableCell>
                              <Badge className={`${(assessment.overall_score || 0) >= 70 ? 'bg-green-600' :
                                (assessment.overall_score || 0) >= 50 ? 'bg-amber-600' : 'bg-red-600'
                                } text-white shadow-sm`}>
                                {assessment.overall_score || 0}%
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {(assessment.proctoring_violations || 0) > 0 ? (
                                <div className="flex items-center gap-2">
                                  <Badge className="bg-red-600 text-white shadow-sm">
                                    <AlertTriangle className="w-3 h-3 mr-1" />
                                    {assessment.proctoring_violations}
                                  </Badge>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-6 w-6 p-0 text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                                    onClick={() => handleViewViolations(assessment.id)}
                                  >
                                    <Eye className="w-4 h-4" />
                                  </Button>
                                </div>
                              ) : (
                                <Badge className="bg-green-600 text-white shadow-sm">
                                  <Shield className="w-3 h-3 mr-1" />
                                  Clean
                                </Badge>
                              )}
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
        </Tabs>
      </main>
      {/* Violations Details Modal */}
      <Dialog open={violationsModalOpen} onOpenChange={setViolationsModalOpen}>
        <DialogContent className="bg-white shadow-md border-slate-200 max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-slate-900">Proctoring Violations Log</DialogTitle>
            <DialogDescription className="text-slate-600">
              Detailed record of detected violations for this assessment
            </DialogDescription>
          </DialogHeader>

          <div className="py-4">
            {loadingViolations ? (
              <div className="text-center py-8 text-slate-600">Loading violations...</div>
            ) : selectedViolations.length === 0 ? (
              <div className="text-center py-12 border-2 border-dashed border-slate-200 rounded-lg">
                <Shield className="w-12 h-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-700 font-medium">No violations recorded</p>
                <p className="text-slate-500 text-sm">This assessment appears clean</p>
              </div>
            ) : (
              <div className="space-y-4">
                {selectedViolations.map((violation) => {
                  // Only show screenshots for visual violations
                  const shouldShowScreenshot = ['no_face', 'multiple_faces', 'unknown_person'].includes(violation.violation_type);

                  return (
                    <div key={violation.id} className="bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50/50 border border-slate-200 rounded-lg p-4 flex gap-4">
                      {shouldShowScreenshot && (
                        <div className="flex-shrink-0">
                          {violation.screenshot_url ? (
                            <div className="w-32 h-20 bg-black rounded overflow-hidden border border-slate-300 relative">
                              <img
                                src={`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}${violation.screenshot_url}`}
                                alt="Violation screenshot"
                                className="w-full h-full object-cover cursor-pointer hover:scale-110 transition-transform"
                                onClick={() => window.open(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'}${violation.screenshot_url}`, '_blank')}
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.nextSibling.style.display = 'flex';
                                }}
                              />
                              <div className="absolute inset-0 items-center justify-center bg-slate-100 text-xs text-slate-500 hidden">
                                📷 Screenshot unavailable
                              </div>
                            </div>
                          ) : (
                            <div className="w-32 h-20 bg-slate-100 rounded flex items-center justify-center border border-slate-200">
                              <Eye className="w-6 h-6 text-slate-400" />
                            </div>
                          )}
                        </div>
                      )}
                      <div className="flex-1">
                        <div className="flex justify-between items-start mb-1">
                          <h4 className="text-slate-900 font-medium capitalize">{violation.violation_type.replace('_', ' ')}</h4>
                          <span className="text-xs text-slate-600 font-mono">
                            {new Date(violation.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <p className="text-slate-600 text-sm mb-2">{violation.description || 'Suspicious activity detected'}</p>
                        <Badge className={
                          violation.severity === 'high' ? 'bg-red-900 text-red-200 border-red-800' :
                            violation.severity === 'medium' ? 'bg-amber-900 text-amber-200 border-amber-800' :
                              'bg-blue-900 text-blue-200 border-blue-800'
                        }>
                          {violation.severity} severity
                        </Badge>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Live Proctoring Monitor */}
      {monitoringAssessmentId && (
        <ProctorMonitor
          assessmentId={monitoringAssessmentId}
          onClose={() => setMonitoringAssessmentId(null)}
        />
      )}
    </div>
  );
};

export default ProctorDashboardPage;
