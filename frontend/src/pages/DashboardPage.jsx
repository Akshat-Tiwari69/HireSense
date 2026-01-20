import React, { useState, useEffect } from 'react';
import { getCandidates, updateCandidateStatus } from '../services/api';

const DashboardPage = () => {
    const [candidates, setCandidates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState('All');

    useEffect(() => {
        loadCandidates();
    }, []);

    const loadCandidates = async () => {
        setLoading(true);
        try {
            const data = await getCandidates();
            setCandidates(data.candidates || []);
        } catch (error) {
            console.error("Error loading candidates", error);
        } finally {
            setLoading(false);
        }
    };

    const handleStatusUpdate = async (id, newStatus) => {
        await updateCandidateStatus(id, newStatus);
        // Optimistic update
        setCandidates(candidates.map(c =>
            c.id === id ? { ...c, status: newStatus } : c
        ));
    };

    const filteredCandidates = filter === 'All'
        ? candidates
        : candidates.filter(c => c.status === filter);

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-7xl mx-auto">
                <header className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Recruiter Dashboard</h1>
                        <p className="text-gray-500 mt-1">Manage and evaluate candidate applications</p>
                    </div>
                    <button onClick={loadCandidates} className="text-blue-600 hover:text-blue-800 font-medium">
                        Refresh Data
                    </button>
                </header>

                {/* Statistics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <p className="text-sm font-medium text-gray-500">Total Candidates</p>
                        <p className="text-2xl font-bold text-gray-900">{candidates.length}</p>
                    </div>
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <p className="text-sm font-medium text-gray-500">Shortlisted</p>
                        <p className="text-2xl font-bold text-green-600">
                            {candidates.filter(c => c.status === 'Shortlisted' || c.status === 'Accepted').length}
                        </p>
                    </div>
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <p className="text-sm font-medium text-gray-500">Pending Review</p>
                        <p className="text-2xl font-bold text-yellow-600">
                            {candidates.filter(c => c.status === 'Pending').length}
                        </p>
                    </div>
                    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
                        <p className="text-sm font-medium text-gray-500">Rejected</p>
                        <p className="text-2xl font-bold text-red-600">
                            {candidates.filter(c => c.status === 'Rejected').length}
                        </p>
                    </div>
                </div>

                {/* Main Content */}
                <div className="bg-white rounded-lg shadow">
                    {/* Filters */}
                    <div className="border-b border-gray-200 px-6 py-4 flex items-center space-x-4">
                        <span className="text-sm font-medium text-gray-700">Filter by Status:</span>
                        {['All', 'Pending', 'Shortlisted', 'Rejected'].map(status => (
                            <button
                                key={status}
                                onClick={() => setFilter(status)}
                                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${filter === status
                                        ? 'bg-blue-100 text-blue-800'
                                        : 'text-gray-500 hover:bg-gray-100'
                                    }`}
                            >
                                {status}
                            </button>
                        ))}
                    </div>

                    {/* Table */}
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Candidate</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Resume Score</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Assessment</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">AI Insight</th>
                                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {loading ? (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                                            Loading candidates...
                                        </td>
                                    </tr>
                                ) : filteredCandidates.length === 0 ? (
                                    <tr>
                                        <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                                            No candidates found.
                                        </td>
                                    </tr>
                                ) : (
                                    filteredCandidates.map((candidate) => (
                                        <tr key={candidate.id} className="hover:bg-gray-50 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center">
                                                    <div className="h-10 w-10 flex-shrink-0">
                                                        <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-600 font-bold">
                                                            {candidate.name.charAt(0)}
                                                        </div>
                                                    </div>
                                                    <div className="ml-4">
                                                        <div className="text-sm font-medium text-gray-900">{candidate.name}</div>
                                                        <div className="text-sm text-gray-500">{candidate.email}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center">
                                                    <div className="flex-1 w-24 bg-gray-200 rounded-full h-2 mr-2">
                                                        <div
                                                            className={`h-2 rounded-full ${candidate.match_score >= 70 ? 'bg-green-500' : candidate.match_score >= 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                                            style={{ width: `${candidate.match_score}%` }}
                                                        ></div>
                                                    </div>
                                                    <span className="text-sm font-bold text-gray-700">{candidate.match_score}%</span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {candidate.assessment_score ? (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                        {candidate.assessment_score}%
                                                    </span>
                                                ) : (
                                                    <span className="text-xs text-gray-500 italic">Not taken</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                                                    ${candidate.status === 'Shortlisted' ? 'bg-green-100 text-green-800' :
                                                        candidate.status === 'Rejected' ? 'bg-red-100 text-red-800' :
                                                            'bg-gray-100 text-gray-800'}`}>
                                                    {candidate.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <p className="text-xs text-gray-500 max-w-xs truncate" title={candidate.evaluation}>
                                                    {candidate.evaluation || "No insights details."}
                                                </p>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                                                {candidate.status === 'Pending' && (
                                                    <>
                                                        <button
                                                            onClick={() => handleStatusUpdate(candidate.id, 'Shortlisted')}
                                                            className="text-green-600 hover:text-green-900"
                                                        >
                                                            Approve
                                                        </button>
                                                        <span className="text-gray-300">|</span>
                                                        <button
                                                            onClick={() => handleStatusUpdate(candidate.id, 'Rejected')}
                                                            className="text-red-600 hover:text-red-900"
                                                        >
                                                            Reject
                                                        </button>
                                                    </>
                                                )}
                                                {candidate.status !== 'Pending' && (
                                                    <button
                                                        onClick={() => handleStatusUpdate(candidate.id, 'Pending')}
                                                        className="text-gray-400 hover:text-gray-600 text-xs"
                                                    >
                                                        Reset
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
