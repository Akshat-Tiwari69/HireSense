import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Upload, CheckCircle, Loader2, FileText } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';
import { uploadResume } from '../services/api';

const UploadPage = () => {
    const navigate = useNavigate();
    const { toast } = useToast();
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        phone: ''
    });
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [errors, setErrors] = useState({});
    const [dragActive, setDragActive] = useState(false);

    const validateForm = () => {
        const newErrors = {};
        if (!formData.name.trim()) newErrors.name = 'Name is required';
        if (!formData.email.trim()) {
            newErrors.email = 'Email is required';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = 'Invalid email format';
        }
        if (!formData.phone.trim()) newErrors.phone = 'Phone is required';
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
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!validateForm()) return;

        setLoading(true);

        try {
            const submissionData = new FormData();
            submissionData.append('file', file);
            submissionData.append('name', formData.name);
            submissionData.append('email', formData.email);
            submissionData.append('phone', formData.phone);

            const response = await uploadResume(submissionData);

            setLoading(false);
            setSubmitted(true);
            toast({
                title: 'Application submitted!',
                description: 'Your resume is being analyzed by our AI.',
            });

            // Store candidate data for potential immediate assessment start (optional integration)
            if (response.data && response.data.candidate_id) {
                localStorage.setItem('currentCandidateId', response.data.candidate_id);
            }

        } catch (error) {
            console.error("Upload error:", error);
            setLoading(false);
            toast({
                variant: 'destructive',
                title: 'Submission failed',
                description: error.message || 'Something went wrong. Please try again.',
            });
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
                        <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 mb-4">Application Received!</h2>
                        <p className="text-slate-600 mb-8 text-base sm:text-lg">
                            Your resume is securely analyzed by AI. You'll hear from us soon.
                        </p>
                        <div className="bg-indigo-50 p-4 rounded-lg mb-6">
                            <p className="text-sm text-indigo-800">
                                <strong>Next Steps:</strong> Our AI is evaluating your application. If selected, you'll receive an email with assessment details.
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
                        <CardTitle className="text-xl sm:text-2xl">Your Information</CardTitle>
                        <CardDescription className="text-sm sm:text-base">
                            Your resume is securely analyzed by AI. Scores are never shown to candidates.
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-6">
                            <div className="space-y-2">
                                <Label htmlFor="name">Full Name *</Label>
                                <Input
                                    id="name"
                                    placeholder="John Doe"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className={errors.name ? 'border-red-500' : ''}
                                />
                                {errors.name && <p className="text-sm text-red-600">{errors.name}</p>}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="email">Email Address *</Label>
                                <Input
                                    id="email"
                                    type="email"
                                    placeholder="john.doe@email.com"
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    className={errors.email ? 'border-red-500' : ''}
                                />
                                {errors.email && <p className="text-sm text-red-600">{errors.email}</p>}
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="phone">Phone Number *</Label>
                                <Input
                                    id="phone"
                                    placeholder="+1-555-0123"
                                    value={formData.phone}
                                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                    className={errors.phone ? 'border-red-500' : ''}
                                />
                                {errors.phone && <p className="text-sm text-red-600">{errors.phone}</p>}
                            </div>

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

                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                <p className="text-sm text-blue-800">
                                    <strong>Privacy Notice:</strong> Your information is encrypted and stored securely. We never share your data with third parties.
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

export default UploadPage;
