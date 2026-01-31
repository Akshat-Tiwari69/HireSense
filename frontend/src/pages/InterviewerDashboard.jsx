import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Plus, Search, Wand2, BarChart3, Clock, CheckCircle, Users, LogOut, Eye } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/services/api';

const InterviewerDashboard = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('my-jobs');
  const [jobs, setJobs] = useState([]);
  const [activeAssessments, setActiveAssessments] = useState([]);
  const [jobAnalytics, setJobAnalytics] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [showJobModal, setShowJobModal] = useState(false);
  const [showJobDetailsModal, setShowJobDetailsModal] = useState(false);
  const [candidates, setCandidates] = useState([]);
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
    if (activeTab === 'candidates') fetchCandidates();
  }, [activeTab]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/interviewer/my-jobs');
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
    setLoading(false);
  };

  const fetchActiveAssessments = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/interviewer/active-assessments');
      setActiveAssessments(response.data);
    } catch (error) {
      console.error('Error fetching assessments:', error);
    }
    setLoading(false);
  };

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/interviewer/candidates');
      setCandidates(response.data);
    } catch (error) {
      console.error('Error fetching candidates:', error);
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to fetch candidates' });
    }
    setLoading(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userRole');
    navigate('/login');
  };

  const createJob = async () => {
    try {
      setLoading(true);
      await api.post('/api/interviewer/jobs', newJob);
      toast({ title: 'Success', description: 'Job created successfully!' });
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
      toast({ variant: 'destructive', title: 'Error', description: error?.response?.data?.error || 'Failed to create job' });
    } finally {
      setLoading(false);
    }
  };

  const refineJobWithAI = async (jobId) => {
    try {
      setLoading(true);
      toast({ title: 'AI Processing...', description: 'Refining job description with AI' });
      const response = await api.post(`/api/interviewer/jobs/${jobId}/ai-refine`, {});
      toast({ title: 'Success!', description: 'Job refined with AI. Click "View Details" to see improvements.' });
      fetchJobs();
    } catch (error) {
      console.error('Error refining job:', error);
      toast({ variant: 'destructive', title: 'Error', description: error?.response?.data?.error || 'Failed to refine job' });
    } finally {
      setLoading(false);
    }
  };

  const viewJobAnalytics = async (jobId) => {
    try {
      const response = await api.get(`/api/interviewer/jobs/${jobId}/analytics`);
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
        <div className="flex items-center gap-4">
          <Badge variant="outline">Job Management & Assessment Control</Badge>
          <Button variant="destructive" onClick={handleLogout} className="gap-2">
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="my-jobs">My Job Postings</TabsTrigger>
          <TabsTrigger value="candidates">Candidates</TabsTrigger>
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
                      onChange={(e) => setNewJob({ ...newJob, min_experience: parseInt(e.target.value) || 0 })}
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
                    <Button variant="outline" size="sm" onClick={() => { setSelectedJob(job); setShowJobDetailsModal(true); }}>
                      <Eye className="w-4 h-4 mr-1" /> View Details
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => refineJobWithAI(job.id)} disabled={loading}>
                      <Wand2 className="w-4 h-4 mr-1" /> AI Refine
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => viewJobAnalytics(job.id)}>
                      <BarChart3 className="w-4 h-4 mr-1" /> Analytics
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* CANDIDATES TAB */}
        <TabsContent value="candidates" className="space-y-4">
          <div className="grid gap-4">
            {candidates.length === 0 ? (
              <Card>
                <CardContent className="pt-6">
                  <p className="text-center text-gray-500">No candidates yet</p>
                </CardContent>
              </Card>
            ) : (
              candidates.map((candidate) => {
                const matchScore = candidate.parsed_data?.match_score || 0;
                const matchLevel = matchScore >= 80 ? 'high' : matchScore >= 60 ? 'medium' : 'low';
                const matchColor = matchLevel === 'high' ? 'bg-green-100 text-green-800' : 
                                 matchLevel === 'medium' ? 'bg-yellow-100 text-yellow-800' : 
                                 'bg-red-100 text-red-800';
                
                return (
                  <Card key={candidate.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <CardTitle className="text-base">{candidate.name}</CardTitle>
                          <p className="text-sm text-gray-600">{candidate.email}</p>
                          {candidate.job_title && (
                            <p className="text-sm text-blue-600 mt-1">Applied for: {candidate.job_title}</p>
                          )}
                        </div>
                        <div className="flex gap-2 items-start">
                          <Badge className={matchColor}>
                            {matchScore}% Match
                          </Badge>
                          <Badge variant={candidate.status === 'pending' ? 'secondary' : 'default'}>
                            {candidate.status || 'pending'}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {candidate.parsed_data && (
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-sm font-medium text-gray-700 mb-2">Strengths</p>
                            <ul className="text-sm text-gray-600 list-disc list-inside">
                              {candidate.parsed_data.pros?.slice(0, 3).map((pro, idx) => (
                                <li key={idx}>{pro}</li>
                              ))}
                            </ul>
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-700 mb-2">Areas to Explore</p>
                            <ul className="text-sm text-gray-600 list-disc list-inside">
                              {candidate.parsed_data.cons?.slice(0, 3).map((con, idx) => (
                                <li key={idx}>{con}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}
                      
                      <div className="flex gap-2 pt-2 border-t">
                        {candidate.resume_path && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              const apiBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || window.location.origin;
                              window.open(`${apiBase}${candidate.resume_path}`, '_blank');
                            }}
                          >
                            View Resume
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={async () => {
                            try {
                              const response = await api.get(`/api/interviewer/candidates/${candidate.id}`);
                              toast({
                                title: "Candidate Details",
                                description: `Full details: ${JSON.stringify(response.data, null, 2)}`
                              });
                            } catch (err) {
                              toast({
                                title: "Error",
                                description: "Failed to load candidate details",
                                variant: "destructive"
                              });
                            }
                          }}
                        >
                          View Details
                        </Button>
                        {candidate.status === 'pending' && (
                          <>
                            <Button
                              size="sm"
                              onClick={async () => {
                                try {
                                  await api.post(`/api/interviewer/candidates/${candidate.id}/schedule`, {
                                    scheduled_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
                                  });
                                  toast({
                                    title: "Success",
                                    description: "Interview scheduled successfully"
                                  });
                                  fetchCandidates();
                                } catch (err) {
                                  toast({
                                    title: "Error",
                                    description: "Failed to schedule interview",
                                    variant: "destructive"
                                  });
                                }
                              }}
                            >
                              Schedule Interview
                            </Button>
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={async () => {
                                try {
                                  await api.post(`/api/interviewer/candidates/${candidate.id}/reject`);
                                  toast({
                                    title: "Success",
                                    description: "Candidate rejected"
                                  });
                                  fetchCandidates();
                                } catch (err) {
                                  toast({
                                    title: "Error",
                                    description: "Failed to reject candidate",
                                    variant: "destructive"
                                  });
                                }
                              }}
                            >
                              Reject
                            </Button>
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
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

      {/* Job Details Modal */}
      {showJobDetailsModal && selectedJob && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle>{selectedJob.title}</CardTitle>
                  <p className="text-sm text-gray-600">{selectedJob.department} • {selectedJob.location}</p>
                </div>
                <Button variant="ghost" onClick={() => setShowJobDetailsModal(false)}>✕</Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h3 className="font-semibold mb-2">Original Description</h3>
                <p className="text-sm text-gray-700">{selectedJob.description}</p>
              </div>

              {selectedJob.ai_refined_description && (
                <div className="bg-blue-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2 text-blue-900">✨ AI-Refined Description</h3>
                  <p className="text-sm text-gray-700">{selectedJob.ai_refined_description}</p>
                </div>
              )}

              {selectedJob.ideal_candidate_profile && (
                <div className="bg-green-50 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2 text-green-900">👤 Ideal Candidate Profile</h3>
                  <p className="text-sm text-gray-700">{selectedJob.ideal_candidate_profile}</p>
                </div>
              )}

              <div>
                <h3 className="font-semibold mb-2">Required Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {(selectedJob.required_skills || []).map((skill, idx) => (
                    <Badge key={idx} variant="secondary">{skill}</Badge>
                  ))}
                </div>
              </div>

              {selectedJob.skill_taxonomy && selectedJob.skill_taxonomy.length > 0 && (
                <div>
                  <h3 className="font-semibold mb-2">🎯 AI-Enhanced Skill Taxonomy</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedJob.skill_taxonomy.map((skill, idx) => (
                      <Badge key={idx} variant="outline" className="bg-purple-50">{skill}</Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-semibold text-gray-600">Min Experience</p>
                  <p className="text-lg">{selectedJob.min_experience} years</p>
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-600">Complexity Level</p>
                  <Badge>{selectedJob.role_complexity_level || 'standard'}</Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default InterviewerDashboard;
