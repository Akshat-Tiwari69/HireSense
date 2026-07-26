import { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  Activity,
  Calendar,
  CheckCircle,
  Filter,
  Loader,
  Search,
  TrendingUp,
  UserRoundSearch,
  Users,
  X,
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { api } from '../services/api';
import ProctorMonitor from '../components/ProctorMonitor';
import ScheduleModal from '../components/interviewer/ScheduleModal';
import CandidateDetailsModal from '../components/interviewer/CandidateDetailsModal';
import { useAuth } from '../contexts/AuthContext';
import WorkspaceShell from '../components/workspace/WorkspaceShell';
import MetricCard from '../components/workspace/MetricCard';
import StatusBadge from '../components/workspace/StatusBadge';
import { resolveCandidateStatus } from '../lib/assessment';

const getScoreBadgeColor = (score) => {
  if (score >= 85) return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  if (score >= 70) return 'border-amber-200 bg-amber-50 text-amber-700';
  return 'border-red-200 bg-red-50 text-red-700';
};

const ScoreBadge = ({ score }) => (
  <Badge
    variant="outline"
    className={`${getScoreBadgeColor(score)} px-2.5 py-1 font-semibold tabular-nums`}
    aria-label={`${score} percent AI match`}
  >
    {score}%
  </Badge>
);

const CandidateActions = ({
  candidate,
  rejecting,
  onView,
  onMonitor,
  onSchedule,
  onReject,
}) => (
  <div className="flex flex-wrap items-center justify-end gap-2">
    <Button
      size="sm"
      variant="outline"
      onClick={() => onView(candidate)}
      aria-label={`View ${candidate.name}`}
    >
      View
    </Button>

    {candidate.status === 'In Progress' ? (
      <Button
        size="sm"
        variant="secondary"
        onClick={() => onMonitor(candidate.assessmentId)}
        disabled={!candidate.assessmentId}
        title={candidate.assessmentId ? undefined : 'Monitoring is not available yet'}
        aria-label={`Monitor ${candidate.name}'s assessment`}
      >
        Monitor
      </Button>
    ) : null}

    {candidate.status === 'Applied' ? (
      <>
        <Button
          size="sm"
          onClick={() => onSchedule(candidate)}
          aria-label={`Schedule ${candidate.name}'s assessment`}
        >
          Schedule
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={() => onReject(candidate.id)}
          disabled={rejecting}
          className="min-w-[68px]"
          aria-label={`Reject ${candidate.name}`}
        >
          {rejecting ? <Loader className="animate-spin" aria-hidden="true" /> : 'Reject'}
        </Button>
      </>
    ) : null}
  </div>
);

const InterviewerDashboardPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { signOut, user } = useAuth();

  const [realtimeCandidates, setRealtimeCandidates] = useState([]);

  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [scoreFilter, setScoreFilter] = useState('all');
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduleTime, setScheduleTime] = useState('');
  const [viewDetailsModalOpen, setViewDetailsModalOpen] = useState(false);
  const [assessmentDetails, setAssessmentDetails] = useState(null);
  const [assessmentLoading, setAssessmentLoading] = useState(false);
  const [decisionLoading, setDecisionLoading] = useState(false);

  const [monitoringAssessmentId, setMonitoringAssessmentId] = useState(null);

  const [isLoading, setIsLoading] = useState(true);
  const [rejectingCandidateId, setRejectingCandidateId] = useState(null);
  const [schedulingLoading, setSchedulingLoading] = useState(false);

  const stats = useMemo(() => realtimeCandidates.reduce((totals, candidate) => {
    if (candidate.aiMatchScore >= 85) totals.highMatch += 1;
    if (candidate.status === 'Scheduled') totals.scheduled += 1;
    if (candidate.status === 'Completed') totals.completed += 1;
    if (candidate.status === 'Hired') totals.hired += 1;
    return totals;
  }, {
    total: realtimeCandidates.length,
    highMatch: 0,
    scheduled: 0,
    completed: 0,
    hired: 0,
  }), [realtimeCandidates]);

  const fetchCandidates = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await api.get('/api/interviewer/candidates');
      const list = res?.data?.data || [];

      const mapped = list.map((c) => {
        const normalizedStatus = resolveCandidateStatus(
          c.status,
          c.assessment_status,
        );

        return {
          id: c.id,
          name: c.name,
          email: c.email,
          status: normalizedStatus,
          aiRecommendation: c.shortlist_status || null,
          aiMatchScore: Math.round(Number(c.match_score) || 0),
          assessmentDecision: c.assessment_decision,
          assessmentScheduled: c.assessment_date || null,
          assessmentId: c.assessment_id || null,
          pros: Array.isArray(c.pros) ? c.pros : (c.pros ? c.pros.split('\n') : []),
          cons: Array.isArray(c.cons) ? c.cons : (c.cons ? c.cons.split('\n') : []),
        };
      });

      setRealtimeCandidates(mapped);
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to load candidates';
      toast({ variant: 'destructive', title: 'Load failed', description: message });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchCandidates();
  }, [fetchCandidates]);

  const handleDownloadResume = useCallback(async (candidateId) => {
    try {
      const response = await api.get(`/api/interviewer/candidates/${candidateId}/resume`, {
        responseType: 'blob'
      });

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

  const filteredCandidates = useMemo(() => {
    const normalizedSearch = searchTerm.trim().toLowerCase();

    return realtimeCandidates.filter((candidate) => {
      const matchesSearch = !normalizedSearch
        || candidate.name?.toLowerCase().includes(normalizedSearch)
        || candidate.email?.toLowerCase().includes(normalizedSearch);
      const matchesStatus = statusFilter === 'all'
        || candidate.status.toLowerCase() === statusFilter.toLowerCase();
      const matchesScore = scoreFilter === 'all'
        || (scoreFilter === 'high' && candidate.aiMatchScore >= 85)
        || (scoreFilter === 'medium' && candidate.aiMatchScore >= 70 && candidate.aiMatchScore < 85)
        || (scoreFilter === 'low' && candidate.aiMatchScore < 70);

      return matchesSearch && matchesStatus && matchesScore;
    });
  }, [realtimeCandidates, scoreFilter, searchTerm, statusFilter]);

  const hasActiveFilters = Boolean(searchTerm.trim()) || statusFilter !== 'all' || scoreFilter !== 'all';

  const clearFilters = useCallback(() => {
    setSearchTerm('');
    setStatusFilter('all');
    setScoreFilter('all');
  }, []);

  const handleOpenSchedule = useCallback((candidate) => {
    setSelectedCandidate(candidate);
    setScheduleModalOpen(true);
  }, []);

  const handleLogout = useCallback(() => {
    signOut();
    navigate('/login');
  }, [navigate, signOut]);

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
  }, [setRealtimeCandidates, toast]);

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
      await api.post(`/api/interviewer/candidates/${selectedCandidate.id}/schedule`, {
        scheduled_time: scheduledDateTime,
        is_technical_role: false,
      });
      setRealtimeCandidates(prev => prev.map(c =>
        c.id === selectedCandidate.id
          ? { ...c, status: 'Scheduled', assessmentScheduled: scheduledDateTime, isTechnicalRole: false }
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
      setSelectedCandidate(null);
    }
  }, [scheduleDate, scheduleTime, selectedCandidate, setRealtimeCandidates, toast]);

  const handleOpenDetails = useCallback(async (candidate) => {
    const shouldLoadAssessment = ['Completed', 'Hired', 'Rejected'].includes(candidate.status);
    setSelectedCandidate(candidate);
    setAssessmentDetails(null);
    setAssessmentLoading(shouldLoadAssessment);
    setViewDetailsModalOpen(true);

    if (shouldLoadAssessment) {
      try {
        const res = await api.get(`/api/interviewer/assessments/${candidate.id}`);
        setAssessmentDetails(res.data.data);
      } catch (err) {
        const message = err?.response?.data?.message || 'Assessment results are unavailable';
        toast({ variant: 'destructive', title: 'Unable to load assessment', description: message });
      } finally {
        setAssessmentLoading(false);
      }
    }
  }, [toast]);

  const handleFinalDecision = useCallback(async (decision, rationale, nextSteps) => {
    if (!assessmentDetails?.id) return;

    setDecisionLoading(true);
    try {
      await api.post(`/api/interviewer/assessments/${assessmentDetails.id}/final-decision`, {
        decision,
        rationale,
        next_steps: nextSteps,
      });

      toast({
        title: 'Success',
        description: `Candidate ${decision === 'hire' ? 'hired' : 'rejected'} successfully.`
      });
      setViewDetailsModalOpen(false);
      fetchCandidates();
    } catch (err) {
      const message = err?.response?.data?.message || 'Failed to record decision';
      toast({ variant: 'destructive', title: 'Error', description: message });
    } finally {
      setDecisionLoading(false);
    }
  }, [assessmentDetails, toast, fetchCandidates]);

  return (
    <WorkspaceShell
      role={user?.role || 'interviewer'}
      title="Candidate pipeline"
      description="Review assigned applicants, schedule assessments, inspect evidence, and record the final hiring outcome."
      user={user}
      onRefresh={fetchCandidates}
      refreshing={isLoading}
      onSignOut={handleLogout}
    >
      <div className="mb-6 grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Candidates" value={stats.total} icon={Users} />
        <MetricCard label="High match" value={stats.highMatch} icon={TrendingUp} tone="success" />
        <MetricCard label="Scheduled" value={stats.scheduled} icon={Calendar} />
        <MetricCard label="Completed" value={stats.completed} icon={Activity} tone="neutral" />
        <MetricCard label="Hired" value={stats.hired} icon={CheckCircle} tone="success" />
      </div>

      <section aria-labelledby="candidate-queue-heading">
        <Card className="overflow-hidden">
          <CardHeader className="gap-5 border-b p-5 sm:p-6">
            <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-start">
              <div>
                <CardTitle>
                  <h2 id="candidate-queue-heading" className="text-lg">Candidate queue</h2>
                </CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">
                  Search and act on candidates assigned to you.
                </p>
              </div>
              <p className="text-sm text-muted-foreground" aria-live="polite">
                <span className="font-semibold tabular-nums text-foreground">{filteredCandidates.length}</span>
                {' '}of {realtimeCandidates.length} shown
              </p>
            </div>

            <div className="grid gap-3 lg:grid-cols-[minmax(260px,1fr)_190px_180px_auto]">
              <div className="relative">
                <label htmlFor="candidate-search" className="sr-only">Search candidates</label>
                <Search
                  className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
                  aria-hidden="true"
                />
                <Input
                  id="candidate-search"
                  type="search"
                  placeholder="Search name or email"
                  value={searchTerm}
                  onChange={(event) => setSearchTerm(event.target.value)}
                  className="pl-9"
                />
              </div>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger aria-label="Filter by candidate status">
                  <Filter className="mr-2 h-4 w-4 text-muted-foreground" aria-hidden="true" />
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All statuses</SelectItem>
                  <SelectItem value="Applied">Applied</SelectItem>
                  <SelectItem value="Scheduled">Scheduled</SelectItem>
                  <SelectItem value="In Progress">In progress</SelectItem>
                  <SelectItem value="Completed">Completed</SelectItem>
                  <SelectItem value="Under Review">Under review</SelectItem>
                  <SelectItem value="Rejected">Rejected</SelectItem>
                  <SelectItem value="Hired">Hired</SelectItem>
                </SelectContent>
              </Select>

              <Select value={scoreFilter} onValueChange={setScoreFilter}>
                <SelectTrigger aria-label="Filter by AI match score">
                  <SelectValue placeholder="All match scores" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All match scores</SelectItem>
                  <SelectItem value="high">High · 85%+</SelectItem>
                  <SelectItem value="medium">Medium · 70–84%</SelectItem>
                  <SelectItem value="low">Low · below 70%</SelectItem>
                </SelectContent>
              </Select>

              {hasActiveFilters ? (
                <Button variant="ghost" onClick={clearFilters} className="justify-start lg:px-3">
                  <X aria-hidden="true" />
                  Clear
                </Button>
              ) : <span className="hidden lg:block" aria-hidden="true" />}
            </div>
          </CardHeader>

          <CardContent className="p-0">
            {isLoading ? (
              <div className="flex min-h-52 items-center justify-center gap-3 text-sm text-muted-foreground" role="status">
                <Loader className="h-5 w-5 animate-spin text-primary" aria-hidden="true" />
                Loading candidates
              </div>
            ) : filteredCandidates.length === 0 ? (
              <div className="flex min-h-64 flex-col items-center justify-center px-6 py-12 text-center">
                <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                  <UserRoundSearch className="h-5 w-5" aria-hidden="true" />
                </span>
                <p className="mt-4 font-semibold text-foreground">No candidates found</p>
                <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                  {hasActiveFilters
                    ? 'Try a different search or clear the active filters.'
                    : 'Candidates assigned to you will appear here.'}
                </p>
                {hasActiveFilters ? (
                  <Button variant="outline" size="sm" onClick={clearFilters} className="mt-4">
                    Clear filters
                  </Button>
                ) : null}
              </div>
            ) : (
              <>
                <ul className="divide-y md:hidden" aria-label="Candidates">
                  {filteredCandidates.map((candidate) => (
                    <li key={candidate.id} className="p-5">
                      <div className="flex items-start justify-between gap-4">
                        <div className="min-w-0">
                          <p className="truncate font-semibold text-foreground">{candidate.name}</p>
                          <p className="mt-1 break-all text-sm text-muted-foreground">{candidate.email}</p>
                        </div>
                        <ScoreBadge score={candidate.aiMatchScore} />
                      </div>
                      <div className="mt-4 flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
                        <div><StatusBadge status={candidate.status} /></div>
                        <CandidateActions
                          candidate={candidate}
                          rejecting={rejectingCandidateId === candidate.id}
                          onView={handleOpenDetails}
                          onMonitor={setMonitoringAssessmentId}
                          onSchedule={handleOpenSchedule}
                          onReject={handleReject}
                        />
                      </div>
                    </li>
                  ))}
                </ul>

                <div className="hidden md:block">
                  <Table className="min-w-[760px]">
                    <TableHeader>
                      <TableRow className="bg-muted/55 hover:bg-muted/55">
                        <TableHead>Candidate</TableHead>
                        <TableHead>AI match</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredCandidates.map((candidate) => (
                        <TableRow key={candidate.id}>
                          <TableCell className="min-w-[220px]">
                            <p className="font-semibold text-foreground">{candidate.name}</p>
                            <p className="mt-0.5 text-sm text-muted-foreground">{candidate.email}</p>
                          </TableCell>
                          <TableCell><ScoreBadge score={candidate.aiMatchScore} /></TableCell>
                          <TableCell><StatusBadge status={candidate.status} /></TableCell>
                          <TableCell className="min-w-[250px] text-right">
                            <CandidateActions
                              candidate={candidate}
                              rejecting={rejectingCandidateId === candidate.id}
                              onView={handleOpenDetails}
                              onMonitor={setMonitoringAssessmentId}
                              onSchedule={handleOpenSchedule}
                              onReject={handleReject}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </section>
      <ScheduleModal
        open={scheduleModalOpen}
        onOpenChange={setScheduleModalOpen}
        selectedCandidate={selectedCandidate}
        scheduleDate={scheduleDate}
        setScheduleDate={setScheduleDate}
        scheduleTime={scheduleTime}
        setScheduleTime={setScheduleTime}
        schedulingLoading={schedulingLoading}
        onSchedule={handleSchedule}
      />

      {/* Candidate Details Modal */}
      <CandidateDetailsModal
        open={viewDetailsModalOpen}
        onOpenChange={setViewDetailsModalOpen}
        selectedCandidate={selectedCandidate}
        assessmentDetails={assessmentDetails}
        assessmentLoading={assessmentLoading}
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
    </WorkspaceShell>
  );
};

export default InterviewerDashboardPage;
