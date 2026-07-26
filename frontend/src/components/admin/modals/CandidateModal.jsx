import { Button } from '../../ui/button';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../../ui/dialog';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/select';
import { Loader2 } from 'lucide-react';

const CandidateModal = ({
  candidateModalOpen,
  setCandidateModalOpen,
  candidateForm,
  setCandidateForm,
  savingCandidate,
  handleSaveCandidate,
}) => (
  <Dialog open={candidateModalOpen} onOpenChange={setCandidateModalOpen}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Edit candidate</DialogTitle>
        <DialogDescription>Update contact information, pipeline status, and the current match score.</DialogDescription>
      </DialogHeader>

      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          handleSaveCandidate();
        }}
      >
        <div className="space-y-2">
          <Label htmlFor="candidate-name">Name</Label>
          <Input
            id="candidate-name"
            autoComplete="name"
            value={candidateForm.name}
            onChange={(event) => setCandidateForm({ ...candidateForm, name: event.target.value })}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="candidate-email">Email</Label>
          <Input
            id="candidate-email"
            type="email"
            autoComplete="email"
            value={candidateForm.email}
            onChange={(event) => setCandidateForm({ ...candidateForm, email: event.target.value })}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="candidate-phone">Phone</Label>
          <Input
            id="candidate-phone"
            type="tel"
            autoComplete="tel"
            value={candidateForm.phone}
            onChange={(event) => setCandidateForm({ ...candidateForm, phone: event.target.value })}
          />
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="candidate-status">Status</Label>
            <Select value={candidateForm.status} onValueChange={(status) => setCandidateForm({ ...candidateForm, status })}>
              <SelectTrigger id="candidate-status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="applied">Applied</SelectItem>
                <SelectItem value="absence_of_details">Missing details</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="under_review">Under review</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="hired">Hired</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="candidate-match-score">Match score (%)</Label>
            <Input
              id="candidate-match-score"
              type="number"
              min="0"
              max="100"
              value={candidateForm.match_score}
              onChange={(event) => setCandidateForm({ ...candidateForm, match_score: parseInt(event.target.value, 10) || 0 })}
            />
          </div>
        </div>

        <DialogFooter className="border-t pt-5">
          <Button type="button" variant="outline" onClick={() => setCandidateModalOpen(false)}>Cancel</Button>
          <Button type="submit" disabled={savingCandidate}>
            {savingCandidate ? <Loader2 className="animate-spin" /> : null}
            {savingCandidate ? 'Saving' : 'Save changes'}
          </Button>
        </DialogFooter>
      </form>
    </DialogContent>
  </Dialog>
);

export default CandidateModal;
