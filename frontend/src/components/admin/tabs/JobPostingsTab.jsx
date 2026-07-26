import { Fragment } from 'react';
import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../ui/table';
import { TabsContent } from '../../ui/tabs';
import StatusBadge from '../../workspace/StatusBadge';
import {
  Briefcase,
  Building2,
  ChevronDown,
  ChevronUp,
  Edit,
  Eye,
  IndianRupee,
  MapPin,
  Plus,
  Trash2,
} from 'lucide-react';

const scoreClassName = (score) => {
  if (score >= 75) return 'text-emerald-700';
  if (score >= 50) return 'text-amber-700';
  return 'text-red-700';
};

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
  handleReviewCandidateMatch,
  reviewingMatch,
}) => {
  const openCreateJob = () => {
    setEditingJob(null);
    setJobForm({
      title: '',
      description: '',
      required_skills: '',
      preferred_skills: '',
      min_experience: 0,
      max_experience: '',
      department: '',
      work_mode: 'On-Site',
      sector_id: '',
      status: 'active',
      employment_type: 'full-time',
      experience_level: 'mid',
      salary_range: '',
      closes_at: '',
      role_complexity_level: 'intermediate',
    });
    setJobModalOpen(true);
  };

  return (
    <TabsContent value="job-postings">
      <Card>
        <CardHeader className="gap-4 border-b lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-1.5">
            <CardTitle>Open roles</CardTitle>
            <CardDescription>Maintain role requirements and inspect the candidates matched to each opening.</CardDescription>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <Button type="button" variant="outline" onClick={() => setSectorModalOpen(true)}>
              <Plus />
              Add sector
            </Button>
            <Button type="button" onClick={openCreateJob}>
              <Plus />
              Create role
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pt-5">
          {sectors.length > 0 ? (
            <div className="mb-5 rounded-lg border bg-slate-50/60 p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">Sectors</p>
              <div className="flex flex-wrap gap-2">
                {sectors.map((sector) => (
                  <Badge key={sector.id} variant="outline" className="border-slate-200 bg-card text-slate-700">
                    {sector.name}
                    {sector.email_alias ? <span className="ml-1 text-muted-foreground">· {sector.email_alias}</span> : null}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}

          {jobPostings.length === 0 ? (
            <div className="flex min-h-56 flex-col items-center justify-center rounded-lg border border-dashed px-6 text-center">
              <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-muted-foreground">
                <Briefcase className="h-5 w-5" />
              </span>
              <p className="font-medium text-foreground">No roles have been created</p>
              <p className="mt-1 max-w-md text-sm text-muted-foreground">Create a role with required skills to begin matching candidates.</p>
            </div>
          ) : (
            <Table className="min-w-[1040px]" aria-label="Job postings">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12"><span className="sr-only">Expand</span></TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead>Work arrangement</TableHead>
                  <TableHead>Level</TableHead>
                  <TableHead>Compensation</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Candidates</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobPostings.map((job) => {
                  const isExpanded = expandedJob === job.id;
                  const employmentType = (job.employment_type || 'full-time').replace('-', ' ');
                  const experienceLevel = job.experience_level || 'mid';

                  return (
                    <Fragment key={job.id}>
                      <TableRow>
                        <TableCell>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => setExpandedJob(isExpanded ? null : job.id)}
                            aria-expanded={isExpanded}
                            aria-label={`${isExpanded ? 'Collapse' : 'Expand'} ${job.title}`}
                            title={isExpanded ? 'Collapse role details' : 'Expand role details'}
                          >
                            {isExpanded ? <ChevronUp /> : <ChevronDown />}
                          </Button>
                        </TableCell>
                        <TableCell>
                          <p className="font-medium text-foreground">{job.title}</p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {[job.department, job.sector_name].filter(Boolean).join(' · ') || 'Unassigned'}
                          </p>
                        </TableCell>
                        <TableCell>
                          <p className="flex items-center gap-1.5 text-sm text-foreground">
                            <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                            {job.work_mode || 'On-Site'}
                          </p>
                          <p className="mt-1 text-xs capitalize text-muted-foreground">{employmentType}</p>
                        </TableCell>
                        <TableCell>
                          <p className="text-sm capitalize text-foreground">{experienceLevel}</p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {job.min_experience || 0}{job.max_experience ? `–${job.max_experience}` : '+'} years
                          </p>
                        </TableCell>
                        <TableCell>
                          {job.salary_range ? (
                            <span className="flex items-center gap-1 text-sm text-foreground">
                              <IndianRupee className="h-3.5 w-3.5 text-muted-foreground" />
                              {job.salary_range}
                            </span>
                          ) : <span className="text-sm text-muted-foreground">Not specified</span>}
                        </TableCell>
                        <TableCell><StatusBadge status={job.status || 'active'} /></TableCell>
                        <TableCell>
                          <Button type="button" variant="ghost" onClick={() => fetchJobCandidates(job.id)}>
                            <Eye />
                            View matches
                          </Button>
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-1.5">
                            <Button
                              type="button"
                              variant="outline"
                              size="icon"
                              onClick={() => openEditJob(job)}
                              aria-label={`Edit ${job.title}`}
                              title="Edit role"
                            >
                              <Edit />
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteJob(job.id)}
                              disabled={deletingJob === job.id}
                              className="text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                              aria-label={`Remove ${job.title}`}
                              title="Close or remove role"
                            >
                              <Trash2 />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>

                      {isExpanded ? (
                        <TableRow className="bg-slate-50/50 hover:bg-slate-50/50">
                          <TableCell colSpan={8} className="p-5">
                            <div className="grid gap-6 lg:grid-cols-2">
                              <section>
                                <h4 className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">Description</h4>
                                <p className="mt-2 whitespace-pre-line text-sm leading-6 text-slate-700">
                                  {job.description || 'No description provided.'}
                                </p>
                              </section>
                              <section className="space-y-4">
                                <div>
                                  <h4 className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">Required skills</h4>
                                  <div className="mt-2 flex flex-wrap gap-2">
                                    {(job.required_skills_list || []).length > 0
                                      ? job.required_skills_list.map((skill, index) => (
                                        <Badge key={`${skill}-${index}`} variant="outline" className="border-blue-200 bg-blue-50 text-blue-700">
                                          {skill}
                                        </Badge>
                                      ))
                                      : <span className="text-sm text-muted-foreground">None specified</span>}
                                  </div>
                                </div>
                                {job.preferred_skills_list?.length > 0 ? (
                                  <div>
                                    <h4 className="text-xs font-semibold uppercase tracking-[0.08em] text-muted-foreground">Preferred skills</h4>
                                    <div className="mt-2 flex flex-wrap gap-2">
                                      {job.preferred_skills_list.map((skill, index) => (
                                        <Badge key={`${skill}-${index}`} variant="outline" className="border-slate-200 bg-card text-slate-700">
                                          {skill}
                                        </Badge>
                                      ))}
                                    </div>
                                  </div>
                                ) : null}
                                <div className="flex items-center gap-2 border-t pt-4 text-sm text-muted-foreground">
                                  <Building2 className="h-4 w-4" />
                                  {job.department || 'No department'} · {job.sector_name || 'No sector'}
                                </div>
                              </section>
                            </div>
                          </TableCell>
                        </TableRow>
                      ) : null}
                    </Fragment>
                  );
                })}
              </TableBody>
            </Table>
          )}

          {selectedJobForCandidates ? (
            <section className="mt-6 rounded-xl border border-blue-200 bg-blue-50/40 p-4 sm:p-5" aria-live="polite">
              <div className="mb-4">
                <h3 className="font-semibold text-foreground">Matched candidates</h3>
                <p className="mt-1 text-sm text-muted-foreground">Results for role ID {selectedJobForCandidates}</p>
              </div>
              {jobCandidates.length === 0 ? (
                <p className="rounded-lg border border-dashed bg-card px-4 py-8 text-center text-sm text-muted-foreground">
                  No matched candidates were returned for this role.
                </p>
              ) : (
                <Table className="min-w-[1040px]" aria-label="Matched candidates for selected role">
                  <TableHeader>
                    <TableRow>
                      <TableHead>Candidate</TableHead>
                      <TableHead>Match score</TableHead>
                      <TableHead>Skill match</TableHead>
                      <TableHead>Experience match</TableHead>
                      <TableHead>Reasoning</TableHead>
                      <TableHead>Review state</TableHead>
                      <TableHead className="text-right">Decision</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {jobCandidates.map((candidate) => (
                      <TableRow key={candidate.id}>
                        <TableCell>
                          <p className="font-medium text-foreground">{candidate.name}</p>
                          <p className="mt-0.5 text-xs text-muted-foreground">{candidate.email}</p>
                        </TableCell>
                        <TableCell className={`font-semibold tabular-nums ${scoreClassName(candidate.match_score)}`}>
                          {candidate.match_score}%
                        </TableCell>
                        <TableCell className="tabular-nums text-foreground">{candidate.skill_match_score}%</TableCell>
                        <TableCell className="tabular-nums text-foreground">{candidate.experience_match_score}%</TableCell>
                        <TableCell className="max-w-[280px] truncate text-xs text-muted-foreground" title={candidate.ai_reasoning}>
                          {candidate.ai_reasoning || 'Not available'}
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={candidate.status || 'auto_matched'} />
                          <p className="mt-1 text-xs text-muted-foreground">
                            {candidate.reviewed_at
                              ? `Reviewed ${new Date(candidate.reviewed_at).toLocaleString()}`
                              : 'Awaiting review'}
                          </p>
                        </TableCell>
                        <TableCell>
                          <div className="flex justify-end gap-2">
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              disabled={reviewingMatch === `${candidate.candidate_id}:${selectedJobForCandidates}` || candidate.status === 'confirmed'}
                              onClick={() => handleReviewCandidateMatch(candidate.candidate_id, selectedJobForCandidates, 'confirmed')}
                              aria-label={`Confirm ${candidate.name} match`}
                            >
                              Confirm
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              disabled={reviewingMatch === `${candidate.candidate_id}:${selectedJobForCandidates}` || candidate.status === 'rejected'}
                              onClick={() => handleReviewCandidateMatch(candidate.candidate_id, selectedJobForCandidates, 'rejected')}
                              aria-label={`Reject ${candidate.name} match`}
                              className="text-red-700 hover:bg-red-50 hover:text-red-800"
                            >
                              Reject
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </section>
          ) : null}
        </CardContent>
      </Card>
    </TabsContent>
  );
};

export default JobPostingsTab;
