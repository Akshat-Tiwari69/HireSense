import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import {
  Briefcase, MapPin, Clock, Search, ArrowRight, Building2, GraduationCap, IndianRupee, X
} from 'lucide-react';
import Logo from '../components/Logo';
import { api } from '../services/api';

const JobListingsPage = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState('all');
  const [levelFilter, setLevelFilter] = useState('all');
  const [selectedJob, setSelectedJob] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get('/api/jobs/postings?status=active').catch(() => ({ data: { data: [] } })),
      api.get('/api/jobs/sectors').catch(() => ({ data: { data: [] } })),
    ]).then(([jobsRes, sectorsRes]) => {
      setJobs(jobsRes.data.data || []);
      setSectors(sectorsRes.data.data || []);
    }).finally(() => setLoading(false));
  }, []);

  const filteredJobs = jobs.filter(job => {
    const matchesSearch =
      job.title?.toLowerCase().includes(search.toLowerCase()) ||
      job.department?.toLowerCase().includes(search.toLowerCase()) ||
      (job.required_skills || '').toLowerCase().includes(search.toLowerCase());
    const matchesSector = sectorFilter === 'all' || String(job.sector_id) === sectorFilter;
    const matchesLevel = levelFilter === 'all' || job.experience_level === levelFilter;
    return matchesSearch && matchesSector && matchesLevel;
  });

  const levelColors = {
    junior: 'bg-green-100 text-green-800',
    mid: 'bg-blue-100 text-blue-800',
    senior: 'bg-purple-100 text-purple-800',
    lead: 'bg-red-100 text-red-800',
    principal: 'bg-amber-100 text-amber-800',
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 py-8 px-4 sm:px-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Logo size="default" />
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-2">Open Positions</h1>
          <p className="text-lg text-slate-600 mb-6">
            Find the role that fits your skills. Our AI matches your resume to the best position.
          </p>
          <Button onClick={() => navigate('/apply')} className="bg-indigo-600 hover:bg-indigo-700">
            Apply Now <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
          <div className="md:col-span-2 flex items-center gap-2 bg-white rounded-lg p-3 border border-slate-200 shadow-sm">
            <Search className="w-4 h-4 text-slate-500" />
            <Input
              placeholder="Search jobs by title, skills, or department..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-transparent border-0 focus:ring-0 text-slate-900"
            />
          </div>
          <Select value={sectorFilter} onValueChange={setSectorFilter}>
            <SelectTrigger className="bg-white border-slate-200 shadow-sm">
              <Building2 className="w-4 h-4 mr-2 text-slate-500" />
              <SelectValue placeholder="All Sectors" />
            </SelectTrigger>
            <SelectContent className="bg-white">
              <SelectItem value="all">All Sectors</SelectItem>
              {sectors.map(s => (
                <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={levelFilter} onValueChange={setLevelFilter}>
            <SelectTrigger className="bg-white border-slate-200 shadow-sm">
              <GraduationCap className="w-4 h-4 mr-2 text-slate-500" />
              <SelectValue placeholder="All Levels" />
            </SelectTrigger>
            <SelectContent className="bg-white">
              <SelectItem value="all">All Levels</SelectItem>
              <SelectItem value="junior">Junior</SelectItem>
              <SelectItem value="mid">Mid-Level</SelectItem>
              <SelectItem value="senior">Senior</SelectItem>
              <SelectItem value="lead">Lead</SelectItem>
              <SelectItem value="principal">Principal</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Results count */}
        <p className="text-sm text-slate-500 mb-4">
          {loading ? 'Loading...' : `${filteredJobs.length} position${filteredJobs.length !== 1 ? 's' : ''} found`}
        </p>

        {/* Job Cards */}
        <div className="space-y-4">
          {filteredJobs.map((job) => (
            <div key={job.id} className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 border-l-4 border-indigo-500 overflow-hidden cursor-pointer" onClick={() => setSelectedJob(job)}>
              <div className="p-5 sm:p-6">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    {/* Title row */}
                    <div className="flex flex-wrap items-center gap-2 mb-3">
                      <h3 className="text-lg sm:text-xl font-bold text-slate-900 leading-tight">{job.title}</h3>
                      <Badge className={`${levelColors[job.experience_level] || 'bg-slate-100 text-slate-800'} text-xs px-2.5 py-0.5`}>
                        {(job.experience_level || 'mid').charAt(0).toUpperCase() + (job.experience_level || 'mid').slice(1)}
                      </Badge>
                      {job.employment_type && (
                        <Badge variant="outline" className="border-slate-300 text-slate-600 text-xs">
                          {job.employment_type.replace('-', ' ')}
                        </Badge>
                      )}
                    </div>

                    {/* Meta row */}
                    <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-sm text-slate-500 mb-4">
                      {job.sector_name && (
                        <span className="flex items-center gap-1.5">
                          <Building2 className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
                          <span>{job.sector_name}</span>
                        </span>
                      )}
                      {job.department && (
                        <span className="flex items-center gap-1.5">
                          <Briefcase className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
                          <span>{job.department}</span>
                        </span>
                      )}
                      {job.location && (
                        <span className="flex items-center gap-1.5">
                          <MapPin className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
                          <span>{job.location}</span>
                        </span>
                      )}
                      <span className="flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 flex-shrink-0 text-slate-400" />
                        <span>{job.min_experience || 0}{job.max_experience ? `–${job.max_experience}` : '+'} years</span>
                      </span>
                      {job.salary_range && (
                        <span className="flex items-center gap-1 font-semibold text-emerald-700">
                          <IndianRupee className="w-3.5 h-3.5 flex-shrink-0" />
                          <span>{job.salary_range}</span>
                        </span>
                      )}
                    </div>

                    {/* Description */}
                    {job.description && (
                      <p className="text-sm text-slate-600 mb-4 leading-relaxed line-clamp-2">{job.description}</p>
                    )}

                    {/* Skills */}
                    <div className="space-y-2">
                      {(job.required_skills_list || []).length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-xs font-semibold text-slate-500 mr-1">Required:</span>
                          {job.required_skills_list.map((skill, i) => (
                            <Badge key={i} className="bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-medium px-2 py-0.5">{skill}</Badge>
                          ))}
                        </div>
                      )}
                      {(job.preferred_skills_list || []).length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5">
                          <span className="text-xs font-semibold text-slate-500 mr-1">Preferred:</span>
                          {job.preferred_skills_list.map((skill, i) => (
                            <Badge key={i} variant="outline" className="border-green-300 text-green-700 text-xs font-medium px-2 py-0.5">{skill}</Badge>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Apply button */}
                  <div className="flex-shrink-0 self-start">
                    <Button onClick={(e) => { e.stopPropagation(); navigate('/apply'); }} className="bg-indigo-600 hover:bg-indigo-700 shadow-sm">
                      Apply <ArrowRight className="w-4 h-4 ml-1.5" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {!loading && filteredJobs.length === 0 && (
            <div className="bg-white rounded-xl shadow-md p-12 text-center">
              <Briefcase className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-2">No positions found</h3>
              <p className="text-slate-500">Try adjusting your search or filters.</p>
            </div>
          )}
        </div>

        {/* Back to Home */}
        <div className="text-center mt-8">
          <Button variant="link" onClick={() => navigate('/')} className="text-slate-600 hover:text-indigo-600">
            ← Back to home
          </Button>
        </div>
      </div>

      {/* Job Detail Modal */}
      <Dialog open={!!selectedJob} onOpenChange={(open) => { if (!open) setSelectedJob(null); }}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto bg-white">
          {selectedJob && (
            <>
              <DialogHeader>
                <DialogTitle className="text-2xl font-bold text-slate-900 pr-8">{selectedJob.title}</DialogTitle>
              </DialogHeader>

              <div className="space-y-5 mt-2">
                {/* Badges */}
                <div className="flex flex-wrap gap-2">
                  <Badge className={`${levelColors[selectedJob.experience_level] || 'bg-slate-100 text-slate-800'} text-xs px-2.5 py-0.5`}>
                    {(selectedJob.experience_level || 'mid').charAt(0).toUpperCase() + (selectedJob.experience_level || 'mid').slice(1)}
                  </Badge>
                  {selectedJob.employment_type && (
                    <Badge variant="outline" className="border-slate-300 text-slate-600 text-xs">
                      {selectedJob.employment_type.replace('-', ' ')}
                    </Badge>
                  )}
                  {selectedJob.status && (
                    <Badge className="bg-green-100 text-green-700 text-xs">{selectedJob.status}</Badge>
                  )}
                </div>

                {/* Meta info grid */}
                <div className="grid grid-cols-2 gap-3 p-4 bg-slate-50 rounded-lg">
                  {selectedJob.sector_name && (
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Building2 className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <div><span className="font-medium text-slate-700">Sector:</span> {selectedJob.sector_name}</div>
                    </div>
                  )}
                  {selectedJob.department && (
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <Briefcase className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <div><span className="font-medium text-slate-700">Department:</span> {selectedJob.department}</div>
                    </div>
                  )}
                  {selectedJob.location && (
                    <div className="flex items-center gap-2 text-sm text-slate-600">
                      <MapPin className="w-4 h-4 text-slate-400 flex-shrink-0" />
                      <div><span className="font-medium text-slate-700">Work Mode:</span> {selectedJob.location}</div>
                    </div>
                  )}
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <Clock className="w-4 h-4 text-slate-400 flex-shrink-0" />
                    <div><span className="font-medium text-slate-700">Experience:</span> {selectedJob.min_experience || 0}{selectedJob.max_experience ? `–${selectedJob.max_experience}` : '+'} years</div>
                  </div>
                  {selectedJob.salary_range && (
                    <div className="flex items-center gap-2 text-sm font-semibold text-emerald-700">
                      <IndianRupee className="w-4 h-4 flex-shrink-0" />
                      <div><span className="font-medium">Salary:</span> {selectedJob.salary_range}</div>
                    </div>
                  )}
                </div>

                {/* Full Description */}
                {selectedJob.description && (
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800 mb-2">Description</h4>
                    <div className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">{selectedJob.description}</div>
                  </div>
                )}

                {/* Skills */}
                {(selectedJob.required_skills_list || []).length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800 mb-2">Required Skills</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedJob.required_skills_list.map((skill, i) => (
                        <Badge key={i} className="bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-medium px-2.5 py-1">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                )}
                {(selectedJob.preferred_skills_list || []).length > 0 && (
                  <div>
                    <h4 className="text-sm font-semibold text-slate-800 mb-2">Preferred Skills</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedJob.preferred_skills_list.map((skill, i) => (
                        <Badge key={i} variant="outline" className="border-green-300 text-green-700 text-xs font-medium px-2.5 py-1">{skill}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Apply button */}
                <div className="pt-2">
                  <Button onClick={() => navigate('/apply')} className="w-full bg-indigo-600 hover:bg-indigo-700 shadow-sm text-base py-5">
                    Apply for this Position <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default JobListingsPage;
