import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Plus, Search, Edit, Trash2, Eye, FileText, Settings, BarChart3, LogOut, X, Save, Target } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { api } from '@/services/api';

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [jobs, setJobs] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [assessmentTemplates, setAssessmentTemplates] = useState([]);
  const [scoringProfiles, setScoringProfiles] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [candidateFilter, setCandidateFilter] = useState('all');
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  // Modal states
  const [showJobModal, setShowJobModal] = useState(false);
  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [showEmailTemplateModal, setShowEmailTemplateModal] = useState(false);
  const [showAssessmentTemplateModal, setShowAssessmentTemplateModal] = useState(false);
  const [showScoringProfileModal, setShowScoringProfileModal] = useState(false);
  const [showAnalyticsModal, setShowAnalyticsModal] = useState(false);

  // Edit states
  const [editingItem, setEditingItem] = useState(null);
  const [selectedJobAnalytics, setSelectedJobAnalytics] = useState(null);

  // Form states
  const [jobForm, setJobForm] = useState({ title: '', description: '', department: '', location: '', required_skills: [], min_experience: 0 });
  const [questionForm, setQuestionForm] = useState({ question_text: '', category: '', question_type: 'mcq', difficulty: 'medium', options: [], correct_answer: '' });
  const [emailTemplateForm, setEmailTemplateForm] = useState({ template_name: '', subject: '', body: '', is_default: false });
  const [assessmentTemplateForm, setAssessmentTemplateForm] = useState({ template_name: '', role_type: '', mcq_count: 10, coding_count: 2, psychometric_count: 3, time_limit_minutes: 60 });
  const [scoringProfileForm, setScoringProfileForm] = useState({ name: '', technical_weight: 60, psychometric_weight: 40, passing_score: 70 });

  useEffect(() => {
    if (activeTab === 'jobs') fetchJobs();
    if (activeTab === 'questions') fetchQuestions();
    if (activeTab === 'email-templates') fetchEmailTemplates();
    if (activeTab === 'assessment-templates') fetchAssessmentTemplates();
    if (activeTab === 'scoringprofile') fetchScoringProfiles();
    if (activeTab === 'candidates') fetchCandidates();
    if (activeTab === 'audit') fetchAuditLogs();
  }, [activeTab]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/admin/jobs', { params: { search } });
      setJobs(response.data || []);
    } catch (error) {
      console.error('Error fetching jobs:', error);
      setJobs([]);
    }
    setLoading(false);
  };

  const fetchQuestions = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/admin/question-bank');
      setQuestions(response.data || []);
    } catch (error) {
      console.error('Error fetching questions:', error);
      setQuestions([]);
    }
    setLoading(false);
  };

  const fetchEmailTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/admin/email-templates');
      setEmailTemplates(response.data || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setEmailTemplates([]);
    }
    setLoading(false);
  };

  const fetchAssessmentTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/admin/assessment-templates');
      setAssessmentTemplates(response.data || []);
    } catch (error) {
      console.error('Error fetching assessment templates:', error);
      setAssessmentTemplates([]);
    }
    setLoading(false);
  };

  const fetchScoringProfiles = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/admin/scoring-profiles');
      setScoringProfiles(response.data || []);
    } catch (error) {
      console.error('Error fetching scoring profiles:', error);
      // Default profiles if API not available
      setScoringProfiles([
        { id: 1, name: 'Standard Technical', technical_weight: 60, psychometric_weight: 40, passing_score: 70, is_default: true },
        { id: 2, name: 'Leadership Focus', technical_weight: 40, psychometric_weight: 60, passing_score: 65, is_default: false },
        { id: 3, name: 'Pure Technical', technical_weight: 80, psychometric_weight: 20, passing_score: 75, is_default: false }
      ]);
    }
    setLoading(false);
  };

  const fetchCandidates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/admin/candidates');
      setCandidates(response.data || []);
    } catch (error) {
      console.error('Error fetching candidates:', error);
      setCandidates([]);
    }
    setLoading(false);
  };

  const updateCandidateStatus = async (candidateId, newStatus) => {
    try {
      await api.put(`/api/admin/candidates/${candidateId}/status`, { status: newStatus });
      fetchCandidates();
      alert(`Candidate status updated to ${newStatus}`);
    } catch (error) {
      console.error('Error updating candidate status:', error);
      alert('Failed to update candidate status');
    }
  };

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/api/admin/audit-logs', { params: { limit: 100 } });
      setAuditLogs(response.data || []);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      setAuditLogs([]);
    }
    setLoading(false);
  };

  // Job handlers
  const handleViewJobAnalytics = async (jobId) => {
    try {
      const response = await api.get(`/api/interviewer/jobs/${jobId}/analytics`);
      setSelectedJobAnalytics({ jobId, data: response.data });
      setShowAnalyticsModal(true);
    } catch (error) {
      console.error('Error fetching job analytics:', error);
      alert('Could not load analytics for this job');
    }
  };

  const handleEditJob = (job) => {
    setEditingItem(job);
    setJobForm({
      title: job.title || '',
      description: job.description || '',
      department: job.department || '',
      location: job.location || '',
      required_skills: job.required_skills || [],
      min_experience: job.min_experience || 0
    });
    setShowJobModal(true);
  };

  const handleSaveJob = async () => {
    try {
      if (editingItem) {
        await api.put(`/api/admin/jobs/${editingItem.id}`, jobForm);
      } else {
        await api.post('/api/admin/jobs', jobForm);
      }
      setShowJobModal(false);
      setEditingItem(null);
      setJobForm({ title: '', description: '', department: '', location: '', required_skills: [], min_experience: 0 });
      fetchJobs();
    } catch (error) {
      console.error('Error saving job:', error);
      alert('Failed to save job');
    }
  };

  const deleteJob = async (jobId) => {
    if (window.confirm('Archive this job?')) {
      try {
        await api.delete(`/api/admin/jobs/${jobId}`);
        setJobs(jobs.filter(j => j.id !== jobId));
      } catch (error) {
        console.error('Error deleting job:', error);
      }
    }
  };

  // Question handlers
  const handleEditQuestion = (question) => {
    setEditingItem(question);
    setQuestionForm({
      question_text: question.question_text || '',
      category: question.category || '',
      question_type: question.question_type || 'mcq',
      difficulty: question.difficulty || 'medium',
      options: question.options || [],
      correct_answer: question.correct_answer || ''
    });
    setShowQuestionModal(true);
  };

  const handleSaveQuestion = async () => {
    try {
      if (editingItem) {
        await api.put(`/api/admin/question-bank/${editingItem.id}`, questionForm);
      } else {
        await api.post('/api/admin/question-bank', questionForm);
      }
      setShowQuestionModal(false);
      setEditingItem(null);
      setQuestionForm({ question_text: '', category: '', question_type: 'mcq', difficulty: 'medium', options: [], correct_answer: '' });
      fetchQuestions();
    } catch (error) {
      console.error('Error saving question:', error);
      alert('Failed to save question');
    }
  };

  const deleteQuestion = async (questionId) => {
    if (window.confirm('Delete this question?')) {
      try {
        await api.delete(`/api/admin/question-bank/${questionId}`);
        setQuestions(questions.filter(q => q.id !== questionId));
      } catch (error) {
        console.error('Error deleting question:', error);
      }
    }
  };

  // Email template handlers
  const handleEditEmailTemplate = (template) => {
    setEditingItem(template);
    setEmailTemplateForm({
      template_name: template.template_name || '',
      subject: template.subject || '',
      body: template.body || '',
      is_default: template.is_default || false
    });
    setShowEmailTemplateModal(true);
  };

  const handleSaveEmailTemplate = async () => {
    try {
      if (editingItem) {
        await api.put(`/api/admin/email-templates/${editingItem.id}`, emailTemplateForm);
      } else {
        await api.post('/api/admin/email-templates', emailTemplateForm);
      }
      setShowEmailTemplateModal(false);
      setEditingItem(null);
      setEmailTemplateForm({ template_name: '', subject: '', body: '', is_default: false });
      fetchEmailTemplates();
    } catch (error) {
      console.error('Error saving email template:', error);
      alert('Failed to save email template');
    }
  };

  const deleteEmailTemplate = async (templateId) => {
    if (window.confirm('Delete this email template?')) {
      try {
        await api.delete(`/api/admin/email-templates/${templateId}`);
        setEmailTemplates(emailTemplates.filter(t => t.id !== templateId));
      } catch (error) {
        console.error('Error deleting email template:', error);
      }
    }
  };

  // Assessment template handlers
  const handleEditAssessmentTemplate = (template) => {
    setEditingItem(template);
    setAssessmentTemplateForm({
      template_name: template.template_name || '',
      role_type: template.role_type || '',
      mcq_count: template.mcq_count || 10,
      coding_count: template.coding_count || 2,
      psychometric_count: template.psychometric_count || 3,
      time_limit_minutes: template.time_limit_minutes || 60
    });
    setShowAssessmentTemplateModal(true);
  };

  const handleSaveAssessmentTemplate = async () => {
    try {
      if (editingItem) {
        await api.put(`/api/admin/assessment-templates/${editingItem.id}`, assessmentTemplateForm);
      } else {
        await api.post('/api/admin/assessment-templates', assessmentTemplateForm);
      }
      setShowAssessmentTemplateModal(false);
      setEditingItem(null);
      setAssessmentTemplateForm({ template_name: '', role_type: '', mcq_count: 10, coding_count: 2, psychometric_count: 3, time_limit_minutes: 60 });
      fetchAssessmentTemplates();
    } catch (error) {
      console.error('Error saving assessment template:', error);
      alert('Failed to save assessment template');
    }
  };

  const deleteAssessmentTemplate = async (templateId) => {
    if (window.confirm('Delete this assessment template?')) {
      try {
        await api.delete(`/api/admin/assessment-templates/${templateId}`);
        setAssessmentTemplates(assessmentTemplates.filter(t => t.id !== templateId));
      } catch (error) {
        console.error('Error deleting assessment template:', error);
      }
    }
  };

  // Scoring profile handlers
  const handleEditScoringProfile = (profile) => {
    setEditingItem(profile);
    setScoringProfileForm({
      name: profile.name || '',
      technical_weight: profile.technical_weight || 60,
      psychometric_weight: profile.psychometric_weight || 40,
      passing_score: profile.passing_score || 70
    });
    setShowScoringProfileModal(true);
  };

  const handleSaveScoringProfile = async () => {
    try {
      if (editingItem) {
        await api.put(`/api/admin/scoring-profiles/${editingItem.id}`, scoringProfileForm);
      } else {
        await api.post('/api/admin/scoring-profiles', scoringProfileForm);
      }
      setShowScoringProfileModal(false);
      setEditingItem(null);
      setScoringProfileForm({ name: '', technical_weight: 60, psychometric_weight: 40, passing_score: 70 });
      fetchScoringProfiles();
    } catch (error) {
      console.error('Error saving scoring profile:', error);
      alert('Failed to save scoring profile');
    }
  };

  const deleteScoringProfile = async (profileId) => {
    if (window.confirm('Delete this scoring profile?')) {
      try {
        await api.delete(`/api/admin/scoring-profiles/${profileId}`);
        setScoringProfiles(scoringProfiles.filter(p => p.id !== profileId));
      } catch (error) {
        console.error('Error deleting scoring profile:', error);
      }
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userRole');
    navigate('/login');
  };

  // Modal Component
  const Modal = ({ show, onClose, title, children }) => {
    if (!show) return null;
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto m-4">
          <div className="flex justify-between items-center p-4 border-b">
            <h2 className="text-xl font-semibold">{title}</h2>
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          <div className="p-4">{children}</div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <div className="flex items-center gap-4">
          <Badge variant="outline">Full System Control</Badge>
          <Button variant="destructive" onClick={handleLogout} className="gap-2">
            <LogOut className="w-4 h-4" />
            Logout
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-8">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="candidates">Candidates</TabsTrigger>
          <TabsTrigger value="jobs">Jobs</TabsTrigger>
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="email-templates">Emails</TabsTrigger>
          <TabsTrigger value="assessment-templates">Assessments</TabsTrigger>
          <TabsTrigger value="scoringprofile">Scoring</TabsTrigger>
          <TabsTrigger value="audit">Audit</TabsTrigger>
        </TabsList>

        {/* OVERVIEW TAB */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Total Jobs</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{jobs.length}</div>
                <p className="text-xs text-gray-500">Active job postings</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Question Bank</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{questions.length}</div>
                <p className="text-xs text-gray-500">Questions available</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Email Templates</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{emailTemplates.length}</div>
                <p className="text-xs text-gray-500">Custom templates</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium">Assessment Templates</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{assessmentTemplates.length}</div>
                <p className="text-xs text-gray-500">Template configurations</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>System Control Features</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button className="w-full" onClick={() => setActiveTab('jobs')}>
                  <Plus className="w-4 h-4 mr-2" /> Manage Jobs
                </Button>
                <Button className="w-full" onClick={() => setActiveTab('questions')}>
                  <FileText className="w-4 h-4 mr-2" /> Question Bank
                </Button>
                <Button className="w-full" onClick={() => setActiveTab('email-templates')}>
                  <Settings className="w-4 h-4 mr-2" /> Email Templates
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* CANDIDATES TAB */}
        <TabsContent value="candidates" className="space-y-4">
          <div className="flex gap-2 items-center">
            <select
              className="border rounded p-2"
              value={candidateFilter}
              onChange={(e) => setCandidateFilter(e.target.value)}
            >
              <option value="all">All Candidates</option>
              <option value="Applied">Applied</option>
              <option value="Scheduled">Scheduled</option>
              <option value="Assessment Complete">Assessment Complete</option>
              <option value="Hired">Hired</option>
              <option value="Rejected">Rejected</option>
            </select>
            <Button variant="outline" onClick={fetchCandidates}>Refresh</Button>
            <span className="text-sm text-gray-500 ml-auto">
              {candidates.filter(c => candidateFilter === 'all' || c.status === candidateFilter).length} candidates
            </span>
          </div>

          <div className="grid gap-4">
            {candidates
              .filter(c => candidateFilter === 'all' || c.status === candidateFilter)
              .map((candidate) => {
                const getStatusBadgeVariant = (status) => {
                  switch (status) {
                    case 'Applied': return 'secondary';
                    case 'Scheduled': return 'default';
                    case 'Assessment Complete': return 'outline';
                    case 'Hired': return 'default';
                    case 'Rejected': return 'destructive';
                    default: return 'secondary';
                  }
                };

                return (
                  <Card key={candidate.id}>
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-base">{candidate.name}</CardTitle>
                          <p className="text-sm text-gray-600">{candidate.email}</p>
                          {candidate.job_title && (
                            <p className="text-sm text-blue-600">Applied for: {candidate.job_title}</p>
                          )}
                        </div>
                        <div className="flex gap-2 items-center">
                          <Badge variant={getStatusBadgeVariant(candidate.status)}>
                            {candidate.status || 'Applied'}
                          </Badge>
                          <Badge variant="outline">
                            {candidate.parsed_data?.match_score || 0}% Match
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex gap-2 items-center">
                        <span className="text-sm font-medium">Change Status:</span>
                        <select
                          className="border rounded p-1 text-sm"
                          value={candidate.status || 'Applied'}
                          onChange={(e) => updateCandidateStatus(candidate.id, e.target.value)}
                        >
                          <option value="Applied">Applied</option>
                          <option value="Scheduled">Scheduled</option>
                          <option value="Assessment Complete">Assessment Complete</option>
                          <option value="Hired">Hired</option>
                          <option value="Rejected">Rejected</option>
                        </select>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000';
                            if (candidate.resume_path) {
                              window.open(`${apiBase}${candidate.resume_path}`, '_blank');
                            }
                          }}
                        >
                          View Resume
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            {candidates.filter(c => candidateFilter === 'all' || c.status === candidateFilter).length === 0 && (
              <Card>
                <CardContent className="pt-6 text-center">
                  <p className="text-gray-500">No candidates found</p>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* JOBS TAB */}
        <TabsContent value="jobs" className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Search jobs..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                fetchJobs();
              }}
            />
            <Button onClick={() => { setEditingItem(null); setJobForm({ title: '', description: '', department: '', location: '', required_skills: [], min_experience: 0 }); setShowJobModal(true); }}>
              <Plus className="w-4 h-4 mr-2" /> New Job
            </Button>
          </div>

          <div className="grid gap-4">
            {jobs.map((job) => (
              <Card key={job.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle>{job.title}</CardTitle>
                      <p className="text-sm text-gray-500 mt-1">{job.department} • {job.location}</p>
                    </div>
                    <Badge>{job.role_complexity_level || 'standard'}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm">{job.description}</p>
                  <div>
                    <p className="text-xs font-semibold text-gray-600">Required Skills:</p>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {(job.required_skills || []).map((skill) => (
                        <Badge key={skill} variant="secondary">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleViewJobAnalytics(job.id)}>
                      <Eye className="w-4 h-4 mr-2" /> View Analytics
                    </Button>
                    <Button variant="outline" size="sm" onClick={() => handleEditJob(job)}>
                      <Edit className="w-4 h-4 mr-2" /> Edit
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => deleteJob(job.id)}>
                      <Trash2 className="w-4 h-4 mr-2" /> Archive
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* QUESTIONS TAB */}
        <TabsContent value="questions" className="space-y-4">
          <div className="flex gap-2">
            <Input placeholder="Search questions..." />
            <Button onClick={() => { setEditingItem(null); setQuestionForm({ question_text: '', category: '', question_type: 'mcq', difficulty: 'medium', options: [], correct_answer: '' }); setShowQuestionModal(true); }}>
              <Plus className="w-4 h-4 mr-2" /> Add Question
            </Button>
          </div>

          <div className="space-y-3">
            {questions.map((q) => (
              <Card key={q.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base">{(q.question_text || '').substring(0, 80)}...</CardTitle>
                      <p className="text-sm text-gray-500 mt-1">{q.category}</p>
                    </div>
                    <div className="flex gap-2">
                      <Badge>{q.question_type}</Badge>
                      <Badge variant="outline">{q.difficulty}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleEditQuestion(q)}>
                      <Edit className="w-4 h-4 mr-2" /> Edit
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => deleteQuestion(q.id)}>
                      <Trash2 className="w-4 h-4 mr-2" /> Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* EMAIL TEMPLATES TAB */}
        <TabsContent value="email-templates" className="space-y-4">
          <Button onClick={() => { setEditingItem(null); setEmailTemplateForm({ template_name: '', subject: '', body: '', is_default: false }); setShowEmailTemplateModal(true); }}>
            <Plus className="w-4 h-4 mr-2" /> Create Template
          </Button>

          <div className="grid gap-4">
            {emailTemplates.map((template) => (
              <Card key={template.id}>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-base">{template.template_name}</CardTitle>
                    {template.is_default && <Badge>Default</Badge>}
                  </div>
                  <p className="text-sm text-gray-600">{template.subject}</p>
                </CardHeader>
                <CardContent>
                  <div className="bg-gray-50 p-3 rounded text-sm max-h-32 overflow-auto">
                    {template.body}
                  </div>
                  <div className="flex gap-2 mt-3">
                    <Button variant="outline" size="sm" onClick={() => handleEditEmailTemplate(template)}>
                      <Edit className="w-4 h-4 mr-2" /> Edit
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => deleteEmailTemplate(template.id)}>
                      <Trash2 className="w-4 h-4 mr-2" /> Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ASSESSMENT TEMPLATES TAB */}
        <TabsContent value="assessment-templates" className="space-y-4">
          <Button onClick={() => { setEditingItem(null); setAssessmentTemplateForm({ template_name: '', role_type: '', mcq_count: 10, coding_count: 2, psychometric_count: 3, time_limit_minutes: 60 }); setShowAssessmentTemplateModal(true); }}>
            <Plus className="w-4 h-4 mr-2" /> Create Template
          </Button>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {assessmentTemplates.map((template) => (
              <Card key={template.id}>
                <CardHeader>
                  <CardTitle className="text-base">{template.template_name}</CardTitle>
                  <p className="text-sm text-gray-600">{template.role_type}</p>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <p className="font-semibold">MCQ</p>
                      <p>{template.mcq_count}</p>
                    </div>
                    <div>
                      <p className="font-semibold">Coding</p>
                      <p>{template.coding_count}</p>
                    </div>
                    <div>
                      <p className="font-semibold">Psych</p>
                      <p>{template.psychometric_count}</p>
                    </div>
                  </div>
                  <p className="text-xs">
                    <span className="font-semibold">Time:</span> {template.time_limit_minutes} min
                  </p>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleEditAssessmentTemplate(template)}>
                      <Edit className="w-4 h-4 mr-2" /> Edit
                    </Button>
                    <Button variant="destructive" size="sm" onClick={() => deleteAssessmentTemplate(template.id)}>
                      <Trash2 className="w-4 h-4 mr-2" /> Delete
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* SCORING PROFILES TAB */}
        <TabsContent value="scoringprofile" className="space-y-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold">Scoring Profiles</h2>
              <p className="text-sm text-gray-500">Configure how assessments are scored and weighted</p>
            </div>
            <Button onClick={() => { setEditingItem(null); setScoringProfileForm({ name: '', technical_weight: 60, psychometric_weight: 40, passing_score: 70 }); setShowScoringProfileModal(true); }}>
              <Plus className="w-4 h-4 mr-2" /> Create Profile
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scoringProfiles.map((profile) => (
              <Card key={profile.id} className={profile.is_default ? 'border-blue-500 border-2' : ''}>
                <CardHeader>
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-base">{profile.name}</CardTitle>
                    {profile.is_default && <Badge variant="secondary">Default</Badge>}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Technical Weight</span>
                      <span className="font-semibold">{profile.technical_weight}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${profile.technical_weight}%` }}></div>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Psychometric Weight</span>
                      <span className="font-semibold">{profile.psychometric_weight}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${profile.psychometric_weight}%` }}></div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 pt-2 border-t">
                    <Target className="w-4 h-4 text-green-500" />
                    <span className="text-sm">Passing Score: <strong>{profile.passing_score}%</strong></span>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleEditScoringProfile(profile)}>
                      <Edit className="w-4 h-4 mr-2" /> Edit
                    </Button>
                    {!profile.is_default && (
                      <Button variant="destructive" size="sm" onClick={() => deleteScoringProfile(profile.id)}>
                        <Trash2 className="w-4 h-4 mr-2" /> Delete
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* AUDIT LOGS TAB */}
        <TabsContent value="audit" className="space-y-4">
          <div className="space-y-2">
            {auditLogs.slice(0, 50).map((log) => (
              <Card key={log.id} className="p-4">
                <div className="flex justify-between items-start">
                  <div className="space-y-1">
                    <p className="font-semibold">{log.action_type}</p>
                    <p className="text-sm text-gray-600">{log.description || `${log.entity_type} #${log.entity_id}`}</p>
                    <p className="text-xs text-gray-500">{new Date(log.timestamp).toLocaleString()}</p>
                  </div>
                  <Badge variant="outline">{log.entity_type}</Badge>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* JOB MODAL */}
      <Modal show={showJobModal} onClose={() => setShowJobModal(false)} title={editingItem ? 'Edit Job' : 'Create New Job'}>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Job Title</label>
            <Input value={jobForm.title} onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })} placeholder="e.g. Senior Software Engineer" />
          </div>
          <div>
            <label className="text-sm font-medium">Description</label>
            <textarea className="w-full border rounded-md p-2 min-h-[100px]" value={jobForm.description} onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })} placeholder="Job description..." />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Department</label>
              <Input value={jobForm.department} onChange={(e) => setJobForm({ ...jobForm, department: e.target.value })} placeholder="Engineering" />
            </div>
            <div>
              <label className="text-sm font-medium">Location</label>
              <Input value={jobForm.location} onChange={(e) => setJobForm({ ...jobForm, location: e.target.value })} placeholder="Remote" />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium">Min Experience (years)</label>
            <Input type="number" value={jobForm.min_experience} onChange={(e) => setJobForm({ ...jobForm, min_experience: parseInt(e.target.value) || 0 })} />
          </div>
          <Button onClick={handleSaveJob} className="w-full">
            <Save className="w-4 h-4 mr-2" /> {editingItem ? 'Update Job' : 'Create Job'}
          </Button>
        </div>
      </Modal>

      {/* QUESTION MODAL */}
      <Modal show={showQuestionModal} onClose={() => setShowQuestionModal(false)} title={editingItem ? 'Edit Question' : 'Add New Question'}>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Question Text</label>
            <textarea className="w-full border rounded-md p-2 min-h-[100px]" value={questionForm.question_text} onChange={(e) => setQuestionForm({ ...questionForm, question_text: e.target.value })} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Category</label>
              <Input value={questionForm.category} onChange={(e) => setQuestionForm({ ...questionForm, category: e.target.value })} placeholder="e.g. Python, JavaScript" />
            </div>
            <div>
              <label className="text-sm font-medium">Difficulty</label>
              <select className="w-full border rounded-md p-2" value={questionForm.difficulty} onChange={(e) => setQuestionForm({ ...questionForm, difficulty: e.target.value })}>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>
          <Button onClick={handleSaveQuestion} className="w-full">
            <Save className="w-4 h-4 mr-2" /> {editingItem ? 'Update Question' : 'Add Question'}
          </Button>
        </div>
      </Modal>

      {/* EMAIL TEMPLATE MODAL */}
      <Modal show={showEmailTemplateModal} onClose={() => setShowEmailTemplateModal(false)} title={editingItem ? 'Edit Email Template' : 'Create Email Template'}>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Template Name</label>
            <Input value={emailTemplateForm.template_name} onChange={(e) => setEmailTemplateForm({ ...emailTemplateForm, template_name: e.target.value })} placeholder="e.g. Rejection Email" />
          </div>
          <div>
            <label className="text-sm font-medium">Subject</label>
            <Input value={emailTemplateForm.subject} onChange={(e) => setEmailTemplateForm({ ...emailTemplateForm, subject: e.target.value })} placeholder="Email subject line" />
          </div>
          <div>
            <label className="text-sm font-medium">Body</label>
            <textarea className="w-full border rounded-md p-2 min-h-[150px]" value={emailTemplateForm.body} onChange={(e) => setEmailTemplateForm({ ...emailTemplateForm, body: e.target.value })} placeholder="Email body content..." />
          </div>
          <Button onClick={handleSaveEmailTemplate} className="w-full">
            <Save className="w-4 h-4 mr-2" /> {editingItem ? 'Update Template' : 'Create Template'}
          </Button>
        </div>
      </Modal>

      {/* ASSESSMENT TEMPLATE MODAL */}
      <Modal show={showAssessmentTemplateModal} onClose={() => setShowAssessmentTemplateModal(false)} title={editingItem ? 'Edit Assessment Template' : 'Create Assessment Template'}>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Template Name</label>
            <Input value={assessmentTemplateForm.template_name} onChange={(e) => setAssessmentTemplateForm({ ...assessmentTemplateForm, template_name: e.target.value })} placeholder="e.g. Standard Developer Test" />
          </div>
          <div>
            <label className="text-sm font-medium">Role Type</label>
            <Input value={assessmentTemplateForm.role_type} onChange={(e) => setAssessmentTemplateForm({ ...assessmentTemplateForm, role_type: e.target.value })} placeholder="e.g. Backend Developer" />
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium">MCQ Count</label>
              <Input type="number" value={assessmentTemplateForm.mcq_count} onChange={(e) => setAssessmentTemplateForm({ ...assessmentTemplateForm, mcq_count: parseInt(e.target.value) || 0 })} />
            </div>
            <div>
              <label className="text-sm font-medium">Coding Count</label>
              <Input type="number" value={assessmentTemplateForm.coding_count} onChange={(e) => setAssessmentTemplateForm({ ...assessmentTemplateForm, coding_count: parseInt(e.target.value) || 0 })} />
            </div>
            <div>
              <label className="text-sm font-medium">Psych Count</label>
              <Input type="number" value={assessmentTemplateForm.psychometric_count} onChange={(e) => setAssessmentTemplateForm({ ...assessmentTemplateForm, psychometric_count: parseInt(e.target.value) || 0 })} />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium">Time Limit (minutes)</label>
            <Input type="number" value={assessmentTemplateForm.time_limit_minutes} onChange={(e) => setAssessmentTemplateForm({ ...assessmentTemplateForm, time_limit_minutes: parseInt(e.target.value) || 60 })} />
          </div>
          <Button onClick={handleSaveAssessmentTemplate} className="w-full">
            <Save className="w-4 h-4 mr-2" /> {editingItem ? 'Update Template' : 'Create Template'}
          </Button>
        </div>
      </Modal>

      {/* SCORING PROFILE MODAL */}
      <Modal show={showScoringProfileModal} onClose={() => setShowScoringProfileModal(false)} title={editingItem ? 'Edit Scoring Profile' : 'Create Scoring Profile'}>
        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium">Profile Name</label>
            <Input value={scoringProfileForm.name} onChange={(e) => setScoringProfileForm({ ...scoringProfileForm, name: e.target.value })} placeholder="e.g. Technical Focus" />
          </div>
          <div>
            <label className="text-sm font-medium">Technical Weight (%)</label>
            <Input type="number" min="0" max="100" value={scoringProfileForm.technical_weight} onChange={(e) => {
              const val = parseInt(e.target.value) || 0;
              setScoringProfileForm({ ...scoringProfileForm, technical_weight: val, psychometric_weight: 100 - val });
            }} />
          </div>
          <div>
            <label className="text-sm font-medium">Psychometric Weight (%)</label>
            <Input type="number" min="0" max="100" value={scoringProfileForm.psychometric_weight} onChange={(e) => {
              const val = parseInt(e.target.value) || 0;
              setScoringProfileForm({ ...scoringProfileForm, psychometric_weight: val, technical_weight: 100 - val });
            }} />
          </div>
          <div>
            <label className="text-sm font-medium">Passing Score (%)</label>
            <Input type="number" min="0" max="100" value={scoringProfileForm.passing_score} onChange={(e) => setScoringProfileForm({ ...scoringProfileForm, passing_score: parseInt(e.target.value) || 70 })} />
          </div>
          <Button onClick={handleSaveScoringProfile} className="w-full">
            <Save className="w-4 h-4 mr-2" /> {editingItem ? 'Update Profile' : 'Create Profile'}
          </Button>
        </div>
      </Modal>

      {/* ANALYTICS MODAL */}
      <Modal show={showAnalyticsModal} onClose={() => setShowAnalyticsModal(false)} title="Job Analytics">
        {selectedJobAnalytics && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-gray-500">Total Candidates</p>
                  <p className="text-2xl font-bold">{selectedJobAnalytics.data?.total_candidates_for_job || 0}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-gray-500">Completed Assessments</p>
                  <p className="text-2xl font-bold">{selectedJobAnalytics.data?.completed_assessments || 0}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-gray-500">Hired</p>
                  <p className="text-2xl font-bold text-green-600">{selectedJobAnalytics.data?.hired || 0}</p>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <p className="text-sm text-gray-500">Avg. Score</p>
                  <p className="text-2xl font-bold">{selectedJobAnalytics.data?.avg_overall_score?.toFixed(1) || 'N/A'}</p>
                </CardContent>
              </Card>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AdminDashboard;
