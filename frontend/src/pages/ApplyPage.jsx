import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Upload, CheckCircle, Loader2, FileText, Briefcase, MapPin, Clock, AlertCircle } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { api } from '../services/api';

const ApplyPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [candidateInfo, setCandidateInfo] = useState({ name: '', email: '' });
  const [errors, setErrors] = useState({});
  const [uploadError, setUploadError] = useState('');
  const [dragActive, setDragActive] = useState(false);

  // Job postings state
  const [jobPostings, setJobPostings] = useState([]);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState('');


  useEffect(() => {
    fetchActiveJobs();
  }, []);

  const fetchActiveJobs = async () => {
    try {
      const res = await api.get('/api/jobs/postings?status=active');
      setJobPostings(res.data.data || []);
    } catch (err) {
      console.warn('Could not load job postings:', err);
    } finally {
      setLoadingJobs(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!selectedJobId) newErrors.job = 'Please select a job to apply for';
    if (!file) newErrors.file = 'Resume is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (selectedFile) => {
    if (selectedFile) {
      const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!validTypes.includes(selectedFile.type)) {
        toast({
          variant: 'destructive',
          title: 'Invalid file type',
          description: 'Please upload a PDF or DOCX file',
        });
        return;
      }
      if (selectedFile.size > 5 * 1024 * 1024) {
        toast({
          variant: 'destructive',
          title: 'File too large',
          description: 'File size must be less than 5MB',
        });
        return;
      }
      setFile(selectedFile);
      setErrors(prev => ({ ...prev, file: '' }));
      setUploadError(''); // Clear any previous upload errors
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setUploadError('');
    try {
      const form = new FormData();
      form.append('file', file);
      form.append('job_id', selectedJobId);

      const res = await api.post('/api/resume/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // Store candidate info from response
      const name = res.data?.candidate?.name || res.data?.data?.candidate?.name || 'Candidate';
      const email = res.data?.candidate?.email || res.data?.data?.candidate?.email || '';
      setCandidateInfo({ name, email });

      setSubmitted(true);
      toast({
        title: 'Application submitted!',
        description: 'Your resume is being analyzed by our AI.',
      });
      console.log('Upload response', res.data);
    } catch (err) {
      const message = err?.response?.data?.message || 'Upload failed';
      setUploadError(message);
      toast({
        variant: 'destructive',
        title: 'Upload failed',
        description: message,
      });
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 flex items-center justify-center p-4 sm:p-6">
        <Card className="w-full max-w-md shadow-2xl border-none text-center">
          <CardContent className="pt-12 pb-12">
            <div className="flex justify-center mb-6">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center">
                <CheckCircle className="w-12 h-12 text-emerald-600" />
              </div>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-4">
              Thank You{candidateInfo.name ? `, ${candidateInfo.name}` : ''}!
            </h2>
            <p className="text-slate-600 mb-4 text-base sm:text-lg">
              Your application has been successfully submitted.
            </p>
            {candidateInfo.email && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <p className="text-sm text-blue-900">
                  <strong>Contact Email:</strong> {candidateInfo.email}
                </p>
                <p className="text-xs text-blue-700 mt-2">
                  You will be contacted on this email if selected for the next round.
                </p>
              </div>
            )}
            <div className="bg-indigo-50 p-4 rounded-lg mb-6">
              <p className="text-sm text-indigo-800">
                <strong>Next Steps:</strong> Our AI is evaluating your application. If selected, you'll receive an email with assessment details within 3-5 business days.
              </p>
            </div>

            <Button
              onClick={() => navigate('/')}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              Back to Home
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-8 sm:py-12 px-4 sm:px-6">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6 sm:mb-8">
          <div className="flex items-center justify-center mb-4">
            <Logo size="default" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-3">Apply for Position</h1>
          <p className="text-base sm:text-lg text-slate-600">Select a role and upload your resume — AI will score you against that specific job</p>
        </div>

        {/* Step 1: Select Job */}
        <Card className={`shadow-lg border-2 mb-6 transition-colors ${selectedJobId ? 'border-emerald-300 bg-emerald-50/30' : errors.job ? 'border-red-300' : 'border-slate-200'}`}>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <div className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white text-sm font-bold">1</div>
              <Briefcase className="w-5 h-5 text-indigo-600" />
              Select the Position You're Applying For
            </CardTitle>
            <CardDescription>Your resume will be evaluated specifically against this role's requirements</CardDescription>
          </CardHeader>
          <CardContent>
            {loadingJobs ? (
              <div className="flex items-center gap-2 text-slate-500 py-4 justify-center">
                <Loader2 className="w-4 h-4 animate-spin" />
                Loading open positions...
              </div>
            ) : jobPostings.length === 0 ? (
              <div className="text-center py-6 text-slate-500">
                <AlertCircle className="w-8 h-8 mx-auto mb-2 text-amber-500" />
                <p className="font-medium">No open positions at the moment</p>
                <p className="text-sm mt-1">Check back later or upload your resume for general consideration</p>
              </div>
            ) : (
              <div className="space-y-3">
                {jobPostings.map((job) => {
                  const isSelected = selectedJobId === String(job.id);
                  const skills = job.required_skills_list || (job.required_skills ? job.required_skills.split(',').map(s => s.trim()).filter(Boolean) : []);
                  return (
                    <div
                      key={job.id}
                      onClick={() => { setSelectedJobId(String(job.id)); setErrors(prev => ({ ...prev, job: '' })); }}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 ${
                        isSelected
                          ? 'border-indigo-500 bg-indigo-50 shadow-md ring-2 ring-indigo-200'
                          : 'border-slate-200 bg-white hover:border-indigo-300 hover:shadow-sm'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                              isSelected ? 'border-indigo-600 bg-indigo-600' : 'border-slate-300'
                            }`}>
                              {isSelected && <CheckCircle className="w-3 h-3 text-white" />}
                            </div>
                            <h4 className="font-semibold text-slate-900">{job.title}</h4>
                          </div>
                          <div className="flex items-center gap-3 mt-1 ml-6 text-xs text-slate-500">
                            {job.department && <span>{job.department}</span>}
                            {job.location && <span className="flex items-center gap-1"><MapPin className="w-3 h-3" />{job.location}</span>}
                            {job.experience_level && (
                              <Badge className="bg-indigo-100 text-indigo-800 text-xs">
                                {job.experience_level.charAt(0).toUpperCase() + job.experience_level.slice(1)}
                              </Badge>
                            )}
                            {job.employment_type && (
                              <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{job.employment_type}</span>
                            )}
                          </div>
                        </div>
                      </div>
                      {skills.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2 ml-6">
                          {skills.slice(0, 6).map((skill, i) => (
                            <Badge key={i} className="bg-blue-100 text-blue-800 text-xs">{skill}</Badge>
                          ))}
                          {skills.length > 6 && (
                            <Badge className="bg-slate-100 text-slate-600 text-xs">+{skills.length - 6}</Badge>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
            {errors.job && <p className="text-sm text-red-600 mt-2 flex items-center gap-1"><AlertCircle className="w-3 h-3" />{errors.job}</p>}
          </CardContent>
        </Card>

        <Card className="shadow-2xl border-none">
          <CardHeader>
            <CardTitle className="text-xl sm:text-2xl flex items-center gap-2">
              <div className="flex items-center justify-center w-7 h-7 rounded-full bg-indigo-600 text-white text-sm font-bold">2</div>
              Upload Your Resume
            </CardTitle>
            <CardDescription className="text-sm sm:text-base">
              {selectedJobId && jobPostings.length > 0
                ? `AI will score your resume against: ${jobPostings.find(j => String(j.id) === selectedJobId)?.title || 'Selected Position'}`
                : 'We auto-detect your name, email, and phone from the resume. No manual entry needed.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label>Resume Upload *</Label>
                <div
                  className={`border-2 border-dashed rounded-lg p-6 sm:p-8 text-center transition-all duration-300 ${dragActive
                    ? 'border-indigo-500 bg-indigo-50'
                    : errors.file
                      ? 'border-red-500'
                      : 'border-slate-300 hover:border-indigo-400'
                    }`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                >
                  {file ? (
                    <div className="space-y-3">
                      <FileText className="w-10 h-10 sm:w-12 sm:h-12 text-indigo-600 mx-auto" />
                      <p className="font-medium text-slate-900 text-sm sm:text-base">{file.name}</p>
                      <p className="text-xs sm:text-sm text-slate-600">{(file.size / 1024).toFixed(2)} KB</p>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => setFile(null)}
                      >
                        Remove
                      </Button>
                    </div>
                  ) : (
                    <>
                      <Upload className="w-10 h-10 sm:w-12 sm:h-12 text-slate-400 mx-auto mb-4" />
                      <p className="text-slate-700 font-medium mb-2 text-sm sm:text-base">
                        Drop your resume here or click to browse
                      </p>
                      <p className="text-xs sm:text-sm text-slate-500 mb-4">PDF or DOCX, max 5MB</p>
                      <Input
                        type="file"
                        className="hidden"
                        id="file-upload"
                        accept=".pdf,.doc,.docx"
                        onChange={(e) => handleFileChange(e.target.files[0])}
                      />
                      <Label
                        htmlFor="file-upload"
                        className="cursor-pointer inline-block px-4 sm:px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm sm:text-base"
                      >
                        Choose File
                      </Label>
                    </>
                  )}
                </div>
                {errors.file && <p className="text-sm text-red-600">{errors.file}</p>}
              </div>

              {uploadError && (
                <div className="bg-red-50 border border-red-300 rounded-lg p-4 mb-4">
                  <p className="text-sm text-red-800 font-medium">
                    <strong>Upload Failed:</strong> {uploadError}
                  </p>
                  <p className="text-xs text-red-600 mt-1">
                    Please ensure your resume contains a valid email address or try a different file format.
                  </p>
                </div>
              )}

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  <strong>Privacy Notice:</strong> We extract your contact details directly from the resume. Your data is encrypted and never shared with third parties.
                </p>
              </div>

              <Button
                type="submit"
                className="w-full bg-indigo-600 hover:bg-indigo-700 h-11 sm:h-12 text-base font-medium transition-all duration-300 hover:scale-[1.02]"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Submitting Application...
                  </>
                ) : (
                  'Submit Application'
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <Button
                variant="link"
                onClick={() => navigate('/')}
                className="text-slate-600 hover:text-indigo-600"
              >
                ← Back to home
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ApplyPage;
