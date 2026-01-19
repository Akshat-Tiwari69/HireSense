import React, { useState } from 'react';
import { uploadResume } from '../services/api';
import { useNavigate } from 'react-router-dom';

const UploadPage = () => {
    const [file, setFile] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        phone: ''
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [successData, setSuccessData] = useState(null);
    const navigate = useNavigate();

    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (selectedFile && (selectedFile.type === 'application/pdf' || selectedFile.name.endsWith('.docx'))) {
            setFile(selectedFile);
            setError(null);
        } else {
            setFile(null);
            setError('Please select a valid PDF or DOCX file.');
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) {
            setError('Please select a resume file.');
            return;
        }
        if (!formData.name || !formData.email) {
            setError('Name and Email are required.');
            return;
        }

        setLoading(true);
        setError(null);

        const data = new FormData();
        data.append('file', file);
        data.append('name', formData.name);
        data.append('email', formData.email);
        data.append('phone', formData.phone);

        try {
            const response = await uploadResume(data);
            setSuccessData(response.data);
            // Optional: Redirect to assessment immediately or let user read results first
            // setTimeout(() => navigate(`/assessment/${response.data.candidate_id}`), 3000); 
        } catch (err) {
            setError(err.message || 'Failed to upload resume.');
        } finally {
            setLoading(false);
        }
    };

    if (successData) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
                <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
                    <div className="text-center">
                        <h2 className="mt-6 text-3xl font-extrabold text-gray-900 text-green-600">Upload Successful!</h2>
                        <p className="mt-2 text-sm text-gray-600">Resume parsed successfully.</p>
                    </div>

                    <div className="mt-8 space-y-4">
                        <div className="bg-gray-50 p-4 rounded-md">
                            <p className="text-sm font-medium text-gray-500">Match Score</p>
                            <p className="text-2xl font-bold text-blue-600">{successData.parsed_data.match_score}%</p>
                        </div>

                        <div>
                            <h3 className="text-lg font-medium text-gray-900">Skills Found</h3>
                            <div className="mt-2 flex flex-wrap gap-2">
                                {successData.parsed_data.skills.map((skill, index) => (
                                    <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                        {skill}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <div className="flex justify-center mt-6">
                            {/* Button to proceed would go here in future steps */}
                            <button
                                onClick={() => console.log("Navigate to assessment")}
                                className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                            >
                                Start Assessment (Coming Soon)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-lg shadow-md">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                        Submit Your Resume
                    </h2>
                    <p className="mt-2 text-center text-sm text-gray-600">
                        Upload your resume to check eligibility and start the assessment.
                    </p>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    <div className="rounded-md shadow-sm -space-y-px">
                        <div className="mb-4">
                            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                            <input
                                id="name"
                                name="name"
                                type="text"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="John Doe"
                                value={formData.name}
                                onChange={handleInputChange}
                            />
                        </div>
                        <div className="mb-4">
                            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                required
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="john@example.com"
                                value={formData.email}
                                onChange={handleInputChange}
                            />
                        </div>
                        <div className="mb-4">
                            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">Phone Number</label>
                            <input
                                id="phone"
                                name="phone"
                                type="tel"
                                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                                placeholder="+1 234 567 890"
                                value={formData.phone}
                                onChange={handleInputChange}
                            />
                        </div>
                        <div className="mb-4">
                            <label className="block text-sm font-medium text-gray-700 mb-1">Resume (PDF/DOCX)</label>
                            <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                                <div className="space-y-1 text-center">
                                    <svg
                                        className="mx-auto h-12 w-12 text-gray-400"
                                        stroke="currentColor"
                                        fill="none"
                                        viewBox="0 0 48 48"
                                        aria-hidden="true"
                                    >
                                        <path
                                            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                                            strokeWidth={2}
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </svg>
                                    <div className="flex text-sm text-gray-600">
                                        <label
                                            htmlFor="file-upload"
                                            className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500"
                                        >
                                            <span>Upload a file</span>
                                            <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".pdf,.docx" />
                                        </label>
                                        <p className="pl-1">or drag and drop</p>
                                    </div>
                                    <p className="text-xs text-gray-500">PDF or DOCX up to 10MB</p>
                                </div>
                            </div>
                            {file && <p className="mt-2 text-sm text-gray-600 text-center">Selected: {file.name}</p>}
                        </div>
                    </div>

                    {error && (
                        <div className="text-red-600 text-sm text-center bg-red-50 p-2 rounded">
                            {error}
                        </div>
                    )}

                    <div>
                        <button
                            type="submit"
                            disabled={loading}
                            className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white ${loading ? 'bg-indigo-400' : 'bg-indigo-600 hover:bg-indigo-700'} focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500`}
                        >
                            {loading ? 'Uploading...' : 'Submit application'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default UploadPage;
