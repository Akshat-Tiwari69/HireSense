import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Activity, Clock, CheckCircle, AlertTriangle, Eye, MessageSquare, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';

const ProctorDashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('live');
  const [stats, setStats] = useState({
    active_assessments: 0,
    scheduled_today: 0,
    completed_today: 0,
    violations_today: 0
  });
  const [liveAssessments, setLiveAssessments] = useState([]);
  const [scheduledAssessments, setScheduledAssessments] = useState([]);
  const [completedAssessments, setCompletedAssessments] = useState([]);
  const [flaggedViolations, setFlaggedViolations] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [qualityMetrics, setQualityMetrics] = useState({});
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    fetchDashboardData();
    const interval = autoRefresh ? setInterval(fetchDashboardData, 10000) : null;
    return () => clearInterval(interval);
  }, [autoRefresh]);

  useEffect(() => {
    if (activeTab === 'live') fetchLiveAssessments();
    if (activeTab === 'scheduled') fetchScheduledAssessments();
    if (activeTab === 'completed') fetchCompletedAssessments();
    if (activeTab === 'violations') fetchFlaggedViolations();
    if (activeTab === 'anomalies') fetchAnomalies();
    if (activeTab === 'quality') fetchQualityMetrics();
  }, [activeTab]);

  const fetchDashboardData = async () => {
    try {
      const response = await api.get('/api/proctor/dashboard-stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    }
  };

  const fetchLiveAssessments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/proctor/active-assessments');
      setLiveAssessments(response.data);
    } catch (error) {
      console.error('Error fetching live assessments:', error);
    }
    setLoading(false);
  };

  const fetchScheduledAssessments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/proctor/scheduled-assessments');
      setScheduledAssessments(response.data);
    } catch (error) {
      console.error('Error fetching scheduled assessments:', error);
    }
    setLoading(false);
  };

  const fetchCompletedAssessments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/proctor/completed-assessments');
      setCompletedAssessments(response.data);
    } catch (error) {
      console.error('Error fetching completed assessments:', error);
    }
    setLoading(false);
  };

  const fetchFlaggedViolations = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/proctor/violations/flagged');
      setFlaggedViolations(response.data);
    } catch (error) {
      console.error('Error fetching violations:', error);
    }
    setLoading(false);
  };

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/proctor/anomaly-detection');
      setAnomalies(response.data.suspicious_assessments || []);
    } catch (error) {
      console.error('Error fetching anomalies:', error);
    }
    setLoading(false);
  };

  const fetchQualityMetrics = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/proctor/quality-metrics');
      setQualityMetrics(response.data);
    } catch (error) {
      console.error('Error fetching quality metrics:', error);
    }
    setLoading(false);
  };

  const getSuspicionColor = (level) => {
    switch (level) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      default: return 'outline';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'in_progress': return 'animate-pulse';
      case 'overdue': return 'text-red-600';
      case 'near_end': return 'text-orange-600';
      default: return '';
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userRole');
    navigate('/login');
  };

  // Handler for Monitor button - opens monitor view
  const [showMonitorModal, setShowMonitorModal] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [reviewNotes, setReviewNotes] = useState('');
  const [showReviewModal, setShowReviewModal] = useState(false);

  const handleMonitor = (assessment) => {
    setSelectedAssessment(assessment);
    setShowMonitorModal(true);
  };

  const handleReviewViolation = (violation) => {
    setSelectedAssessment(violation);
    setReviewNotes('');
    setShowReviewModal(true);
  };

  const handleSubmitReview = async () => {
    if (!selectedAssessment) return;
    try {
      await api.post(`/api/proctor/violations/${selectedAssessment.id}/review`, {
        reviewer_notes: reviewNotes
      });
      setShowReviewModal(false);
      fetchFlaggedViolations();
      alert('Review submitted successfully');
    } catch (error) {
      console.error('Error submitting review:', error);
      alert('Failed to submit review');
    }
  };

  const handleFlagForReview = async (assessment) => {
    try {
      await api.post(`/api/proctor/assessments/${assessment.id}/flag`, {
        reason: 'Flagged from anomaly detection'
      });
      fetchAnomalies();
      alert('Assessment flagged for review');
    } catch (error) {
      console.error('Error flagging assessment:', error);
      alert('Failed to flag assessment');
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Proctor Dashboard</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Auto-refresh (10s)
            </label>
            <Badge variant="outline" className={autoRefresh ? 'animate-pulse' : ''}>
              {stats.active_assessments} Live
            </Badge>
          </div>
          <Button variant="destructive" onClick={handleLogout} className="gap-2">
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>
      </div>

      {/* STATS CARDS */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="border-blue-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="w-4 h-4 text-blue-600" /> Active Now
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600 animate-pulse">{stats.active_assessments}</div>
            <p className="text-xs text-gray-500 mt-1">Currently being assessed</p>
          </CardContent>
        </Card>

        <Card className="border-yellow-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <Clock className="w-4 h-4 text-yellow-600" /> Scheduled Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">{stats.scheduled_today}</div>
            <p className="text-xs text-gray-500 mt-1">Yet to start</p>
          </CardContent>
        </Card>

        <Card className="border-green-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-600" /> Completed Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{stats.completed_today}</div>
            <p className="text-xs text-gray-500 mt-1">Successfully finished</p>
          </CardContent>
        </Card>

        <Card className="border-red-200">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-600" /> Violations Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{stats.violations_today}</div>
            <p className="text-xs text-gray-500 mt-1">Incidents recorded</p>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="live">Live ({stats.active_assessments})</TabsTrigger>
          <TabsTrigger value="scheduled">Scheduled</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
          <TabsTrigger value="anomalies">Anomalies</TabsTrigger>
          <TabsTrigger value="quality">Quality</TabsTrigger>
          <TabsTrigger value="metrics">Metrics</TabsTrigger>
        </TabsList>

        {/* LIVE ASSESSMENTS TAB */}
        <TabsContent value="live" className="space-y-4">
          {liveAssessments.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-gray-500">No active assessments at the moment</p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {liveAssessments.map((assessment) => (
                <Card key={assessment.assessment_id} className="border-orange-200 bg-orange-50">
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-base">{assessment.candidate_name}</CardTitle>
                        <p className="text-sm text-gray-600">{assessment.job_title}</p>
                      </div>
                      <div className="flex gap-2">
                        <Badge className={`animate-pulse ${getStatusColor(assessment.time_status)}`}>
                          {assessment.time_status?.replace('_', ' ').toUpperCase()}
                        </Badge>
                        {assessment.violation_count > 2 && (
                          <Badge variant="destructive">⚠️ {assessment.violation_count} violations</Badge>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div>
                        <p className="text-xs text-gray-600">Time Elapsed</p>
                        <p className="font-semibold">
                          {Math.round((Date.now() - new Date(assessment.started_at)) / 60000)} min
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Violations</p>
                        <p className={`font-semibold ${assessment.violation_count > 2 ? 'text-red-600' : ''}`}>
                          {assessment.violation_count}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Candidate Email</p>
                        <p className="font-semibold text-sm">{assessment.candidate_email}</p>
                      </div>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => handleMonitor(assessment)}>
                      <Eye className="w-4 h-4 mr-2" /> Monitor
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* SCHEDULED ASSESSMENTS TAB */}
        <TabsContent value="scheduled" className="space-y-4">
          <div className="space-y-3">
            {scheduledAssessments.map((assessment) => (
              <Card key={assessment.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base">{assessment.candidate_name}</CardTitle>
                      <p className="text-sm text-gray-600">{assessment.job_title}</p>
                    </div>
                    <Badge variant="outline">
                      In {assessment.minutes_until_start} min
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm">
                    <span className="font-semibold">Scheduled:</span> {new Date(assessment.scheduled_time).toLocaleString()}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* COMPLETED ASSESSMENTS TAB */}
        <TabsContent value="completed" className="space-y-3">
          {completedAssessments.map((assessment) => (
            <Card key={assessment.id}>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-base">{assessment.candidate_name}</CardTitle>
                    <p className="text-sm text-gray-600">{assessment.job_title}</p>
                  </div>
                  <Badge variant="secondary">
                    {Math.round(assessment.overall_score || 0)}%
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-3 text-sm">
                  <div>
                    <p className="text-gray-600">Technical</p>
                    <p className="font-bold">{Math.round(assessment.technical_score || 0)}%</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Psychometric</p>
                    <p className="font-bold">{Math.round(assessment.psychometric_score || 0)}%</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Violations</p>
                    <p className={`font-bold ${assessment.violation_count > 2 ? 'text-red-600' : ''}`}>
                      {assessment.violation_count}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600">Completed</p>
                    <p className="font-bold">{new Date(assessment.completed_at).toLocaleTimeString()}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* VIOLATIONS TAB */}
        <TabsContent value="violations" className="space-y-3">
          {flaggedViolations.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-gray-500">No flagged violations</p>
              </CardContent>
            </Card>
          ) : (
            flaggedViolations.map((violation) => (
              <Card key={violation.id} className={violation.severity === 'critical' ? 'border-red-400' : 'border-orange-400'}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base">{violation.candidate_name}</CardTitle>
                      <p className="text-sm text-gray-600">{violation.job_title}</p>
                    </div>
                    <Badge variant={violation.severity === 'critical' ? 'destructive' : 'secondary'}>
                      {violation.event_type}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <p className="text-sm">{violation.details}</p>
                  <Button size="sm" variant="outline" onClick={() => handleReviewViolation(violation)}>
                    <MessageSquare className="w-4 h-4 mr-2" /> Review & Comment
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* ANOMALIES TAB */}
        <TabsContent value="anomalies" className="space-y-3">
          {anomalies.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-gray-500">No suspicious patterns detected</p>
              </CardContent>
            </Card>
          ) : (
            anomalies.map((assessment) => (
              <Card key={assessment.id} className="border-red-300 bg-red-50">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base">{assessment.candidate_name}</CardTitle>
                      <p className="text-sm text-gray-600">{assessment.job_title}</p>
                    </div>
                    <Badge variant={getSuspicionColor(assessment.suspicion_level)}>
                      {assessment.suspicion_level.toUpperCase()}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    <div>
                      <p className="text-gray-600">Violations</p>
                      <p className="font-bold text-red-600">{assessment.violation_count}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Types</p>
                      <p className="font-semibold">{assessment.violation_types}</p>
                    </div>
                    <div>
                      <p className="text-gray-600">Score</p>
                      <p className="font-bold">{Math.round(assessment.overall_score || 0)}%</p>
                    </div>
                  </div>
                  <Button size="sm" variant="destructive" onClick={() => handleFlagForReview(assessment)}>
                    <AlertCircle className="w-4 h-4 mr-2" /> Flag for Review
                  </Button>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* QUALITY METRICS TAB */}
        <TabsContent value="quality" className="space-y-4">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Total Proctored</p>
                <p className="text-3xl font-bold">{qualityMetrics.total_proctored || 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Completed</p>
                <p className="text-3xl font-bold text-green-600">{qualityMetrics.completed || 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Flagged</p>
                <p className="text-3xl font-bold text-red-600">{qualityMetrics.flagged_assessments || 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Avg Violations</p>
                <p className="text-3xl font-bold">{(qualityMetrics.avg_violations_per_assessment || 0).toFixed(1)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Critical Violations</p>
                <p className="text-3xl font-bold text-red-600">{qualityMetrics.critical_violations || 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-gray-600">Reviewed</p>
                <p className="text-3xl font-bold text-blue-600">{qualityMetrics.reviewed_violations || 0}</p>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* METRICS TAB */}
        <TabsContent value="metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Performance by Job Type</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between p-3 bg-gray-50 rounded">
                  <span className="font-semibold">Job Type</span>
                  <span className="font-semibold">Assessments</span>
                  <span className="font-semibold">Avg Score</span>
                  <span className="font-semibold">Violations</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Modal Components */}
      <MonitorModal
        show={showMonitorModal}
        assessment={selectedAssessment}
        onClose={() => setShowMonitorModal(false)}
      />
      <ReviewModal
        show={showReviewModal}
        violation={selectedAssessment}
        notes={reviewNotes}
        setNotes={setReviewNotes}
        onSubmit={handleSubmitReview}
        onClose={() => setShowReviewModal(false)}
      />
    </div>
  );
};

// Monitor Modal Component
const MonitorModal = ({ show, assessment, onClose }) => {
  if (!show || !assessment) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Monitoring: {assessment.candidate_name}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-100 rounded-lg p-4">
              <h3 className="font-semibold mb-2">Assessment Info</h3>
              <p><span className="text-gray-600">Job:</span> {assessment.job_title}</p>
              <p><span className="text-gray-600">Email:</span> {assessment.candidate_email}</p>
              <p><span className="text-gray-600">Started:</span> {new Date(assessment.started_at).toLocaleString()}</p>
            </div>
            <div className="bg-gray-100 rounded-lg p-4">
              <h3 className="font-semibold mb-2">Proctoring Status</h3>
              <p><span className="text-gray-600">Violations:</span> <span className={assessment.violation_count > 2 ? 'text-red-600 font-bold' : ''}>{assessment.violation_count}</span></p>
              <p><span className="text-gray-600">Status:</span> {assessment.time_status}</p>
            </div>
          </div>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">Live video monitoring requires webcam permission from the candidate. Real-time feed will appear here when available.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

// Review Modal Component  
const ReviewModal = ({ show, violation, notes, setNotes, onSubmit, onClose }) => {
  if (!show || !violation) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-lg w-full">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="text-xl font-semibold">Review Violation</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <p className="font-semibold">{violation.candidate_name}</p>
            <p className="text-sm text-gray-600">{violation.event_type}</p>
            <p className="text-sm mt-2">{violation.details}</p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Reviewer Notes</label>
            <textarea
              className="w-full border rounded-md p-2 min-h-[100px]"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add your review notes here..."
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={onSubmit}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Submit Review
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 border rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProctorDashboard;
