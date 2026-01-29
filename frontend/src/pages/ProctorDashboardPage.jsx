import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  LogOut, Eye, Users, Clock, CheckCircle, AlertTriangle, RefreshCw,
  Video, Calendar, Activity, Shield
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { api } from '../services/api';

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

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900">
        <div className="text-white text-xl">Loading proctor dashboard...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Logo size="default" />
            <Badge className="bg-indigo-600 text-white border-indigo-500">
              <Eye className="w-3 h-3 mr-1" />
              PROCTOR
            </Badge>
          </div>
          <div className="flex gap-2 items-center">
            <div className="flex items-center gap-2 mr-4">
              <span className="text-slate-400 text-sm">Auto-refresh</span>
              <Button
                size="sm"
                variant={autoRefresh ? 'default' : 'outline'}
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={autoRefresh ? 'bg-green-600 hover:bg-green-700' : 'border-slate-600'}
              >
                {autoRefresh ? 'ON' : 'OFF'}
              </Button>
            </div>
            <Button variant="outline" onClick={() => fetchAllData()} className="border-slate-600 text-slate-300 hover:bg-slate-800">
              <RefreshCw className="w-4 h-4 mr-2" />
              Refresh
            </Button>
            <Button variant="ghost" onClick={handleLogout} className="text-slate-300 hover:text-red-400">
              <LogOut className="mr-2 w-4 h-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Scheduled</p>
                  <p className="text-3xl font-bold text-white">{stats.scheduled_count}</p>
                </div>
                <Calendar className="w-10 h-10 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700 border-2 border-green-500/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Active Now</p>
                  <p className="text-3xl font-bold text-green-400">{stats.active_count}</p>
                </div>
                <Activity className="w-10 h-10 text-green-400 animate-pulse" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Completed Today</p>
                  <p className="text-3xl font-bold text-white">{stats.completed_today}</p>
                </div>
                <CheckCircle className="w-10 h-10 text-emerald-400" />
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-slate-800/50 border-slate-700">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-slate-400 text-sm">Violations Today</p>
                  <p className="text-3xl font-bold text-amber-400">{stats.violations_today}</p>
                </div>
                <AlertTriangle className="w-10 h-10 text-amber-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Tabs */}
        <Tabs defaultValue="active" className="space-y-6">
          <TabsList className="bg-slate-800 border-slate-700">
            <TabsTrigger value="active" className="data-[state=active]:bg-green-600">
              <Activity className="w-4 h-4 mr-2" />
              Active ({activeAssessments.length})
            </TabsTrigger>
            <TabsTrigger value="scheduled" className="data-[state=active]:bg-slate-700">
              <Calendar className="w-4 h-4 mr-2" />
              Scheduled ({scheduledAssessments.length})
            </TabsTrigger>
            <TabsTrigger value="completed" className="data-[state=active]:bg-slate-700">
              <CheckCircle className="w-4 h-4 mr-2" />
              Completed
            </TabsTrigger>
          </TabsList>

          {/* Active Assessments Tab */}
          <TabsContent value="active">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Activity className="w-5 h-5 text-green-400 animate-pulse" />
                  Live Assessments
                </CardTitle>
                <CardDescription className="text-slate-400">
                  Currently active assessments being monitored
                </CardDescription>
              </CardHeader>
              <CardContent>
                {activeAssessments.length === 0 ? (
                  <div className="text-center py-12">
                    <Video className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                    <p className="text-slate-400 text-lg">No active assessments at the moment</p>
                    <p className="text-slate-500 text-sm mt-2">Active assessments will appear here for monitoring</p>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {activeAssessments.map((assessment) => (
                      <Card key={assessment.id} className="bg-slate-900/50 border-green-500/30 border-2">
                        <CardContent className="pt-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-12 h-12 bg-green-600/20 rounded-full flex items-center justify-center">
                                <Video className="w-6 h-6 text-green-400" />
                              </div>
                              <div>
                                <h3 className="text-white font-semibold text-lg">{assessment.candidate_name}</h3>
                                <p className="text-slate-400 text-sm">{assessment.candidate_email}</p>
                                <p className="text-slate-500 text-xs mt-1">
                                  Started: {formatDateTime(assessment.started_at)}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3">
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
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Upcoming Assessments</CardTitle>
                <CardDescription className="text-slate-400">Assessments scheduled for today and upcoming</CardDescription>
              </CardHeader>
              <CardContent>
                {scheduledAssessments.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">No scheduled assessments</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-700">
                        <TableHead className="text-slate-300">Candidate</TableHead>
                        <TableHead className="text-slate-300">Email</TableHead>
                        <TableHead className="text-slate-300">Scheduled Time</TableHead>
                        <TableHead className="text-slate-300">Starts In</TableHead>
                        <TableHead className="text-slate-300">Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {scheduledAssessments.map((assessment) => (
                        <TableRow key={assessment.id} className="border-slate-700">
                          <TableCell className="text-white font-medium">{assessment.candidate_name}</TableCell>
                          <TableCell className="text-slate-300">{assessment.candidate_email}</TableCell>
                          <TableCell className="text-slate-300">{formatDateTime(assessment.scheduled_time)}</TableCell>
                          <TableCell>
                            <Badge className={
                              getTimeUntil(assessment.scheduled_time) === 'Overdue' 
                                ? 'bg-red-600' 
                                : 'bg-blue-600'
                            }>
                              {getTimeUntil(assessment.scheduled_time)}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Badge className="bg-slate-600">{assessment.status}</Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Completed Tab */}
          <TabsContent value="completed">
            <Card className="bg-slate-800/50 border-slate-700">
              <CardHeader>
                <CardTitle className="text-white">Completed Assessments</CardTitle>
                <CardDescription className="text-slate-400">Recently completed assessments with results</CardDescription>
              </CardHeader>
              <CardContent>
                {completedAssessments.length === 0 ? (
                  <p className="text-slate-400 text-center py-8">No completed assessments</p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow className="border-slate-700">
                        <TableHead className="text-slate-300">Candidate</TableHead>
                        <TableHead className="text-slate-300">Completed At</TableHead>
                        <TableHead className="text-slate-300">MCQ</TableHead>
                        <TableHead className="text-slate-300">Coding</TableHead>
                        <TableHead className="text-slate-300">Overall</TableHead>
                        <TableHead className="text-slate-300">Violations</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {completedAssessments.map((assessment) => (
                        <TableRow key={assessment.id} className="border-slate-700">
                          <TableCell className="text-white font-medium">{assessment.candidate_name}</TableCell>
                          <TableCell className="text-slate-300">{formatDateTime(assessment.completed_at)}</TableCell>
                          <TableCell className="text-slate-300">{assessment.mcq_score || 0}%</TableCell>
                          <TableCell className="text-slate-300">{assessment.coding_score || 0}%</TableCell>
                          <TableCell>
                            <Badge className={
                              (assessment.overall_score || 0) >= 70 ? 'bg-green-600' :
                              (assessment.overall_score || 0) >= 50 ? 'bg-amber-600' : 'bg-red-600'
                            }>
                              {assessment.overall_score || 0}%
                            </Badge>
                          </TableCell>
                          <TableCell>
                            {(assessment.proctoring_violations || 0) > 0 ? (
                              <Badge className="bg-red-600">
                                <AlertTriangle className="w-3 h-3 mr-1" />
                                {assessment.proctoring_violations}
                              </Badge>
                            ) : (
                              <Badge className="bg-green-600">
                                <Shield className="w-3 h-3 mr-1" />
                                Clean
                              </Badge>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default ProctorDashboardPage;
