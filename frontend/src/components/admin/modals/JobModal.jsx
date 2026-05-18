import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../../ui/dialog';
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

  return (
    <Dialog open={jobModalOpen} onOpenChange={setJobModalOpen}>
      <DialogContent className="bg-white border-slate-200 shadow-md max-w-2xl max-h-[90vh] overflow-y-auto [&_input]:caret-slate-900 [&_textarea]:caret-slate-900" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle className="text-slate-900">{editingJob ? 'Edit Job Posting' : 'Create Job Posting'}</DialogTitle>
          <DialogDescription className="text-slate-600">
            {editingJob ? 'Update job details and skill requirements' : 'Define a new job with required skills. AI will match incoming candidates automatically.'}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label className="text-slate-700">Job Title *</Label>
            <Input
              autoFocus
              value={jobForm.title}
              onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })}
              className="bg-white border-slate-300 text-slate-900 focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Senior Software Engineer"
            />
          </div>
          <div className="space-y-2">
            <Label className="text-slate-700">Description</Label>
            <textarea
              value={jobForm.description}
              onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })}
              className="w-full bg-white border border-slate-300 text-slate-900 rounded-md p-2 text-sm min-h-[80px]"
              placeholder="Detailed job description..."
            />
          </div>
          {/* AI Enhance Button */}
          {(jobForm.title || jobForm.description) && (
            <Button
              type="button"
              variant="outline"
              className="border-purple-300 text-purple-700 hover:bg-purple-50"
              disabled={enhancingJob}
              onClick={async () => {
                setEnhancingJob(true);
                try {
                  const res = await api.post('/api/admin/ai-enhance', {
                    type: 'job',
                    title: jobForm.title,
                    description: jobForm.description
                  });
                  if (res.data.status === 'success') {
                    setJobForm(prev => ({
                      ...prev,
                      title: res.data.enhanced_title || prev.title,
                      description: res.data.enhanced_description || prev.description,
                      required_skills: res.data.required_skills || prev.required_skills,
                      preferred_skills: res.data.preferred_skills || prev.preferred_skills
                    }));
                    toast({ title: 'Enhanced', description: 'Title, description & skills polished by AI', duration: 3000 });
                  } else {
                    toast({ title: 'AI Error', description: res.data.message, variant: 'destructive' });
                  }
                } catch (err) {
                  toast({ title: 'AI Error', description: err.response?.data?.message || err.message, variant: 'destructive' });
                } finally {
                  setEnhancingJob(false);
                }
              }}
            >
              {enhancingJob ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Sparkles className="w-4 h-4 mr-2" />}
              {enhancingJob ? 'Enhancing...' : 'Enhance with AI'}
            </Button>
          )}

          {/* Skills Section — THE KEY IMPROVEMENT */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg space-y-3">
            <p className="text-sm font-semibold text-blue-900"> Skill Requirements (Critical for AI Matching)</p>
            <div className="space-y-2">
              <Label className="text-blue-800 font-medium">Required Skills * <span className="font-normal text-xs">(comma-separated)</span></Label>
              <Input
                value={jobForm.required_skills}
                onChange={(e) => setJobForm({ ...jobForm, required_skills: e.target.value })}
                className="bg-white border-blue-300 text-slate-900"
                placeholder="e.g., Python, React, PostgreSQL, Docker"
              />
              <p className="text-xs text-blue-700">These skills are mandatory. Candidates missing required skills will score lower.</p>
            </div>
            <div className="space-y-2">
              <Label className="text-blue-800 font-medium">Preferred Skills <span className="font-normal text-xs">(comma-separated)</span></Label>
              <Input
                value={jobForm.preferred_skills}
                onChange={(e) => setJobForm({ ...jobForm, preferred_skills: e.target.value })}
                className="bg-white border-blue-300 text-slate-900"
                placeholder="e.g., Kubernetes, AWS, GraphQL, TypeScript"
              />
              <p className="text-xs text-blue-700">Nice-to-have skills that boost match scores.</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-slate-700">Experience Level</Label>
              <Select value={jobForm.experience_level} onValueChange={(v) => setJobForm({ ...jobForm, experience_level: v })}>
                <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-slate-200 shadow-md" position="popper" sideOffset={4}>
                  <SelectItem value="junior">Junior (0-2 years)</SelectItem>
                  <SelectItem value="mid">Mid-Level (2-5 years)</SelectItem>
                  <SelectItem value="senior">Senior (5-10 years)</SelectItem>
                  <SelectItem value="lead">Lead (8-15 years)</SelectItem>
                  <SelectItem value="principal">Principal (12+ years)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Employment Type</Label>
              <Select value={jobForm.employment_type} onValueChange={(v) => setJobForm({ ...jobForm, employment_type: v })}>
                <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-slate-200 shadow-md" position="popper" sideOffset={4}>
                  <SelectItem value="full-time">Full-time</SelectItem>
                  <SelectItem value="part-time">Part-time</SelectItem>
                  <SelectItem value="contract">Contract</SelectItem>
                  <SelectItem value="internship">Internship</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label className="text-slate-700">Min Experience (yrs)</Label>
              <Input
                type="number" min="0"
                value={jobForm.min_experience}
                onChange={(e) => setJobForm({ ...jobForm, min_experience: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Max Experience (yrs)</Label>
              <Input
                type="number" min="0"
                value={jobForm.max_experience}
                onChange={(e) => setJobForm({ ...jobForm, max_experience: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
                placeholder="Optional"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Salary Range</Label>
              <Input
                value={jobForm.salary_range}
                onChange={(e) => setJobForm({ ...jobForm, salary_range: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
                placeholder="e.g., ₹8L-₹12L per annum"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label className="text-slate-700">Department</Label>
              <Input
                value={jobForm.department}
                onChange={(e) => setJobForm({ ...jobForm, department: e.target.value })}
                className="bg-white border-slate-300 text-slate-900"
                placeholder="e.g., Engineering"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Work Mode</Label>
              <Select value={jobForm.location} onValueChange={(v) => setJobForm({ ...jobForm, location: v })}>
                <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                  <SelectValue placeholder="Select work mode" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Remote">Remote</SelectItem>
                  <SelectItem value="On-Site">On-Site</SelectItem>
                  <SelectItem value="Hybrid">Hybrid</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label className="text-slate-700">Sector</Label>
              <Select value={jobForm.sector_id} onValueChange={(v) => setJobForm({ ...jobForm, sector_id: v })}>
                <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                  <SelectValue placeholder="Select sector" />
                </SelectTrigger>
                <SelectContent className="bg-white border-slate-200 shadow-md" position="popper" sideOffset={4}>
                  <SelectItem value="none">No Sector</SelectItem>
                  {sectors.map(s => (
                    <SelectItem key={s.id} value={String(s.id)}>{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {editingJob && (
            <div className="space-y-2">
              <Label className="text-slate-700">Status</Label>
              <Select value={jobForm.status} onValueChange={(v) => setJobForm({ ...jobForm, status: v })}>
                <SelectTrigger className="bg-white border-slate-300 text-slate-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-slate-200 shadow-md" position="popper" sideOffset={4}>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="paused">Paused</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setJobModalOpen(false)} className="border-slate-300 text-slate-700">
            Cancel
          </Button>
          <Button onClick={handleSaveJob} disabled={savingJob} className="bg-indigo-600 hover:bg-indigo-700">
            {savingJob ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            {editingJob ? 'Update' : 'Create'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default JobModal;
