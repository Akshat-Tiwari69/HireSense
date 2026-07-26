import { Button } from '../../ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Loader2, Sparkles } from 'lucide-react';
import { api } from '../../../services/api';
import { useToast } from '../../../hooks/use-toast';

const JobModal = ({
  jobModalOpen,
  setJobModalOpen,
  editingJob,
  jobForm,
  setJobForm,
  savingJob,
  enhancingJob,
  setEnhancingJob,
  sectors,
  handleSaveJob,
}) => {
  const { toast } = useToast();

  const enhanceJob = async () => {
    setEnhancingJob(true);
    try {
      const response = await api.post('/api/admin/ai-enhance', {
        type: 'job',
        title: jobForm.title,
        description: jobForm.description,
      });
      if (response.data.status === 'success') {
        setJobForm((current) => ({
          ...current,
          title: response.data.enhanced_title || current.title,
          description: response.data.enhanced_description || current.description,
          required_skills: response.data.required_skills || current.required_skills,
          preferred_skills: response.data.preferred_skills || current.preferred_skills,
        }));
        toast({ title: 'Role refined', description: 'The title, description, and skills were updated.', duration: 3000 });
      } else {
        toast({ title: 'Enhancement failed', description: response.data.message, variant: 'destructive' });
      }
    } catch (error) {
      toast({ title: 'Enhancement failed', description: error.response?.data?.message || error.message, variant: 'destructive' });
    } finally {
      setEnhancingJob(false);
    }
  };

  return (
    <Dialog open={jobModalOpen} onOpenChange={setJobModalOpen}>
      <DialogContent
        className="max-w-3xl"
        onPointerDownOutside={(event) => event.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{editingJob ? 'Edit role' : 'Create role'}</DialogTitle>
          <DialogDescription>
            Define the position, working arrangement, and skills used for candidate matching.
          </DialogDescription>
        </DialogHeader>

        <form
          className="space-y-6"
          onSubmit={(event) => {
            event.preventDefault();
            handleSaveJob();
          }}
        >
          <section className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="job-title">Role title</Label>
              <Input
                id="job-title"
                autoFocus
                value={jobForm.title}
                onChange={(event) => setJobForm({ ...jobForm, title: event.target.value })}
                placeholder="Senior Software Engineer"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="job-description">Description</Label>
              <textarea
                id="job-description"
                value={jobForm.description}
                onChange={(event) => setJobForm({ ...jobForm, description: event.target.value })}
                className="min-h-32 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm text-foreground shadow-sm outline-none transition-colors placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                placeholder="Describe the responsibilities and expected outcomes for this role."
              />
            </div>
            {jobForm.title || jobForm.description ? (
              <Button type="button" variant="outline" disabled={enhancingJob} onClick={enhanceJob}>
                {enhancingJob ? <Loader2 className="animate-spin" /> : <Sparkles className="text-blue-700" />}
                {enhancingJob ? 'Refining role' : 'Refine with AI'}
              </Button>
            ) : null}
          </section>

          <section className="space-y-4 rounded-xl border bg-slate-50/60 p-4 sm:p-5">
            <div>
              <h3 className="font-semibold text-foreground">Matching criteria</h3>
              <p className="mt-1 text-sm text-muted-foreground">Required skills carry the most weight in candidate scoring.</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="job-required-skills">Required skills <span className="font-normal text-muted-foreground">(comma-separated)</span></Label>
              <Input
                id="job-required-skills"
                value={jobForm.required_skills}
                onChange={(event) => setJobForm({ ...jobForm, required_skills: event.target.value })}
                placeholder="Python, React, PostgreSQL, Docker"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="job-preferred-skills">Preferred skills <span className="font-normal text-muted-foreground">(comma-separated)</span></Label>
              <Input
                id="job-preferred-skills"
                value={jobForm.preferred_skills}
                onChange={(event) => setJobForm({ ...jobForm, preferred_skills: event.target.value })}
                placeholder="Kubernetes, AWS, GraphQL, TypeScript"
              />
            </div>
          </section>

          <section className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="job-experience-level">Experience level</Label>
                <Select value={jobForm.experience_level} onValueChange={(experience_level) => setJobForm({ ...jobForm, experience_level })}>
                  <SelectTrigger id="job-experience-level">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent position="popper" sideOffset={4}>
                    <SelectItem value="junior">Junior (0–2 years)</SelectItem>
                    <SelectItem value="mid">Mid-level (2–5 years)</SelectItem>
                    <SelectItem value="senior">Senior (5–10 years)</SelectItem>
                    <SelectItem value="lead">Lead (8–15 years)</SelectItem>
                    <SelectItem value="principal">Principal (12+ years)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="job-employment-type">Employment type</Label>
                <Select value={jobForm.employment_type} onValueChange={(employment_type) => setJobForm({ ...jobForm, employment_type })}>
                  <SelectTrigger id="job-employment-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent position="popper" sideOffset={4}>
                    <SelectItem value="full-time">Full-time</SelectItem>
                    <SelectItem value="part-time">Part-time</SelectItem>
                    <SelectItem value="contract">Contract</SelectItem>
                    <SelectItem value="internship">Internship</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="job-min-experience">Minimum experience</Label>
                <Input
                  id="job-min-experience"
                  type="number"
                  min="0"
                  value={jobForm.min_experience}
                  onChange={(event) => setJobForm({ ...jobForm, min_experience: event.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="job-max-experience">Maximum experience</Label>
                <Input
                  id="job-max-experience"
                  type="number"
                  min="0"
                  value={jobForm.max_experience}
                  onChange={(event) => setJobForm({ ...jobForm, max_experience: event.target.value })}
                  placeholder="Optional"
                />
              </div>
              <div className="space-y-2 sm:col-span-2 lg:col-span-1">
                <Label htmlFor="job-salary-range">Salary range</Label>
                <Input
                  id="job-salary-range"
                  value={jobForm.salary_range}
                  onChange={(event) => setJobForm({ ...jobForm, salary_range: event.target.value })}
                  placeholder="₹8L–₹12L per annum"
                />
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="job-department">Department</Label>
                <Input
                  id="job-department"
                  value={jobForm.department}
                  onChange={(event) => setJobForm({ ...jobForm, department: event.target.value })}
                  placeholder="Engineering"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="job-work-mode">Work mode</Label>
                <Select value={jobForm.work_mode} onValueChange={(work_mode) => setJobForm({ ...jobForm, work_mode })}>
                  <SelectTrigger id="job-work-mode">
                    <SelectValue placeholder="Select work mode" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Remote">Remote</SelectItem>
                    <SelectItem value="On-Site">On-site</SelectItem>
                    <SelectItem value="Hybrid">Hybrid</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 sm:col-span-2 lg:col-span-1">
                <Label htmlFor="job-sector">Sector</Label>
                <Select value={jobForm.sector_id} onValueChange={(sector_id) => setJobForm({ ...jobForm, sector_id })}>
                  <SelectTrigger id="job-sector">
                    <SelectValue placeholder="Select sector" />
                  </SelectTrigger>
                  <SelectContent position="popper" sideOffset={4}>
                    <SelectItem value="none">No sector</SelectItem>
                    {sectors.map((sector) => (
                      <SelectItem key={sector.id} value={String(sector.id)}>{sector.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="job-status">Status</Label>
                <Select value={jobForm.status} onValueChange={(status) => setJobForm({ ...jobForm, status })}>
                  <SelectTrigger id="job-status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent position="popper" sideOffset={4}>
                    <SelectItem value="draft">Draft</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="paused">Paused</SelectItem>
                    <SelectItem value="closed">Closed</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="job-role-complexity">Role complexity</Label>
                <Select
                  value={jobForm.role_complexity_level}
                  onValueChange={(role_complexity_level) => setJobForm({ ...jobForm, role_complexity_level })}
                >
                  <SelectTrigger id="job-role-complexity">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent position="popper" sideOffset={4}>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="intermediate">Intermediate</SelectItem>
                    <SelectItem value="advanced">Advanced</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2 sm:col-span-2 lg:col-span-1">
                <Label htmlFor="job-closes-at">Applications close</Label>
                <Input
                  id="job-closes-at"
                  type="datetime-local"
                  value={jobForm.closes_at}
                  onChange={(event) => setJobForm({ ...jobForm, closes_at: event.target.value })}
                />
              </div>
            </div>
          </section>

          <DialogFooter className="border-t pt-5">
            <Button type="button" variant="outline" onClick={() => setJobModalOpen(false)}>Cancel</Button>
            <Button type="submit" disabled={savingJob}>
              {savingJob ? <Loader2 className="animate-spin" /> : null}
              {savingJob ? 'Saving role' : editingJob ? 'Save changes' : 'Create role'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default JobModal;
