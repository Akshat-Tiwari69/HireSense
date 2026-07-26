import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  Calendar,
  CheckCircle,
  Eye,
  Loader2,
  Search,
  Shield,
  UserPlus,
  Video,
  Zap,
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import LoadingScreen from '../components/common/LoadingScreen';
import ProctorMonitor from '../components/ProctorMonitor';
import MetricCard from '../components/workspace/MetricCard';
import StatusBadge from '../components/workspace/StatusBadge';
import WorkspaceShell from '../components/workspace/WorkspaceShell';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import { api } from '../services/api';

const ViolationScreenshot = ({ screenshotUrl }) => {
  const [requested, setRequested] = useState(false);
  const [objectUrl, setObjectUrl] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (!requested) return undefined;

    let active = true;
    let createdUrl = null;
    setFailed(false);
    setObjectUrl(null);

    api.get(screenshotUrl, { responseType: 'blob' })
      .then((response) => {
        if (!active) return;
        createdUrl = URL.createObjectURL(response.data);
        setObjectUrl(createdUrl);
      })
      .catch(() => {
        if (active) setFailed(true);
      });

    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [requested, screenshotUrl]);

  if (!requested) {
    return (
      <Button type="button" size="sm" variant="outline" onClick={() => setRequested(true)}>
        <Eye aria-hidden="true" />
        Load evidence
      </Button>
    );
  }

  if (failed) {
    return (
      <div className="flex h-24 w-36 flex-col items-center justify-center rounded-lg border border-slate-200 bg-slate-50 px-3 text-center">
        <p className="text-xs text-slate-500">Evidence unavailable</p>
        <button
          type="button"
          className="mt-1 text-xs font-semibold text-primary hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          onClick={() => setRequested(false)}
        >
          Try again
        </button>
      </div>
    );
  }

  if (!objectUrl) {
    return (
      <div className="flex h-24 w-36 items-center justify-center gap-2 rounded-lg border border-slate-200 bg-slate-50 text-xs text-slate-500" aria-live="polite">
        <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
        Loading
      </div>
    );
  }

  return (
    <button
      type="button"
      className="h-24 w-36 overflow-hidden rounded-lg border border-slate-300 bg-slate-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
      onClick={() => window.open(objectUrl, '_blank', 'noopener,noreferrer')}
      aria-label="Open violation evidence in a new tab"
    >
      <img src={objectUrl} alt="Captured integrity event" className="h-full w-full object-cover" />
    </button>
  );
};

const EmptyState = ({ icon: Icon, title, description }) => (
  <div className="flex flex-col items-center px-6 py-14 text-center">
    <div className="flex h-11 w-11 items-center justify-center rounded-lg border border-slate-200 bg-slate-50">
      <Icon className="h-5 w-5 text-slate-500" aria-hidden="true" />
    </div>
    <p className="mt-4 text-sm font-semibold text-slate-900">{title}</p>
    <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>
  </div>
);

const ScoreBadge = ({ score }) => {
  const numericScore = Number(score) || 0;
  const tone = numericScore >= 70
    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
    : numericScore >= 50
      ? 'border-amber-200 bg-amber-50 text-amber-700'
      : 'border-red-200 bg-red-50 text-red-700';

  return <Badge variant="outline" className={tone}>{numericScore}%</Badge>;
};

const formatDateTime = (value) => {
  if (!value) return 'Not available';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Not available' : date.toLocaleString();
};

const formatEventType = (value) => String(value || 'integrity event').replaceAll('_', ' ');

const severityClassName = (severity) => {
  const normalized = String(severity || '').toLowerCase();
  if (normalized === 'high' || normalized === 'critical') return 'border-red-200 bg-red-50 text-red-700';
  if (normalized === 'medium') return 'border-amber-200 bg-amber-50 text-amber-700';
  return 'border-blue-200 bg-blue-50 text-blue-700';
};

const ProctorDashboardPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { signOut, user } = useAuth();

  const [stats, setStats] = useState({
    scheduled_count: 0,
    active_count: 0,
    completed_today: 0,
    violations_today: 0,
  });
  const [scheduledAssessments, setScheduledAssessments] = useState([]);
  const [activeAssessments, setActiveAssessments] = useState([]);
  const [completedAssessments, setCompletedAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [currentProctorId, setCurrentProctorId] = useState(() => Number(user?.id) || null);
  const [claimingAssessmentIds, setClaimingAssessmentIds] = useState(() => new Set());
  const [violationsModalOpen, setViolationsModalOpen] = useState(false);
  const [selectedViolations, setSelectedViolations] = useState([]);
  const [loadingViolations, setLoadingViolations] = useState(false);
  const [monitoringAssessmentId, setMonitoringAssessmentId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchAllDataRef = useRef(null);
  const fetchingRef = useRef(false);
  const normalizedSearch = searchQuery.trim().toLowerCase();

  const matchesSearch = useCallback((assessment) => (
    !normalizedSearch
    || assessment.candidate_name?.toLowerCase().includes(normalizedSearch)
    || assessment.candidate_email?.toLowerCase().includes(normalizedSearch)
  ), [normalizedSearch]);

  const filteredScheduled = useMemo(
    () => scheduledAssessments.filter(matchesSearch),
    [matchesSearch, scheduledAssessments],
  );
  const filteredActive = useMemo(
    () => activeAssessments.filter(matchesSearch),
    [activeAssessments, matchesSearch],
  );
  const filteredCompleted = useMemo(
    () => completedAssessments.filter(matchesSearch),
    [completedAssessments, matchesSearch],
  );

  useEffect(() => {
    fetchAllDataRef.current?.();
  }, []);

  useEffect(() => {
    if (!autoRefresh) return undefined;

    const refreshWhenVisible = () => {
      if (document.visibilityState === 'visible') fetchAllDataRef.current?.(true);
    };
    const interval = setInterval(refreshWhenVisible, 30000);
    document.addEventListener('visibilitychange', refreshWhenVisible);

    return () => {
      clearInterval(interval);
      document.removeEventListener('visibilitychange', refreshWhenVisible);
    };
  }, [autoRefresh]);

  const fetchAllData = useCallback(async (silent = false) => {
    if (fetchingRef.current) return;
    fetchingRef.current = true;
    if (!silent) setLoading(true);

    try {
      const [statsRes, scheduledRes, activeRes, completedRes] = await Promise.all([
        api.get('/api/proctor/dashboard-stats'),
        api.get('/api/proctor/scheduled-assessments'),
        api.get('/api/proctor/active-assessments'),
        api.get('/api/proctor/completed-assessments'),
      ]);

      const dashboard = statsRes.data || {};
      setStats({
        scheduled_count: dashboard.scheduled_today || 0,
        active_count: dashboard.active_assessments || 0,
        completed_today: dashboard.completed_today || 0,
        violations_today: dashboard.violations_today || 0,
      });
      setScheduledAssessments(scheduledRes.data || []);
      setActiveAssessments((activeRes.data || []).map((assessment) => ({
        ...assessment,
        id: assessment.assessment_id,
      })));
      setCompletedAssessments(completedRes.data || []);
    } catch (error) {
      const message = error?.response?.data?.message || 'Failed to load proctor data';
      if (error?.response?.status === 403) {
        toast({ variant: 'destructive', title: 'Access denied', description: 'Proctor role required' });
        navigate('/dashboard');
      } else if (!silent) {
        toast({ variant: 'destructive', title: 'Unable to load dashboard', description: message });
      }
    } finally {
      fetchingRef.current = false;
      if (!silent) setLoading(false);
    }
  }, [navigate, toast]);
  fetchAllDataRef.current = fetchAllData;

  const isAssignedToCurrentProctor = useCallback((assessment) => (
    currentProctorId !== null && Number(assessment?.proctor_id) === currentProctorId
  ), [currentProctorId]);

  const handleClaimAssessment = useCallback(async (scheduledAssessmentId) => {
    if (!scheduledAssessmentId || claimingAssessmentIds.has(scheduledAssessmentId)) return;

    setClaimingAssessmentIds((previous) => {
      const next = new Set(previous);
      next.add(scheduledAssessmentId);
      return next;
    });

    try {
      const response = await api.post('/api/proctor/assign-assessment', {
        scheduled_assessment_id: scheduledAssessmentId,
      });
      const assignedProctorId = Number(response.data?.data?.proctor_id);
      if (Number.isInteger(assignedProctorId) && assignedProctorId > 0) setCurrentProctorId(assignedProctorId);
      toast({
        title: 'Assessment claimed',
        description: 'You can now monitor this candidate and review their integrity events.',
      });
      await fetchAllData(true);
    } catch (error) {
      const message = error?.response?.data?.message || 'Failed to claim assessment';
      toast({ variant: 'destructive', title: 'Claim failed', description: message });
      await fetchAllData(true);
    } finally {
      setClaimingAssessmentIds((previous) => {
        const next = new Set(previous);
        next.delete(scheduledAssessmentId);
        return next;
      });
    }
  }, [claimingAssessmentIds, fetchAllData, toast]);

  const getTimeUntil = (value) => {
    if (!value) return 'Not scheduled';
    const scheduled = new Date(value);
    if (Number.isNaN(scheduled.getTime())) return 'Not scheduled';

    const diffMinutes = Math.floor((scheduled.getTime() - Date.now()) / 60000);
    if (diffMinutes < 0) return 'Overdue';
    if (diffMinutes < 60) return `${diffMinutes} min`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)} hr`;
    return `${Math.floor(diffMinutes / 1440)} days`;
  };

  const handleViewViolations = async (assessment) => {
    if (!isAssignedToCurrentProctor(assessment)) {
      toast({
        variant: 'destructive',
        title: 'Assignment required',
        description: 'Claim this assessment before reviewing its integrity event log.',
      });
      return;
    }

    const assessmentId = assessment.assessment_id ?? assessment.id;
    setLoadingViolations(true);
    setViolationsModalOpen(true);
    setSelectedViolations([]);

    try {
      const response = await api.get(`/api/proctor/assessments/${assessmentId}/violations`);
      setSelectedViolations(response.data.data || []);
    } catch {
      toast({ variant: 'destructive', title: 'Unable to load events', description: 'Please try again.' });
    } finally {
      setLoadingViolations(false);
    }
  };

  const handleStartMonitoring = (assessment) => {
    if (!isAssignedToCurrentProctor(assessment)) {
      toast({
        variant: 'destructive',
        title: 'Assignment required',
        description: 'Claim this assessment before opening the live monitor.',
      });
      return;
    }
    setMonitoringAssessmentId(assessment.assessment_id);
  };

  const handleLogout = () => {
    signOut();
    navigate('/login');
  };

  if (loading) return <LoadingScreen message="Loading proctor workspace" />;

  return (
    <WorkspaceShell
      role="proctor"
      title="Assessment integrity"
      description="Claim sessions, observe active candidates, and review integrity events in context."
      user={user}
      onRefresh={fetchAllData}
      refreshing={loading}
      onSignOut={handleLogout}
    >
      <div className="mb-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Proctoring summary">
        <MetricCard label="Scheduled" value={stats.scheduled_count || 0} hint="Upcoming today" icon={Calendar} />
        <MetricCard label="Active now" value={stats.active_count || 0} hint="Live sessions" icon={Zap} tone="success" />
        <MetricCard label="Completed today" value={stats.completed_today || 0} hint="Finished sessions" icon={CheckCircle} tone="neutral" />
        <MetricCard label="Events today" value={stats.violations_today || 0} hint="Awaiting human context" icon={AlertTriangle} tone="warning" />
      </div>

      <div className="mb-6 flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-900">Live dashboard updates</p>
          <p className="mt-0.5 text-xs text-slate-500">Refreshes every 30 seconds while this tab is visible.</p>
        </div>
        <Button
          type="button"
          size="sm"
          variant={autoRefresh ? 'secondary' : 'outline'}
          aria-pressed={autoRefresh}
          onClick={() => setAutoRefresh((enabled) => !enabled)}
        >
          {autoRefresh ? 'Auto-refresh on' : 'Auto-refresh off'}
        </Button>
      </div>

      <Tabs defaultValue="active" className="space-y-5">
        <TabsList aria-label="Assessment status">
          <TabsTrigger value="active">
            <Activity aria-hidden="true" />
            Active
            <Badge variant="secondary" className="ml-1 border-0 px-1.5 py-0">{stats.active_count || 0}</Badge>
          </TabsTrigger>
          <TabsTrigger value="scheduled">
            <Calendar aria-hidden="true" />
            Scheduled
            <Badge variant="secondary" className="ml-1 border-0 px-1.5 py-0">{scheduledAssessments.length}</Badge>
          </TabsTrigger>
          <TabsTrigger value="completed">
            <CheckCircle aria-hidden="true" />
            Completed
          </TabsTrigger>
        </TabsList>

        <div className="relative max-w-lg">
          <label htmlFor="candidate-search" className="sr-only">Search candidates</label>
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" aria-hidden="true" />
          <Input
            id="candidate-search"
            type="search"
            placeholder="Search by candidate name or email"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            className="pl-9"
          />
        </div>

        <TabsContent value="active">
          <Card>
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="flex items-center gap-2 text-base text-slate-900">
                <Activity className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                Active assessments
              </CardTitle>
              <CardDescription>Live sessions available to your proctor team.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {filteredActive.length === 0 ? (
                <EmptyState
                  icon={Video}
                  title={normalizedSearch ? 'No matching active assessments' : 'No active assessments'}
                  description={normalizedSearch ? 'Try another candidate name or email.' : 'Live sessions will appear here when candidates begin.'}
                />
              ) : (
                <div className="divide-y divide-slate-100">
                  {filteredActive.map((assessment) => {
                    const isAssigned = isAssignedToCurrentProctor(assessment);
                    const isClaiming = claimingAssessmentIds.has(assessment.scheduled_assessment_id);

                    return (
                      <article key={assessment.id} className="p-5 sm:p-6">
                        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                          <div className="flex min-w-0 items-start gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-emerald-200 bg-emerald-50">
                              <Video className="h-4 w-4 text-emerald-700" aria-hidden="true" />
                            </div>
                            <div className="min-w-0">
                              <div className="flex flex-wrap items-center gap-2">
                                <h3 className="truncate text-sm font-semibold text-slate-900">{assessment.candidate_name}</h3>
                                <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">Live</Badge>
                                {(assessment.proctoring_violations || 0) > 0 ? (
                                  <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700">
                                    <AlertTriangle aria-hidden="true" />
                                    {assessment.proctoring_violations} event{assessment.proctoring_violations === 1 ? '' : 's'}
                                  </Badge>
                                ) : null}
                              </div>
                              <p className="mt-1 truncate text-sm text-slate-600">{assessment.candidate_email}</p>
                              <p className="mt-1 text-xs text-slate-500">Started {formatDateTime(assessment.started_at)}</p>
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center gap-2 lg:justify-end">
                            {!isAssigned && !assessment.proctor_id ? (
                              <Button
                                type="button"
                                size="sm"
                                variant="outline"
                                disabled={isClaiming}
                                onClick={() => handleClaimAssessment(assessment.scheduled_assessment_id)}
                              >
                                {isClaiming ? <Loader2 className="animate-spin motion-reduce:animate-none" aria-hidden="true" /> : <UserPlus aria-hidden="true" />}
                                {isClaiming ? 'Claiming…' : 'Claim'}
                              </Button>
                            ) : null}
                            {!isAssigned && assessment.proctor_id ? (
                              <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-600">Claimed by another proctor</Badge>
                            ) : null}
                            <Button
                              type="button"
                              size="sm"
                              disabled={!isAssigned}
                              title={isAssigned ? 'Open live monitor' : 'Claim this assessment first'}
                              onClick={() => handleStartMonitoring(assessment)}
                            >
                              <Video aria-hidden="true" />
                              Monitor live
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              disabled={!isAssigned}
                              title={isAssigned ? 'Review integrity events' : 'Claim this assessment first'}
                              onClick={() => handleViewViolations(assessment)}
                            >
                              <Eye aria-hidden="true" />
                              Review events
                            </Button>
                          </div>
                        </div>
                      </article>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="scheduled">
          <Card>
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Upcoming assessments</CardTitle>
              <CardDescription>
                {filteredScheduled.length} assessment{filteredScheduled.length === 1 ? '' : 's'} in this view.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {filteredScheduled.length === 0 ? (
                <EmptyState
                  icon={Calendar}
                  title={normalizedSearch ? 'No matching scheduled assessments' : 'No scheduled assessments'}
                  description={normalizedSearch ? 'Try another candidate name or email.' : 'Upcoming sessions will appear here once they are scheduled.'}
                />
              ) : (
                <div className="overflow-x-auto">
                  <Table className="min-w-[880px]">
                    <TableHeader>
                      <TableRow>
                        <TableHead>Candidate</TableHead>
                        <TableHead>Scheduled time</TableHead>
                        <TableHead>Starts in</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Assignment</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredScheduled.map((assessment) => {
                        const timeUntil = getTimeUntil(assessment.scheduled_time);
                        const isClaiming = claimingAssessmentIds.has(assessment.id);

                        return (
                          <TableRow key={assessment.id}>
                            <TableCell>
                              <p className="font-medium text-slate-900">{assessment.candidate_name}</p>
                              <p className="mt-0.5 text-xs text-slate-500">{assessment.candidate_email}</p>
                            </TableCell>
                            <TableCell className="text-sm text-slate-600">{formatDateTime(assessment.scheduled_time)}</TableCell>
                            <TableCell>
                              <Badge
                                variant="outline"
                                className={timeUntil === 'Overdue'
                                  ? 'border-red-200 bg-red-50 text-red-700'
                                  : 'border-blue-200 bg-blue-50 text-blue-700'}
                              >
                                {timeUntil}
                              </Badge>
                            </TableCell>
                            <TableCell><StatusBadge status={assessment.status} /></TableCell>
                            <TableCell className="text-right">
                              {isAssignedToCurrentProctor(assessment) ? (
                                <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">Assigned to you</Badge>
                              ) : assessment.proctor_id ? (
                                <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-600">Claimed</Badge>
                              ) : (
                                <Button
                                  type="button"
                                  size="sm"
                                  disabled={isClaiming}
                                  onClick={() => handleClaimAssessment(assessment.id)}
                                >
                                  {isClaiming ? <Loader2 className="animate-spin motion-reduce:animate-none" aria-hidden="true" /> : <UserPlus aria-hidden="true" />}
                                  {isClaiming ? 'Claiming…' : 'Claim assessment'}
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="completed">
          <Card>
            <CardHeader className="border-b border-slate-100">
              <CardTitle className="text-base text-slate-900">Completed assessments</CardTitle>
              <CardDescription>
                {filteredCompleted.length} assessment{filteredCompleted.length === 1 ? '' : 's'} in this view.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              {filteredCompleted.length === 0 ? (
                <EmptyState
                  icon={CheckCircle}
                  title={normalizedSearch ? 'No matching completed assessments' : 'No completed assessments'}
                  description={normalizedSearch ? 'Try another candidate name or email.' : 'Finished sessions and their integrity summaries will appear here.'}
                />
              ) : (
                <div className="overflow-x-auto">
                  <Table className="min-w-[820px]">
                    <TableHeader>
                      <TableRow>
                        <TableHead>Candidate</TableHead>
                        <TableHead>Completed</TableHead>
                        <TableHead>MCQ</TableHead>
                        <TableHead>Coding</TableHead>
                        <TableHead>Overall</TableHead>
                        <TableHead>Integrity events</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredCompleted.map((assessment) => (
                        <TableRow key={assessment.id ?? assessment.assessment_id}>
                          <TableCell>
                            <p className="font-medium text-slate-900">{assessment.candidate_name}</p>
                            <p className="mt-0.5 text-xs text-slate-500">{assessment.candidate_email}</p>
                          </TableCell>
                          <TableCell className="text-sm text-slate-600">{formatDateTime(assessment.completed_at)}</TableCell>
                          <TableCell className="text-sm text-slate-600">{Number(assessment.mcq_score) || 0}%</TableCell>
                          <TableCell className="text-sm text-slate-600">{Number(assessment.coding_score) || 0}%</TableCell>
                          <TableCell><ScoreBadge score={assessment.overall_score} /></TableCell>
                          <TableCell>
                            {(assessment.proctoring_violations || 0) > 0 ? (
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700">
                                  <AlertTriangle aria-hidden="true" />
                                  {assessment.proctoring_violations}
                                </Badge>
                                <Button
                                  type="button"
                                  size="icon"
                                  variant="ghost"
                                  className="h-8 w-8"
                                  disabled={!isAssignedToCurrentProctor(assessment)}
                                  title={isAssignedToCurrentProctor(assessment) ? 'Review integrity events' : 'Only the assigned proctor can review events'}
                                  aria-label="Review integrity events"
                                  onClick={() => handleViewViolations(assessment)}
                                >
                                  <Eye aria-hidden="true" />
                                </Button>
                              </div>
                            ) : (
                              <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700">
                                <Shield aria-hidden="true" />
                                None recorded
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

      <Dialog open={violationsModalOpen} onOpenChange={setViolationsModalOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Integrity event log</DialogTitle>
            <DialogDescription>
              Automated signals require human review and should not be treated as standalone evidence.
            </DialogDescription>
          </DialogHeader>

          <div className="pt-2">
            {loadingViolations ? (
              <div className="flex items-center justify-center gap-2 py-14 text-sm text-slate-500" aria-live="polite">
                <Loader2 className="h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                Loading integrity events
              </div>
            ) : selectedViolations.length === 0 ? (
              <EmptyState icon={Shield} title="No events recorded" description="No integrity signals were recorded for this assessment." />
            ) : (
              <div className="divide-y divide-slate-100 rounded-lg border border-slate-200">
                {selectedViolations.map((violation) => {
                  const shouldShowScreenshot = ['no_face', 'multiple_faces', 'unknown_person'].includes(violation.violation_type);
                  const severity = String(violation.severity || 'review').toLowerCase();

                  return (
                    <article key={violation.id} className="flex flex-col gap-4 p-4 sm:flex-row sm:items-start">
                      {shouldShowScreenshot ? (
                        <div className="shrink-0">
                          {violation.screenshot_url ? (
                            <ViolationScreenshot screenshotUrl={violation.screenshot_url} />
                          ) : (
                            <div className="flex h-24 w-36 items-center justify-center rounded-lg border border-slate-200 bg-slate-50">
                              <Eye className="h-5 w-5 text-slate-400" aria-hidden="true" />
                              <span className="sr-only">No evidence image available</span>
                            </div>
                          )}
                        </div>
                      ) : null}
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                          <h3 className="text-sm font-semibold capitalize text-slate-900">{formatEventType(violation.violation_type)}</h3>
                          <time className="shrink-0 text-xs text-slate-500" dateTime={violation.timestamp}>
                            {formatDateTime(violation.timestamp)}
                          </time>
                        </div>
                        <p className="mt-2 text-sm leading-6 text-slate-600">
                          {violation.description || 'An automated integrity signal was recorded.'}
                        </p>
                        <Badge variant="outline" className={`mt-3 capitalize ${severityClassName(severity)}`}>
                          {severity} severity
                        </Badge>
                      </div>
                    </article>
                  );
                })}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {monitoringAssessmentId ? (
        <ProctorMonitor
          assessmentId={monitoringAssessmentId}
          onClose={() => setMonitoringAssessmentId(null)}
        />
      ) : null}
    </WorkspaceShell>
  );
};

export default ProctorDashboardPage;
