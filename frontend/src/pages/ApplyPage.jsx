import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Upload, CheckCircle, Loader2, FileText } from 'lucide-react';
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

  const validateForm = () => {
    const newErrors = {};
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

      const res = await api.post('/api/resume/upload', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      // Store candidate info from response
      const name = res.data?.candidate?.name || 'Candidate';
      const email = res.data?.candidate?.email || '';
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
          <p className="text-base sm:text-lg text-slate-600">Submit your resume and let AI help you stand out</p>
        </div>

        <Card className="shadow-2xl border-none">
          <CardHeader>
            <CardTitle className="text-xl sm:text-2xl">Upload Your Resume</CardTitle>
            <CardDescription className="text-sm sm:text-base">
              We auto-detect your name, email, and phone from the resume. No manual entry needed.
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
