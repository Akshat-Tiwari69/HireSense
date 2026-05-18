import React from 'react';
import { Button } from '../../ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { Badge } from '../../ui/badge';
import { TabsContent } from '../../ui/tabs';
import {
  Plus, Edit, Trash2, Eye, ChevronDown, ChevronUp,
  MapPin, IndianRupee, Clock, Building2
} from 'lucide-react';

const JobPostingsTab = ({
  jobPostings,
  sectors,
  expandedJob,
  setExpandedJob,
  deletingJob,
  selectedJobForCandidates,
  jobCandidates,
  setSectorModalOpen,
  setEditingJob,
  setJobForm,
  setJobModalOpen,
  openEditJob,
  handleDeleteJob,
  fetchJobCandidates,
}) => (
  <TabsContent value="job-postings">
    <Card className="bg-white border-none shadow-md hover:shadow-xl transition-all duration-300">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-slate-900">Job Postings</CardTitle>
          <CardDescription className="text-slate-600">Manage job openings with required/preferred skills. AI will match candidates to the best-fit role.</CardDescription>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setSectorModalOpen(true)} className="border-slate-300 text-slate-700">
            <Plus className="w-4 h-4 mr-2" />
            Add Sector
          </Button>
          <Button onClick={() => { setEditingJob(null); setJobForm({ title: '', description: '', required_skills: '', preferred_skills: '', min_experience: 0, max_experience: '', department: '', location: '', sector_id: '', status: 'active', employment_type: 'full-time', experience_level: 'mid', salary_range: '' }); setJobModalOpen(true); }} className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="w-4 h-4 mr-2" />
            Create Job
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {/* Sectors overview */}
        {sectors.length > 0 && (
          <div className="mb-6">
            <p className="text-sm font-semibold text-slate-700 mb-2">Sectors</p>
            <div className="flex flex-wrap gap-2">
              {sectors.map(s => (
                <Badge key={s.id} className="bg-indigo-100 text-indigo-800 border-indigo-200">
                  {s.name} {s.email_alias && <span className="ml-1 opacity-70">({s.email_alias})</span>}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <Table>
          <TableHeader>
            <TableRow className="border-slate-200">
              <TableHead className="text-slate-700 w-8"></TableHead>
              <TableHead className="text-slate-700">Title</TableHead>
              <TableHead className="text-slate-700">Department</TableHead>
              <TableHead className="text-slate-700">Sector</TableHead>
              <TableHead className="text-slate-700">Work Mode</TableHead>
              <TableHead className="text-slate-700">Level / Type</TableHead>
              <TableHead className="text-slate-700">Experience</TableHead>
              <TableHead className="text-slate-700">Salary</TableHead>
              <TableHead className="text-slate-700">Status</TableHead>
              <TableHead className="text-slate-700">Candidates</TableHead>
              <TableHead className="text-slate-700">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {jobPostings.map((job) => (
              <React.Fragment key={job.id}>
                <TableRow className="border-slate-200 cursor-pointer hover:bg-slate-50" onClick={() => setExpandedJob(expandedJob === job.id ? null : job.id)}>
                  <TableCell className="text-slate-400 px-2">
                    {expandedJob === job.id ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </TableCell>
                  <TableCell className="text-slate-900 font-medium">{job.title}</TableCell>
                  <TableCell className="text-slate-700 text-sm">{job.department || <span className="text-slate-400">—</span>}</TableCell>
                  <TableCell className="text-slate-700 text-sm">{job.sector_name || <span className="text-slate-400">Unassigned</span>}</TableCell>
                  <TableCell className="text-slate-700 text-sm">
                    {job.location ? (
                      <span className="flex items-center gap-1"><MapPin className="w-3 h-3 text-slate-400" />{job.location}</span>
                    ) : <span className="text-slate-400">—</span>}
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-col gap-1">
                      <Badge className={`text-xs ${
                        job.experience_level === 'senior' ? 'bg-purple-600' :
                        job.experience_level === 'lead' ? 'bg-red-600' :
                        job.experience_level === 'principal' ? 'bg-amber-700' :
                        job.experience_level === 'junior' ? 'bg-green-600' :
                        'bg-blue-600'
                      } text-white`}>
                        {(job.experience_level || 'mid').charAt(0).toUpperCase() + (job.experience_level || 'mid').slice(1)}
                      </Badge>
                      <span className="text-xs text-slate-500">{(job.employment_type || 'full-time').replace('-', ' ')}</span>
                    </div>
                  </TableCell>
                  <TableCell className="text-slate-700 text-sm">
                    {job.min_experience || 0}{job.max_experience ? `–${job.max_experience}` : '+'} yrs
                  </TableCell>
                  <TableCell className="text-slate-700 text-sm">
                    {job.salary_range ? (
                      <span className="flex items-center gap-1"><IndianRupee className="w-3 h-3 text-slate-400" />{job.salary_range}</span>
                    ) : <span className="text-slate-400">—</span>}
                  </TableCell>
                  <TableCell>
                    <Badge className={job.status === 'active' ? 'bg-green-600' : job.status === 'closed' ? 'bg-red-600' : 'bg-slate-600'}>
                      {job.status ? job.status.charAt(0).toUpperCase() + job.status.slice(1) : 'Active'}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); fetchJobCandidates(job.id); }} className="text-indigo-600 hover:text-indigo-800 text-xs">
                      <Eye className="w-3 h-3 mr-1" /> View
                    </Button>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-1">
                      <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); openEditJob(job); }} className="text-slate-600 hover:text-indigo-600">
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleDeleteJob(job.id); }} disabled={deletingJob === job.id} className="text-red-400 hover:text-red-600">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
                {/* Expanded detail row */}
                {expandedJob === job.id && (
                  <TableRow className="bg-slate-50/80 border-slate-200">
                    <TableCell colSpan={11} className="py-4 px-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Left: Description */}
                        <div>
                          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Description</p>
                          {job.description ? (
                            <p className="text-sm text-slate-700 whitespace-pre-line leading-relaxed">{job.description}</p>
                          ) : (
                            <p className="text-sm text-slate-400 italic">No description provided</p>
                          )}
                        </div>
                        {/* Right: Skills & Details */}
                        <div className="space-y-4">
                          <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Required Skills</p>
                            <div className="flex flex-wrap gap-1">
                              {(job.required_skills_list || []).length > 0 ? (
                                job.required_skills_list.map((skill, i) => (
                                  <Badge key={i} className="bg-blue-100 text-blue-800 text-xs">{skill}</Badge>
                                ))
                              ) : <span className="text-sm text-slate-400">None specified</span>}
                            </div>
                          </div>
                          {job.preferred_skills_list?.length > 0 && (
                            <div>
                              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Preferred Skills</p>
                              <div className="flex flex-wrap gap-1">
                                {job.preferred_skills_list.map((skill, i) => (
                                  <Badge key={i} variant="outline" className="text-xs border-green-300 text-green-700">{skill}</Badge>
                                ))}
                              </div>
                            </div>
                          )}
                          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-200">
                            <div className="flex items-center gap-2 text-sm text-slate-600">
                              <Building2 className="w-4 h-4 text-slate-400" />
                              <span><span className="font-medium">Dept:</span> {job.department || '—'}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-slate-600">
                              <MapPin className="w-4 h-4 text-slate-400" />
                              <span><span className="font-medium">Work Mode:</span> {job.location || '—'}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-slate-600">
                              <Clock className="w-4 h-4 text-slate-400" />
                              <span><span className="font-medium">Type:</span> {(job.employment_type || 'full-time').replace('-', ' ')}</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-slate-600">
                              <IndianRupee className="w-4 h-4 text-slate-400" />
                              <span><span className="font-medium">Salary:</span> {job.salary_range || '—'}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
            ))}
          </TableBody>
        </Table>
        {jobPostings.length === 0 && (
          <p className="text-slate-600 text-center py-8">No job postings found. Create one with required skills to enable AI candidate matching.</p>
        )}

        {/* Matched candidates for selected job */}
        {selectedJobForCandidates && jobCandidates.length > 0 && (
          <div className="mt-6 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
            <h4 className="font-semibold text-indigo-900 mb-3">
              Matched Candidates for Job #{selectedJobForCandidates}
            </h4>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-indigo-800">Candidate</TableHead>
                  <TableHead className="text-indigo-800">Match Score</TableHead>
                  <TableHead className="text-indigo-800">Skill Match</TableHead>
                  <TableHead className="text-indigo-800">Exp Match</TableHead>
                  <TableHead className="text-indigo-800">AI Reasoning</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobCandidates.map((c) => (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium text-slate-900">{c.name} <span className="text-xs text-slate-500">({c.email})</span></TableCell>
                    <TableCell>
                      <span className={`font-bold ${c.match_score >= 75 ? 'text-green-600' : c.match_score >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                        {c.match_score}%
                      </span>
                    </TableCell>
                    <TableCell className="text-slate-700">{c.skill_match_score}%</TableCell>
                    <TableCell className="text-slate-700">{c.experience_match_score}%</TableCell>
                    <TableCell className="text-slate-600 text-xs max-w-[250px] truncate" title={c.ai_reasoning}>{c.ai_reasoning || 'N/A'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  </TabsContent>
);

export default JobPostingsTab;
