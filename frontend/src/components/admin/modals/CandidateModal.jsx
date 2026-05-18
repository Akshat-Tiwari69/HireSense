import React from 'react';
import { Button } from '../../ui/button';
import { Input } from '../../ui/input';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from '../../ui/dialog';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';

const CandidateModal = ({
  candidateModalOpen,
  setCandidateModalOpen,
  candidateForm,
  setCandidateForm,
  savingCandidate,
  handleSaveCandidate,
}) => (
  <Dialog open={candidateModalOpen} onOpenChange={setCandidateModalOpen}>
    <DialogContent className="bg-white border-slate-200 shadow-md">
      <DialogHeader>
        <DialogTitle className="text-slate-900">Edit Candidate</DialogTitle>
        <DialogDescription className="text-slate-600">Update candidate details</DialogDescription>
      </DialogHeader>
      <div className="space-y-4 py-4">
        <div className="space-y-2">
          <Label className="text-slate-700">Name</Label>
          <Input
            value={candidateForm.name}
            onChange={(e) => setCandidateForm({ ...candidateForm, name: e.target.value })}
            className="bg-white border-slate-300 text-slate-900"
          />
        </div>
        <div className="space-y-2">
          <Label className="text-slate-700">Email</Label>
          <Input
            type="email"
            value={candidateForm.email}
            onChange={(e) => setCandidateForm({ ...candidateForm, email: e.target.value })}
            className="bg-white border-slate-300 text-slate-900"
          />
        </div>
        <div className="space-y-2">
          <Label className="text-slate-700">Phone</Label>
          <Input
            value={candidateForm.phone}
            onChange={(e) => setCandidateForm({ ...candidateForm, phone: e.target.value })}
            className="bg-white border-slate-300 text-slate-900"
          />
        </div>
        <div className="space-y-2">
          <Label className="text-slate-700">Status</Label>
          <Select value={candidateForm.status} onValueChange={(v) => setCandidateForm({ ...candidateForm, status: v })}>
            <SelectTrigger className="bg-white border-slate-300 text-slate-900">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-white border-slate-200 shadow-md">
              <SelectItem value="Applied">Applied</SelectItem>
              <SelectItem value="Scheduled">Scheduled</SelectItem>
              <SelectItem value="Completed">Completed</SelectItem>
              <SelectItem value="Rejected">Rejected</SelectItem>
              <SelectItem value="Hired">Hired</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label className="text-slate-700">Match Score (%)</Label>
          <Input
            type="number"
            min="0"
            max="100"
            value={candidateForm.match_score}
            onChange={(e) => setCandidateForm({ ...candidateForm, match_score: parseInt(e.target.value) || 0 })}
            className="bg-white border-slate-300 text-slate-900"
          />
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => setCandidateModalOpen(false)} className="border-slate-300 text-slate-700">
          Cancel
        </Button>
        <Button onClick={handleSaveCandidate} disabled={savingCandidate} className="bg-indigo-600 hover:bg-indigo-700">
          Update
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export default CandidateModal;
