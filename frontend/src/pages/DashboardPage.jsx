import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { LogOut, Search, Filter, Calendar, CheckCircle, XCircle, Clock, ThumbsUp, ThumbsDown, Users, BarChart3 } from 'lucide-react';
import { mockCandidates } from '../data/mock';
import { useToast } from '../hooks/use-toast';
import Logo from '../components/Logo';

const DashboardPage = () => {
    const navigate = useNavigate();
    const { toast } = useToast();
    const [candidates, setCandidates] = useState(mockCandidates);
    const [filteredCandidates, setFilteredCandidates] = useState(mockCandidates);
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');
    const [scoreFilter, setScoreFilter] = useState('all');
    const [selectedCandidate, setSelectedCandidate] = useState(null);
    const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
    const [scheduleDate, setScheduleDate] = useState('');
    const [scheduleTime, setScheduleTime] = useState('');

    useEffect(() => {
        // Check auth
        const token = localStorage.getItem('authToken');
        if (!token) {
            navigate('/login');
        }
    }, [navigate]);

    useEffect(() => {
        let filtered = candidates;

        // Search filter
        if (searchTerm) {
            filtered = filtered.filter(c =>
                c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                c.email.toLowerCase().includes(searchTerm.toLowerCase())
            );
        }

        // Status filter
        if (statusFilter !== 'all') {
            filtered = filtered.filter(c => c.status === statusFilter);
        }

        // Score filter
        if (scoreFilter !== 'all') {
            if (scoreFilter === 'high') {
                filtered = filtered.filter(c => c.aiMatchScore >= 85);
            } else if (scoreFilter === 'medium') {
                filtered = filtered.filter(c => c.aiMatchScore >= 70 && c.aiMatchScore < 85);
            } else if (scoreFilter === 'low') {
                filtered = filtered.filter(c => c.aiMatchScore < 70);
            }
        }

        setFilteredCandidates(filtered);
    }, [searchTerm, statusFilter, scoreFilter, candidates]);

    const handleLogout = () => {
        localStorage.removeItem('authToken');
        localStorage.removeItem('userEmail');
        navigate('/login');
    };

    const handleReject = (candidateId) => {
        setCandidates(prev => prev.map(c =>
            c.id === candidateId ? { ...c, status: 'Rejected' } : c
        ));
        toast({
            title: 'Candidate rejected',
            description: 'Rejection email will be sent automatically',
        });
    };

    const handleSchedule = () => {
        if (!scheduleDate || !scheduleTime) {
            toast({
                variant: 'destructive',
                title: 'Missing information',
                description: 'Please select both date and time',
            });
            return;
        }

        const scheduledDateTime = `${scheduleDate}T${scheduleTime}:00`;
        setCandidates(prev => prev.map(c =>
            c.id === selectedCandidate.id
                ? { ...c, status: 'Scheduled', assessmentScheduled: scheduledDateTime }
                : c
        ));
        toast({
            title: 'Assessment scheduled',
            description: `Candidate will receive email with assessment link for ${scheduleDate} at ${scheduleTime}`,
        });
        setScheduleModalOpen(false);
        setScheduleDate('');
        setScheduleTime('');
        setSelectedCandidate(null);
    };

    const getScoreBadgeColor = (score) => {
        if (score >= 85) return 'bg-emerald-100 text-emerald-800 border-emerald-300';
        if (score >= 70) return 'bg-amber-100 text-amber-800 border-amber-300';
        return 'bg-red-100 text-red-800 border-red-300';
    };

    const getStatusBadge = (status) => {
        const styles = {
            'Applied': 'bg-blue-100 text-blue-800 border-blue-300',
            'Scheduled': 'bg-purple-100 text-purple-800 border-purple-300',
            'Completed': 'bg-emerald-100 text-emerald-800 border-emerald-300',
            'Rejected': 'bg-red-100 text-red-800 border-red-300'
        };
        return styles[status] || '';
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
            {/* Header */}
            <header className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4 flex justify-between items-center">
                    <Logo size="default" />
                    <Button
                        variant="ghost"
                        onClick={handleLogout}
                        className="text-slate-700 hover:text-red-600 transition-colors text-sm sm:text-base"
                    >
                        <LogOut className="mr-2 w-4 h-4" />
                        <span className="hidden sm:inline">Logout</span>
                    </Button>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
                {/* Stats Cards */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mb-6 sm:mb-8">
                    <Card className="border-none shadow-md">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-slate-600 mb-1">Total Candidates</p>
                                    <p className="text-3xl font-bold text-slate-900">{candidates.length}</p>
                                </div>
                                <Users className="w-10 h-10 text-indigo-600" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-none shadow-md">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-slate-600 mb-1">High Match</p>
                                    <p className="text-3xl font-bold text-emerald-600">
                                        {candidates.filter(c => c.aiMatchScore >= 85).length}
                                    </p>
                                </div>
                                <CheckCircle className="w-10 h-10 text-emerald-600" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-none shadow-md">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-slate-600 mb-1">Scheduled</p>
                                    <p className="text-3xl font-bold text-purple-600">
                                        {candidates.filter(c => c.status === 'Scheduled').length}
                                    </p>
                                </div>
                                <Clock className="w-10 h-10 text-purple-600" />
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="border-none shadow-md">
                        <CardContent className="pt-6">
                            <div className="flex items-center justify-between">
                                <div>
                                    <p className="text-sm text-slate-600 mb-1">Completed</p>
                                    <p className="text-3xl font-bold text-blue-600">
                                        {candidates.filter(c => c.status === 'Completed').length}
                                    </p>
                                </div>
                                <CheckCircle className="w-10 h-10 text-blue-600" />
                            </div>
                        </CardContent>
                    </Card>
                </div>

                {/* Filters */}
                <Card className="mb-6 border-none shadow-md">
                    <CardContent className="pt-6">
                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                                <Input
                                    placeholder="Search by name or email..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="pl-10"
                                />
                            </div>
                            <Select value={statusFilter} onValueChange={setStatusFilter}>
                                <SelectTrigger className="w-full md:w-48">
                                    <Filter className="w-4 h-4 mr-2" />
                                    <SelectValue placeholder="Status" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Status</SelectItem>
                                    <SelectItem value="Applied">Applied</SelectItem>
                                    <SelectItem value="Scheduled">Scheduled</SelectItem>
                                    <SelectItem value="Completed">Completed</SelectItem>
                                    <SelectItem value="Rejected">Rejected</SelectItem>
                                </SelectContent>
                            </Select>
                            <Select value={scoreFilter} onValueChange={setScoreFilter}>
                                <SelectTrigger className="w-full md:w-48">
                                    <SelectValue placeholder="Score Range" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="all">All Scores</SelectItem>
                                    <SelectItem value="high">High (85+)</SelectItem>
                                    <SelectItem value="medium">Medium (70-84)</SelectItem>
                                    <SelectItem value="low">Low (&lt;70)</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </CardContent>
                </Card>

                {/* Candidates Table */}
                <Card className="border-none shadow-md">
                    <CardHeader>
                        <CardTitle className="text-2xl">Candidates</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="rounded-lg border overflow-hidden">
                            <Table>
                                <TableHeader>
                                    <TableRow className="bg-slate-50">
                                        <TableHead className="font-semibold">Name</TableHead>
                                        <TableHead className="font-semibold">Email</TableHead>
                                        <TableHead className="font-semibold">AI Score</TableHead>
                                        <TableHead className="font-semibold">Status</TableHead>
                                        <TableHead className="font-semibold">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {filteredCandidates.length === 0 ? (
                                        <TableRow>
                                            <TableCell colSpan={5} className="text-center py-8 text-slate-500">
                                                No candidates found
                                            </TableCell>
                                        </TableRow>
                                    ) : (
                                        filteredCandidates.map((candidate) => (
                                            <TableRow key={candidate.id} className="hover:bg-slate-50 transition-colors">
                                                <TableCell className="font-medium">{candidate.name}</TableCell>
                                                <TableCell className="text-slate-600">{candidate.email}</TableCell>
                                                <TableCell>
                                                    <Badge className={`${getScoreBadgeColor(candidate.aiMatchScore)} border font-semibold`}>
                                                        {candidate.aiMatchScore}%
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <Badge className={`${getStatusBadge(candidate.status)} border`}>
                                                        {candidate.status}
                                                    </Badge>
                                                </TableCell>
                                                <TableCell>
                                                    <div className="flex gap-2">
                                                        <Dialog>
                                                            <DialogTrigger asChild>
                                                                <Button size="sm" variant="outline" className="hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-300">
                                                                    View Details
                                                                </Button>
                                                            </DialogTrigger>
                                                            <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                                                                <DialogHeader>
                                                                    <DialogTitle className="text-2xl">{candidate.name}</DialogTitle>
                                                                    <DialogDescription>{candidate.email} | {candidate.phone}</DialogDescription>
                                                                </DialogHeader>
                                                                <div className="space-y-6 mt-4">
                                                                    <div>
                                                                        <h3 className="font-semibold text-lg mb-2 flex items-center gap-2">
                                                                            <BarChart3 className="w-5 h-5 text-indigo-600" />
                                                                            AI Match Score
                                                                        </h3>
                                                                        <div className="bg-slate-50 p-4 rounded-lg">
                                                                            <div className="text-4xl font-bold text-indigo-600 mb-2">
                                                                                {candidate.aiMatchScore}%
                                                                            </div>
                                                                            <div className="w-full bg-slate-200 rounded-full h-3">
                                                                                <div
                                                                                    className="bg-indigo-600 h-3 rounded-full transition-all duration-500"
                                                                                    style={{ width: `${candidate.aiMatchScore}%` }}
                                                                                />
                                                                            </div>
                                                                        </div>
                                                                    </div>

                                                                    <div>
                                                                        <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                                                                            <ThumbsUp className="w-5 h-5 text-emerald-600" />
                                                                            AI-Generated Strengths
                                                                        </h3>
                                                                        <ul className="space-y-2">
                                                                            {candidate.aiPros.map((pro, idx) => (
                                                                                <li key={idx} className="flex items-start gap-2 bg-emerald-50 p-3 rounded-lg">
                                                                                    <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                                                                                    <span className="text-slate-700">{pro}</span>
                                                                                </li>
                                                                            ))}
                                                                        </ul>
                                                                    </div>

                                                                    <div>
                                                                        <h3 className="font-semibold text-lg mb-3 flex items-center gap-2">
                                                                            <ThumbsDown className="w-5 h-5 text-amber-600" />
                                                                            Areas for Consideration
                                                                        </h3>
                                                                        <ul className="space-y-2">
                                                                            {candidate.aiCons.map((con, idx) => (
                                                                                <li key={idx} className="flex items-start gap-2 bg-amber-50 p-3 rounded-lg">
                                                                                    <XCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                                                                                    <span className="text-slate-700">{con}</span>
                                                                                </li>
                                                                            ))}
                                                                        </ul>
                                                                    </div>

                                                                    {candidate.status === 'Completed' && (
                                                                        <div className="bg-indigo-50 border border-indigo-200 p-4 rounded-lg">
                                                                            <h3 className="font-semibold text-lg mb-2">Assessment Results</h3>
                                                                            <p className="text-slate-700">Score: <span className="font-bold text-indigo-600">{candidate.assessmentScore}%</span></p>
                                                                        </div>
                                                                    )}
                                                                </div>
                                                            </DialogContent>
                                                        </Dialog>

                                                        {candidate.status === 'Applied' && (
                                                            <>
                                                                <Button
                                                                    size="sm"
                                                                    onClick={() => {
                                                                        setSelectedCandidate(candidate);
                                                                        setScheduleModalOpen(true);
                                                                    }}
                                                                    className="bg-emerald-600 hover:bg-emerald-700 text-white"
                                                                >
                                                                    Schedule
                                                                </Button>
                                                                <Button
                                                                    size="sm"
                                                                    variant="destructive"
                                                                    onClick={() => handleReject(candidate.id)}
                                                                >
                                                                    Reject
                                                                </Button>
                                                            </>
                                                        )}
                                                    </div>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>

                {/* Schedule Modal */}
                <Dialog open={scheduleModalOpen} onOpenChange={setScheduleModalOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Schedule Assessment</DialogTitle>
                            <DialogDescription>
                                Choose date and time for {selectedCandidate?.name}'s assessment
                            </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label htmlFor="date">Date</Label>
                                <Input
                                    id="date"
                                    type="date"
                                    value={scheduleDate}
                                    onChange={(e) => setScheduleDate(e.target.value)}
                                    min={new Date().toISOString().split('T')[0]}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="time">Time</Label>
                                <Input
                                    id="time"
                                    type="time"
                                    value={scheduleTime}
                                    onChange={(e) => setScheduleTime(e.target.value)}
                                />
                            </div>
                        </div>
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setScheduleModalOpen(false)}>
                                Cancel
                            </Button>
                            <Button onClick={handleSchedule} className="bg-indigo-600 hover:bg-indigo-700">
                                <Calendar className="mr-2 w-4 h-4" />
                                Confirm Schedule
                            </Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
            </div>
        </div>
    );
};

export default DashboardPage;
