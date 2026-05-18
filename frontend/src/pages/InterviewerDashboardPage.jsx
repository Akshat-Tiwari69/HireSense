import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { LogOut, Search, Filter, Calendar, CheckCircle, XCircle, Clock, ThumbsUp, ThumbsDown, Users, BarChart3, Settings, X, Plus, Download, LayoutDashboard, Shield, Eye, Loader, TrendingUp, Activity, AlertCircle, Code, FileText, Upload, BookOpen } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { api } from '../services/api';
import ProctorMonitor from '../components/ProctorMonitor';
import { useRealtimeTable } from '../hooks/useRealtimeTable';
import RealtimeIndicator from '../components/common/RealtimeIndicator';
import ScheduleModal from '../components/interviewer/ScheduleModal';
import CandidateDetailsModal from '../components/interviewer/CandidateDetailsModal';

const InterviewerDashboardPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // Realtime subscription for candidates
  const {
    data: realtimeCandidates,
    setData: setRealtimeCandidates,
    isConnected: candidatesConnected
  } = useRealtimeTable('candidates', [], {
    onUpdate: (newCandidate) => {
      toast({
        title: " Candidate Updated",
        description: `${newCandidate.name}'s status changed`,
        duration: 3000
      });
    }
  });

  const [filteredCandidates, setFilteredCandidates] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [scoreFilter, setScoreFilter] = useState('all');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [isTechnicalRole, setIsTechnicalRole] = useState(true);
  const [customQFile, setCustomQFile] = useState(null);
  const [customQUploading, setCustomQUploading] = useState(false);
  const [skillsModalOpen, setSkillsModalOpen] = useState(false);
  const [desiredSkills, setDesiredSkills] = useState([]);
  const [newSkill, setNewSkill] = useState('');

  // New state for detailed view and decisions
  const [viewDetailsModalOpen, setViewDetailsModalOpen] = useState(false);
  const [assessmentDetails, setAssessmentDetails] = useState(null);
  const [decisionLoading, setDecisionLoading] = useState(false);

  // Live monitoring state
  const [monitoringAssessmentId, setMonitoringAssessmentId] = useState(null);

  // Loading states
  const [isLoading, setIsLoading] = useState(true);
  const [rejectingCandidateId, setRejectingCandidateId] = useState(null);
  const [schedulingLoading, setSchedulingLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (!token) {
      navigate('/login');
      return;
    }

    // Load desired skills from localStorage
    const saved = localStorage.getItem('desiredSkills');
    if (saved) {
      setDesiredSkills(JSON.parse(saved));
    }

    fetchCandidates();
  }, [navigate, toast]);

  // Memoized stats calculations - Vercel React Best Practices
  const stats = useMemo(() => ({
    total: realtimeCandidates.length,
    highMatch: realtimeCandidates.filter(c => c.aiMatchScore >= 85).length,
    scheduled: realtimeCandidates.filter(c => c.status === 'Scheduled').length,
    completed: realtimeCandidates.filter(c => c.status === 'Completed').length,
    hired: realtimeCandidates.filter(c => c.status === 'Hired').length,
  }), [realtimeCandidates]);

  const fetchCandidates = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/api/interviewer/candidates');
      const list = res?.data?.data || [];

      // Normalize status to display format
      const normalizeStatus = (status) => {
        const statusMap = {
          'applied': 'Applied',
          'pending': 'Pending',
          'scheduled': 'Scheduled',
          'in_progress': 'In Progress',
          'completed': 'Completed',
          'under_review': 'Under Review',
          'rejected': 'Rejected',
          'hired': 'Hired'
        };
        return statusMap[status?.toLowerCase()] || status || 'Pending';
      };

      const mapped = list.map((c) => {
        const normalizedStatus = normalizeStatus(c.status || c.shortlist_status);

        return {
          id: c.id,
          name: c.name,
          email: c.email,
          status: normalizedStatus,
          aiMatchScore: Math.round(Number(c.match_score) || 0),
          assessmentDecision: c.assessment_decision,
          assessmentScheduled: c.assessment_date || null,
          pros: Array.isArray(c.pros) ? c.pros : (c.pros ? c.pros.split('\n') : []),
          cons: Array.isArray(c.cons) ? c.cons : (c.cons ? c.cons.split('\n') : []),
        };
      });

      // Update realtime data
      setRealtimeCandidates(mapped);
      setFilteredCandidates(mapped);
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to load candidates';
      toast({ variant: 'destructive', title: 'Load failed', description: message });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  const handleDownloadResume = useCallback(async (candidateId) => {
    try {
      const response = await api.get(`/api/interviewer/candidates/${candidateId}/resume`, {
        responseType: 'blob'
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `resume_${candidateId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      toast({ title: 'Success', description: 'Resume downloaded successfully' });
    } catch (err) {
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to download resume' });
    }
  }, [toast]);

  // Filter logic - memoized for performance (Vercel React Best Practices)
  useEffect(() => {
    let filtered = realtimeCandidates;

    // Search filter
    if (searchTerm) {
      const lowerTerm = searchTerm.toLowerCase();
      filtered = filtered.filter(c =>
        c.name.toLowerCase().includes(lowerTerm) ||
        c.email.toLowerCase().includes(lowerTerm)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(c => c.status.toLowerCase() === statusFilter.toLowerCase());
    }

    // Score filter
    if (scoreFilter !== 'all') {
      if (scoreFilter === 'high') {
        filtered = filtered.filter(c => c.aiMatchScore >= 85);
      } else if (scoreFilter === 'medium') {
        filtered = filtered.filter(c => c.aiMatchScore >= 70 && c.aiMatchScore < 85);
      } else if (scoreFilter === 'low') {
        filtered = filtered.filter(c => c.aiMatchScore < 70);
      }
    }

    setFilteredCandidates(filtered);
  }, [searchTerm, statusFilter, scoreFilter, realtimeCandidates]);

  const handleLogout = useCallback(() => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    navigate('/login');
  }, [navigate]);

  const handleAddSkill = useCallback(() => {
    if (newSkill.trim() && !desiredSkills.includes(newSkill.trim())) {
      const updated = [...desiredSkills, newSkill.trim()];
      setDesiredSkills(updated);
      localStorage.setItem('desiredSkills', JSON.stringify(updated));
      setNewSkill('');
      toast({
        title: 'Skill added',
        description: `${newSkill} added to desired skills`,
      });
    }
  }, [newSkill, desiredSkills, toast]);

  const handleRemoveSkill = useCallback((skill) => {
    const updated = desiredSkills.filter(s => s !== skill);
    setDesiredSkills(updated);
    localStorage.setItem('desiredSkills', JSON.stringify(updated));
  }, [desiredSkills]);

  const handleReject = useCallback(async (candidateId) => {
    setRejectingCandidateId(candidateId);
    try {
      await api.post(`/api/interviewer/candidates/${candidateId}/reject`, { reason: '' });
      setRealtimeCandidates(prev => prev.map(c =>
        c.id === candidateId ? { ...c, status: 'Rejected' } : c
      ));
      toast({
        title: 'Candidate rejected',
        description: 'Rejection email sent',
      });
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to reject candidate';
      toast({ variant: 'destructive', title: 'Action failed', description: message });
    } finally {
      setRejectingCandidateId(null);
    }
  }, [toast]);

  const handleSchedule = useCallback(async () => {
    if (!scheduleDate || !scheduleTime) {
      toast({
        variant: 'destructive',
        title: 'Missing information',
        description: 'Please select both date and time',
      });
      return;
    }

    setSchedulingLoading(true);
    const scheduledDateTime = `${scheduleDate}T${scheduleTime}:00`;
    try {
      // If a custom question file was attached, upload it first
      if (customQFile) {
        setCustomQUploading(true);
        const formData = new FormData();
        formData.append('file', customQFile);
        formData.append('description', `Uploaded during scheduling for ${selectedCandidate?.name}`);
        formData.append('tags', 'schedule-upload');
        try {
          await api.post('/api/admin/question-bank/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
          });
        } catch (qErr) {
          console.warn('Custom question upload failed, proceeding with schedule:', qErr);
        } finally {
          setCustomQUploading(false);
        }
      }

      await api.post(`/api/interviewer/candidates/${selectedCandidate.id}/schedule`, {
        scheduled_time: scheduledDateTime,
        is_technical_role: isTechnicalRole,
      });
      setRealtimeCandidates(prev => prev.map(c =>
        c.id === selectedCandidate.id
          ? { ...c, status: 'Scheduled', assessmentScheduled: scheduledDateTime, isTechnicalRole }
          : c
      ));
      toast({
        title: 'Assessment scheduled',
        description: `Candidate will receive email with assessment link for ${scheduleDate} at ${scheduleTime}`,
      });
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to schedule assessment';
      toast({ variant: 'destructive', title: 'Schedule failed', description: message });
    } finally {
      setSchedulingLoading(false);
      setScheduleModalOpen(false);
      setScheduleDate('');
      setScheduleTime('');
      setIsTechnicalRole(true);
      setCustomQFile(null);
      setSelectedCandidate(null);
    }
  }, [selectedCandidate, scheduleDate, scheduleTime, toast]);

  const handleOpenDetails = useCallback(async (candidate) => {
    setSelectedCandidate(candidate);
    setAssessmentDetails(null);
    setViewDetailsModalOpen(true);

    // If completed or hired/rejected, fetch assessment details
    if (['Completed', 'Hired', 'Rejected'].includes(candidate.status)) {
      try {
        const res = await api.get(`/api/interviewer/assessments/${candidate.id}`);
        setAssessmentDetails(res.data.data);
      } catch (err) {
        console.error("Failed to fetch assessment details", err);
      }
    }
  }, []);

  const handleFinalDecision = useCallback(async (decision) => {
    if (!assessmentDetails?.id) return;

    setDecisionLoading(true);
    try {
      await api.post(`/api/interviewer/assessments/${assessmentDetails.id}/final-decision`, {
        decision: decision,
        rationale: decision === 'hire' ? 'Candidate meets all requirements.' : 'Candidate does not meet requirements.'
      });

      toast({
        title: 'Success',
        description: `Candidate ${decision === 'hire' ? 'hired' : 'rejected'} successfully.`
      });
      setViewDetailsModalOpen(false);
      fetchCandidates(); // Refresh list
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to record decision';
      toast({ variant: 'destructive', title: 'Error', description: message });
    } finally {
      setDecisionLoading(false);
    }
  }, [assessmentDetails, toast, fetchCandidates]);

  // Color utilities - theme-factory pattern
  const getScoreBadgeColor = useCallback((score) => {
    if (score >= 85) return 'bg-emerald-100 text-emerald-800 border-emerald-300 shadow-sm';
    if (score >= 70) return 'bg-amber-100 text-amber-800 border-amber-300 shadow-sm';
    return 'bg-red-100 text-red-800 border-red-300 shadow-sm';
  }, []);

  const getStatusBadge = useCallback((status) => {
    const styles = {
      'Applied': 'bg-blue-100 text-blue-800 border-blue-300 shadow-sm',
      'Pending': 'bg-slate-100 text-slate-800 border-slate-300 shadow-sm',
      'Scheduled': 'bg-purple-100 text-purple-800 border-purple-300 shadow-sm',
      'In Progress': 'bg-yellow-100 text-yellow-800 border-yellow-300 shadow-sm',
      'Completed': 'bg-emerald-100 text-emerald-800 border-emerald-300 shadow-sm',
      'Under Review': 'bg-indigo-100 text-indigo-800 border-indigo-300 shadow-sm',
      'Rejected': 'bg-red-100 text-red-800 border-red-300 shadow-sm',
      'Hired': 'bg-green-100 text-green-800 border-green-300 shadow-sm'
    };
    return styles[status] || 'bg-slate-100 text-slate-800 border-slate-300 shadow-sm';
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-xl sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Logo size="default" />
            <Badge className="bg-indigo-600 text-white font-semibold">INTERVIEWER</Badge>
            {candidatesConnected && (
              <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 ml-2">
                <div className="w-2 h-2 bg-emerald-600 rounded-full animate-pulse" />
                Live
              </div>
            )}
          </div>
          <div className="flex gap-2 items-center">
            <Dialog open={skillsModalOpen} onOpenChange={setSkillsModalOpen}>
              <DialogTrigger asChild>
                <Button
                  variant="outline"
                  className="text-slate-700 hover:text-indigo-600 hover:border-indigo-300 transition-colors text-sm sm:text-base"
                >
                  <Settings className="mr-2 w-4 h-4" />
                  <span className="hidden sm:inline">Skills</span>
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Configure Desired Skills</DialogTitle>
                  <DialogDescription>
                    Set the skills you want to prioritize when evaluating candidates
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4 py-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="e.g., Python, React, AWS..."
                      value={newSkill}
                      onChange={(e) => setNewSkill(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleAddSkill()}
                    />
                    <Button onClick={handleAddSkill} className="bg-indigo-600 hover:bg-indigo-700">
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>

                  {desiredSkills.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold mb-2 text-slate-700">Current skills:</p>
                      <div className="flex flex-wrap gap-2">
                        {desiredSkills.map((skill) => (
                          <Badge key={skill} className="bg-indigo-100 text-indigo-800 border border-indigo-300 flex items-center gap-1 py-1 px-3">
                            {skill}
                            <button
                              onClick={() => handleRemoveSkill(skill)}
                              className="ml-1 hover:text-red-600"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {desiredSkills.length === 0 && (
                    <p className="text-sm text-slate-500 text-center py-4">No skills added yet. Add your first skill above.</p>
                  )}
                </div>
              </DialogContent>
            </Dialog>
            <Button
              variant="ghost"
              onClick={handleLogout}
              className="text-slate-700 hover:text-red-600 hover:bg-red-50 transition-colors text-sm sm:text-base"
            >
              <LogOut className="mr-2 w-4 h-4" />
              <span className="hidden sm:inline">Logout</span>
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {/* Stats Cards - Enhanced UI/UX */}
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4 mb-8">
          <Card className="border-none shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-600 mb-1 font-medium">Total</p>
                  <p className="text-2xl sm:text-3xl font-bold text-slate-900">{stats.total}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
                  <Users className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-none shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-600 mb-1 font-medium">High Match</p>
                  <p className="text-2xl sm:text-3xl font-bold text-emerald-600">{stats.highMatch}</p>
                </div>
                <div className="p-3 bg-emerald-100 rounded-lg group-hover:bg-emerald-200 transition-colors">
                  <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6 text-emerald-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-none shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-600 mb-1 font-medium">Scheduled</p>
                  <p className="text-2xl sm:text-3xl font-bold text-purple-600">{stats.scheduled}</p>
                </div>
                <div className="p-3 bg-purple-100 rounded-lg group-hover:bg-purple-200 transition-colors">
                  <Calendar className="w-5 h-5 sm:w-6 sm:h-6 text-purple-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-none shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-600 mb-1 font-medium">Completed</p>
                  <p className="text-2xl sm:text-3xl font-bold text-blue-600">{stats.completed}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-lg group-hover:bg-blue-200 transition-colors">
                  <Activity className="w-5 h-5 sm:w-6 sm:h-6 text-blue-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-none shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-1 group bg-white">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs sm:text-sm text-slate-600 mb-1 font-medium">Hired</p>
                  <p className="text-2xl sm:text-3xl font-bold text-green-600">{stats.hired}</p>
                </div>
                <div className="p-3 bg-green-100 rounded-lg group-hover:bg-green-200 transition-colors">
                  <CheckCircle className="w-5 h-5 sm:w-6 sm:h-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters - Enhanced UI/UX */}
        <Card className="mb-6 border-none shadow-md hover:shadow-lg transition-shadow">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                <Input
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 border-slate-200 focus:border-indigo-400 focus:ring-indigo-200 transition-all"
                />
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full md:w-48 border-slate-200 hover:border-indigo-300 transition-colors">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="Applied">Applied</SelectItem>
                  <SelectItem value="Scheduled">Scheduled</SelectItem>
                  <SelectItem value="In Progress">In Progress</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                  <SelectItem value="Under Review">Under Review</SelectItem>
                  <SelectItem value="Rejected">Rejected</SelectItem>
                  <SelectItem value="Hired">Hired</SelectItem>
                </SelectContent>
              </Select>
              <Select value={scoreFilter} onValueChange={setScoreFilter}>
                <SelectTrigger className="w-full md:w-48 border-slate-200 hover:border-indigo-300 transition-colors">
                  <SelectValue placeholder="Score Range" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Scores</SelectItem>
                  <SelectItem value="high">High (85+)</SelectItem>
                  <SelectItem value="medium">Medium (70-84)</SelectItem>
                  <SelectItem value="low">Low (&lt;70)</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Candidates Table - Enhanced UI/UX */}
        <Card className="border-none shadow-md hover:shadow-lg transition-shadow">
          <CardHeader className="border-b border-slate-100">
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl font-bold">Candidates</CardTitle>
              <div className="text-sm text-slate-600">
                {isLoading ? (
                  <div className="flex items-center gap-2">
                    <Loader className="w-4 h-4 animate-spin" />
                    Loading...
                  </div>
                ) : (
                  `${filteredCandidates.length} of ${realtimeCandidates.length}`
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-slate-100 overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="bg-slate-50 hover:bg-slate-50 border-slate-100">
                    <TableHead className="font-semibold text-slate-700">Name</TableHead>
                    <TableHead className="font-semibold text-slate-700">Email</TableHead>
                    <TableHead className="font-semibold text-slate-700">AI Score</TableHead>
                    <TableHead className="font-semibold text-slate-700">Status</TableHead>
                    <TableHead className="font-semibold text-slate-700 text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-12">
                        <div className="flex justify-center items-center gap-2">
                          <Loader className="w-5 h-5 animate-spin text-indigo-600" />
                          <span className="text-slate-600">Loading candidates...</span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ) : filteredCandidates.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="text-center py-12 text-slate-500">
                        No candidates found
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredCandidates.map((candidate) => (
                      <TableRow key={candidate.id} className="hover:bg-indigo-50 transition-colors border-slate-100">
                        <TableCell className="font-medium text-slate-900">{candidate.name}</TableCell>
                        <TableCell className="text-slate-600">{candidate.email}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={`${candidate.status === 'Completed' ? 'bg-indigo-600 text-white' : getScoreBadgeColor(candidate.aiMatchScore)} font-bold shadow-sm px-3 py-1`}
                          >
                            {candidate.aiMatchScore}%
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline" className={`${getStatusBadge(candidate.status)} font-medium w-fit`}>
                            {candidate.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex gap-2 justify-end">
                            <Button
                              size="sm"
                              variant="outline"
                              className="hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-300 transition-colors"
                              onClick={() => handleOpenDetails(candidate)}
                            >
                              View
                            </Button>

                            {candidate.status === 'In Progress' && (
                              <Button
                                size="sm"
                                className="bg-purple-600 hover:bg-purple-700 text-white transition-colors"
                                onClick={() => setMonitoringAssessmentId(candidate.id)}
                              >
                                Monitor
                              </Button>
                            )}

                            {candidate.status === 'Applied' && (
                              <>
                                <Button
                                  size="sm"
                                  onClick={() => {
                                    setSelectedCandidate(candidate);
                                    setScheduleModalOpen(true);
                                  }}
                                  className="bg-emerald-600 hover:bg-emerald-700 text-white transition-colors"
                                >
                                  Schedule
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  onClick={() => handleReject(candidate.id)}
                                  disabled={rejectingCandidateId === candidate.id}
                                  className="transition-colors min-w-[70px]"
                                >
                                  {rejectingCandidateId === candidate.id ? (
                                    <Loader className="w-4 h-4 animate-spin" />
                                  ) : (
                                    'Reject'
                                  )}
                                </Button>
                              </>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      <ScheduleModal
        open={scheduleModalOpen}
        onOpenChange={setScheduleModalOpen}
        selectedCandidate={selectedCandidate}
        scheduleDate={scheduleDate}
        setScheduleDate={setScheduleDate}
        scheduleTime={scheduleTime}
        setScheduleTime={setScheduleTime}
        isTechnicalRole={isTechnicalRole}
        setIsTechnicalRole={setIsTechnicalRole}
        customQFile={customQFile}
        setCustomQFile={setCustomQFile}
        customQUploading={customQUploading}
        schedulingLoading={schedulingLoading}
        onSchedule={handleSchedule}
      />

      {/* Candidate Details Modal */}
      <CandidateDetailsModal
        open={viewDetailsModalOpen}
        onOpenChange={setViewDetailsModalOpen}
        selectedCandidate={selectedCandidate}
        assessmentDetails={assessmentDetails}
        decisionLoading={decisionLoading}
        onDownloadResume={handleDownloadResume}
        onFinalDecision={handleFinalDecision}
      />

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

export default InterviewerDashboardPage;
