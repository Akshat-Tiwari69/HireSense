import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Plus, Search, Wand2, BarChart3, Clock, CheckCircle, Users } from 'lucide-react';
import { api } from '@/services/api';

const InterviewerDashboard = () => {
  const [activeTab, setActiveTab] = useState('my-jobs');
  const [jobs, setJobs] = useState([]);
  const [activeAssessments, setActiveAssessments] = useState([]);
  const [jobAnalytics, setJobAnalytics] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showJobModal, setShowJobModal] = useState(false);
  const [newJob, setNewJob] = useState({
    title: '',
    description: '',
    required_skills: [],
    min_experience: 0,
    department: '',
    location: ''
  });

  useEffect(() => {
    if (activeTab === 'my-jobs') fetchJobs();
    if (activeTab === 'active') fetchActiveAssessments();
  }, [activeTab]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/interviewer/my-jobs');
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
    setLoading(false);
  };

  const fetchActiveAssessments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/interviewer/active-assessments');
      setActiveAssessments(response.data);
    } catch (error) {
      console.error('Error fetching assessments:', error);
    }
    setLoading(false);
  };

  const createJob = async () => {
    try {
      await api.post('/interviewer/jobs', newJob);
      setShowJobModal(false);
      setNewJob({
        title: '',
        description: '',
        required_skills: [],
        min_experience: 0,
        department: '',
        location: ''
      });
      fetchJobs();
    } catch (error) {
      console.error('Error creating job:', error);
    }
  };

  const refineJobWithAI = async (jobId) => {
    try {
      const response = await api.post(`/interviewer/jobs/${jobId}/ai-refine`, {});
      alert('Job refined with AI! Check the job details for updates.');
      fetchJobs();
    } catch (error) {
      console.error('Error refining job:', error);
    }
  };

  const viewJobAnalytics = async (jobId) => {
    try {
      const response = await api.get(`/interviewer/jobs/${jobId}/analytics`);
      setJobAnalytics(response.data);
      setActiveTab('analytics');
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Interviewer Dashboard</h1>
        <Badge variant="outline">Job Management & Assessment Control</Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="my-jobs">My Job Postings</TabsTrigger>
          <TabsTrigger value="active">Active Assessments</TabsTrigger>
          <TabsTrigger value="results">Assessment Results</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        {/* MY JOB POSTINGS TAB */}
        <TabsContent value="my-jobs" className="space-y-4">
          <div className="flex gap-2 mb-4">
            <Button onClick={() => setShowJobModal(true)} className="gap-2">
              <Plus className="w-4 h-4" /> Create New Job
            </Button>
          </div>

          {showJobModal && (
            <Card className="border-blue-500">
              <CardHeader>
                <CardTitle>Create New Job Posting</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-semibold">Job Title *</label>
                  <Input
                    placeholder="e.g., Senior Software Engineer"
                    value={newJob.title}
                    onChange={(e) => setNewJob({ ...newJob, title: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-semibold">Description *</label>
                  <textarea
                    className="w-full border rounded p-2 h-24"
                    placeholder="Job description..."
                    value={newJob.description}
                    onChange={(e) => setNewJob({ ...newJob, description: e.target.value })}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Department</label>
                    <Input
                      value={newJob.department}
                      onChange={(e) => setNewJob({ ...newJob, department: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Location</label>
                    <Input
                      value={newJob.location}
                      onChange={(e) => setNewJob({ ...newJob, location: e.target.value })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Min Experience (years)</label>
                    <Input
                      type="number"
                      value={newJob.min_experience}
                      onChange={(e) => setNewJob({ ...newJob, min_experience: parseInt(e.target.value) })}
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-semibold">Required Skills</label>
                    <Input
                      placeholder="Python, JavaScript, React..."
                      onChange={(e) => setNewJob({
                        ...newJob,
                        required_skills: e.target.value.split(',').map(s => s.trim())
                      })}
                    />
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button onClick={createJob}>Create Job</Button>
                  <Button variant="outline" onClick={() => setShowJobModal(false)}>Cancel</Button>
                </div>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-4">
            {jobs.map((job) => (
              <Card key={job.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <CardTitle>{job.title}</CardTitle>
                      <p className="text-sm text-gray-600">{job.department} • {job.location}</p>
                    </div>
                    <Badge variant={job.role_complexity_level === 'senior' ? 'destructive' : 'secondary'}>
                      {job.role_complexity_level || 'standard'}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="space-y-4">
                  <p className="text-sm">{job.description?.substring(0, 150)}...</p>

                  {job.skill_taxonomy && (
                    <div>
                      <p className="text-xs font-semibold text-gray-600 mb-2">Skills:</p>
                      <div className="flex flex-wrap gap-1">
                        {job.skill_taxonomy?.slice(0, 5).map((skill) => (
                          <Badge key={skill} variant="secondary" className="text-xs">{skill}</Badge>
                        ))}
                        {job.skill_taxonomy?.length > 5 && (
                          <Badge variant="outline" className="text-xs">+{job.skill_taxonomy.length - 5}</Badge>
                        )}
                      </div>
                    </div>
                  )}

                  {job.analytics && (
                    <div className="grid grid-cols-3 gap-2 bg-blue-50 p-3 rounded">
                      <div>
                        <p className="text-xs text-gray-600">Assessments</p>
                        <p className="font-bold">{job.analytics.total_assessments || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Completed</p>
                        <p className="font-bold">{job.analytics.completed_assessments || 0}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600">Hired</p>
                        <p className="font-bold text-green-600">{job.analytics.hired_count || 0}</p>
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2 flex-wrap">
                    <Button variant="outline" size="sm" onClick={() => refineJobWithAI(job.id)}>
                      <Wand2 className="w-4 h-4 mr-1" /> AI Refine
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => viewJobAnalytics(job.id)}>
                      <BarChart3 className="w-4 h-4 mr-1" /> Analytics
                    </Button>
                    <Button size="sm">
                      <Users className="w-4 h-4 mr-1" /> Schedule Assessment
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ACTIVE ASSESSMENTS TAB */}
        <TabsContent value="active" className="space-y-4">
          <div className="grid gap-4">
            {activeAssessments.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-center text-gray-500">No active assessments</p>
                </CardContent>
              </Card>
            ) : (
              activeAssessments.map((assessment) => (
                <Card key={assessment.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="text-base">{assessment.candidate_name}</CardTitle>
                        <p className="text-sm text-gray-600">{assessment.job_title}</p>
                      </div>
                      <Badge variant="destructive" className="animate-pulse">In Progress</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-gray-600">Started</p>
                        <p className="font-semibold">{new Date(assessment.started_at).toLocaleTimeString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-600">Violations</p>
                        <p className={`font-semibold ${assessment.proctoring_violations > 2 ? 'text-red-600' : ''}`}>
                          {assessment.proctoring_violations}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-600">Time Elapsed</p>
                        <p className="font-semibold">
                          {Math.round((Date.now() - new Date(assessment.started_at)) / 60000)} min
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </TabsContent>

        {/* ANALYTICS TAB */}
        <TabsContent value="analytics" className="space-y-4">
          {selectedJob ? (
            <Card>
              <CardHeader>
                <CardTitle>Job Analytics: {selectedJob?.title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-blue-50 p-4 rounded">
                    <p className="text-sm text-gray-600">Total Candidates</p>
                    <p className="text-2xl font-bold">{jobAnalytics.total_candidates_for_job || 0}</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded">
                    <p className="text-sm text-gray-600">Completed</p>
                    <p className="text-2xl font-bold">{jobAnalytics.completed_assessments || 0}</p>
                  </div>
                  <div className="bg-purple-50 p-4 rounded">
                    <p className="text-sm text-gray-600">Hired</p>
                    <p className="text-2xl font-bold text-green-600">{jobAnalytics.hired || 0}</p>
                  </div>
                  <div className="bg-red-50 p-4 rounded">
                    <p className="text-sm text-gray-600">Rejected</p>
                    <p className="text-2xl font-bold text-red-600">{jobAnalytics.rejected || 0}</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-sm text-gray-600">Avg Technical Score</p>
                      <p className="text-3xl font-bold">{Math.round(jobAnalytics.avg_technical_score || 0)}%</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <p className="text-sm text-gray-600">Avg Psychometric Score</p>
                      <p className="text-3xl font-bold">{Math.round(jobAnalytics.avg_psychometric_score || 0)}%</p>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-gray-500">Select a job to view analytics</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* SETTINGS TAB */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Your Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-semibold">Default Assessment Template</label>
                <select className="w-full border rounded p-2">
                  <option>None</option>
                  <option>SWE_Junior</option>
                  <option>SWE_Mid</option>
                  <option>SWE_Senior</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold">Assessment Time Window (minutes)</label>
                <Input type="number" defaultValue="30" />
              </div>

              <label className="flex items-center gap-2">
                <input type="checkbox" defaultChecked />
                <span className="text-sm">Email notifications for scheduled assessments</span>
              </label>

              <Button>Save Preferences</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default InterviewerDashboard;
