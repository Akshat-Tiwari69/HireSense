import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Activity, Clock, CheckCircle, AlertTriangle, Eye, MessageSquare } from 'lucide-react';
import api from '@/services/api';

const ProctorDashboard = () => {
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
      const response = await api.get('/proctor/dashboard-stats');
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
    }
  };

  const fetchLiveAssessments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/proctor/active-assessments');
      setLiveAssessments(response.data);
    } catch (error) {
      console.error('Error fetching live assessments:', error);
    }
    setLoading(false);
  };

  const fetchScheduledAssessments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/proctor/scheduled-assessments');
      setScheduledAssessments(response.data);
    } catch (error) {
      console.error('Error fetching scheduled assessments:', error);
    }
    setLoading(false);
  };

  const fetchCompletedAssessments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/proctor/completed-assessments');
      setCompletedAssessments(response.data);
    } catch (error) {
      console.error('Error fetching completed assessments:', error);
    }
    setLoading(false);
  };

  const fetchFlaggedViolations = async () => {
    setLoading(true);
    try {
      const response = await api.get('/proctor/violations/flagged');
      setFlaggedViolations(response.data);
    } catch (error) {
      console.error('Error fetching violations:', error);
    }
    setLoading(false);
  };

  const fetchAnomalies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/proctor/anomaly-detection');
      setAnomalies(response.data.suspicious_assessments || []);
    } catch (error) {
      console.error('Error fetching anomalies:', error);
    }
    setLoading(false);
  };

  const fetchQualityMetrics = async () => {
    setLoading(true);
    try {
      const response = await api.get('/proctor/quality-metrics');
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

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Proctor Dashboard</h1>
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
                    <Button variant="outline" size="sm">
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
                  <Button size="sm" variant="outline">
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
                  <Button size="sm" variant="destructive">
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
    </div>
  );
};

export default ProctorDashboard;
