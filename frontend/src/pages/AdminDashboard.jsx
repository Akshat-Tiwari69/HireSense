  import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, Plus, Search, Edit, Trash2, Eye, FileText, Settings, BarChart3 } from 'lucide-react';
import { api } from '@/services/api';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [jobs, setJobs] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [emailTemplates, setEmailTemplates] = useState([]);
  const [assessmentTemplates, setAssessmentTemplates] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [selectedJob, setSelectedJob] = useState(null);
  const [showJobModal, setShowJobModal] = useState(false);

  useEffect(() => {
    if (activeTab === 'jobs') fetchJobs();
    if (activeTab === 'questions') fetchQuestions();
    if (activeTab === 'email-templates') fetchEmailTemplates();
    if (activeTab === 'assessment-templates') fetchAssessmentTemplates();
    if (activeTab === 'audit') fetchAuditLogs();
  }, [activeTab]);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/jobs', { params: { search } });
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
    setLoading(false);
  };

  const fetchQuestions = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/question-bank');
      setQuestions(response.data);
    } catch (error) {
      console.error('Error fetching questions:', error);
    }
    setLoading(false);
  };

  const fetchEmailTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/email-templates');
      setEmailTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
    setLoading(false);
  };

  const fetchAssessmentTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/assessment-templates');
      setAssessmentTemplates(response.data);
    } catch (error) {
      console.error('Error fetching assessment templates:', error);
    }
    setLoading(false);
  };

  const fetchAuditLogs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/audit-logs', { params: { limit: 100 } });
      setAuditLogs(response.data);
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
    setLoading(false);
  };

  const deleteJob = async (jobId) => {
    if (window.confirm('Archive this job?')) {
      try {
        await api.delete(`/admin/jobs/${jobId}`);
        setJobs(jobs.filter(j => j.id !== jobId));
      } catch (error) {
        console.error('Error deleting job:', error);
      }
    }
  };

  const deleteQuestion = async (questionId) => {
    try {
      await api.delete(`/admin/question-bank/${questionId}`);
      setQuestions(questions.filter(q => q.id !== questionId));
    } catch (error) {
      console.error('Error deleting question:', error);
    }
  };

  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Admin Dashboard</h1>
        <Badge variant="outline">Full System Control</Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="jobs">Jobs</TabsTrigger>
          <TabsTrigger value="questions">Questions</TabsTrigger>
          <TabsTrigger value="email-templates">Email Templates</TabsTrigger>
          <TabsTrigger value="assessment-templates">Assessment Templates</TabsTrigger>
          <TabsTrigger value="scoringprofile">Scoring Profiles</TabsTrigger>
          <TabsTrigger value="audit">Audit Logs</TabsTrigger>
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
            <Button onClick={() => setShowJobModal(true)}>
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
                      {job.required_skills?.map((skill) => (
                        <Badge key={skill} variant="secondary">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="w-4 h-4 mr-2" /> View Analytics
                    </Button>
                    <Button variant="outline" size="sm">
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
            <Button>
              <Plus className="w-4 h-4 mr-2" /> Add Question
            </Button>
          </div>

          <div className="space-y-3">
            {questions.map((q) => (
              <Card key={q.id}>
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-base">{q.question_text.substring(0, 80)}...</CardTitle>
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
                    <Button variant="outline" size="sm">Edit</Button>
                    <Button variant="destructive" size="sm" onClick={() => deleteQuestion(q.id)}>Delete</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* EMAIL TEMPLATES TAB */}
        <TabsContent value="email-templates" className="space-y-4">
          <Button>
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
                    <Button variant="outline" size="sm">Edit</Button>
                    <Button variant="destructive" size="sm">Delete</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        {/* ASSESSMENT TEMPLATES TAB */}
        <TabsContent value="assessment-templates" className="space-y-4">
          <Button>
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
                    <Button variant="outline" size="sm">Edit</Button>
                    <Button variant="destructive" size="sm">Delete</Button>
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
    </div>
  );
};

export default AdminDashboard;
