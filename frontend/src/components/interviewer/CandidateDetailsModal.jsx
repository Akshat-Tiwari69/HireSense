import { useEffect, useState } from 'react';
import {
  AlertTriangle,
  Check,
  Download,
  FileText,
  LoaderCircle,
  ShieldCheck,
  X,
} from 'lucide-react';

import { Button } from '../ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import StatusBadge from '../workspace/StatusBadge';

const clampScore = (value) => Math.min(100, Math.max(0, Number(value) || 0));

const ScoreRow = ({ label, value }) => {
  const score = clampScore(value);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="font-semibold tabular-nums text-slate-950">{Math.round(score)}%</span>
      </div>
      <div
        className="h-1.5 overflow-hidden rounded-full bg-slate-100"
        role="progressbar"
        aria-label={label}
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={Math.round(score)}
      >
        <div className="h-full rounded-full bg-blue-600" style={{ width: `${score}%` }} />
      </div>
    </div>
  );
};

const InsightList = ({ items, emptyLabel, tone }) => {
  const values = Array.isArray(items) ? items.filter(Boolean) : [];
  const Icon = tone === 'positive' ? Check : AlertTriangle;
  const iconClass = tone === 'positive' ? 'text-emerald-600' : 'text-amber-600';

  if (!values.length) {
    return <p className="text-sm text-slate-500">{emptyLabel}</p>;
  }

  return (
    <ul className="space-y-3">
      {values.map((item, index) => (
        <li key={`${item}-${index}`} className="flex items-start gap-2.5 text-sm leading-6 text-slate-700">
          <Icon className={`mt-1 h-4 w-4 shrink-0 ${iconClass}`} aria-hidden="true" />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
};

const CandidateDetailsModal = ({
  open,
  onOpenChange,
  selectedCandidate,
  assessmentDetails,
  assessmentLoading,
  decisionLoading,
  onDownloadResume,
  onFinalDecision,
}) => {
  const [rationale, setRationale] = useState('');
  const [nextSteps, setNextSteps] = useState('');

  useEffect(() => {
    if (open) {
      setRationale('');
      setNextSteps('');
    }
  }, [open]);

  const initials = selectedCandidate?.name
    ?.split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase() || 'HC';
  const matchScore = clampScore(selectedCandidate?.aiMatchScore);
  const canMakeDecision = selectedCandidate?.status === 'Completed'
    && assessmentDetails
    && !assessmentDetails.final_decision;

  const submitDecision = (decision) => {
    onFinalDecision(decision, rationale.trim() || null, nextSteps.trim() || null);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl p-0">
        <DialogHeader className="border-b border-slate-200 px-6 py-5 pr-14 sm:px-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex min-w-0 items-center gap-3.5">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-slate-950 text-sm font-semibold text-white">
                {initials}
              </div>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <DialogTitle className="truncate text-xl text-slate-950">
                    {selectedCandidate?.name || 'Candidate'}
                  </DialogTitle>
                  {selectedCandidate?.status && <StatusBadge status={selectedCandidate.status} />}
                </div>
                <DialogDescription className="mt-1 truncate">
                  {selectedCandidate?.email || 'No email available'}
                </DialogDescription>
              </div>
            </div>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => onDownloadResume(selectedCandidate?.id)}
              disabled={!selectedCandidate?.id}
              className="self-start sm:self-auto"
            >
              <Download className="mr-2 h-4 w-4" aria-hidden="true" />
              Resume
            </Button>
          </div>
        </DialogHeader>

        {selectedCandidate && (
          <div className="space-y-8 px-6 py-6 sm:px-8">
            <section aria-labelledby="candidate-evidence-heading">
              <div className="mb-4 flex items-center gap-2">
                <FileText className="h-4 w-4 text-slate-500" aria-hidden="true" />
                <h3 id="candidate-evidence-heading" className="text-sm font-semibold text-slate-950">
                  Application evidence
                </h3>
              </div>
              <div className="grid gap-5 rounded-xl border border-slate-200 bg-white p-5 md:grid-cols-[12rem_1fr]">
                <div className="border-b border-slate-200 pb-5 md:border-b-0 md:border-r md:pb-0 md:pr-5">
                  <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">Role match</p>
                  <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-950 tabular-nums">
                    {Math.round(matchScore)}%
                  </p>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-slate-100">
                    <div className="h-full rounded-full bg-blue-600" style={{ width: `${matchScore}%` }} />
                  </div>
                  <div className="mt-4 border-t border-slate-200 pt-4">
                    <p className="text-xs text-slate-500">AI recommendation</p>
                    <p className="mt-1 text-sm font-semibold text-slate-950">
                      {selectedCandidate.aiRecommendation || 'Not available'}
                    </p>
                  </div>
                </div>
                <div className="grid gap-6 sm:grid-cols-2">
                  <div>
                    <p className="mb-3 text-sm font-medium text-slate-950">Strengths</p>
                    <InsightList
                      items={selectedCandidate.pros}
                      emptyLabel="No strengths were recorded by the matcher."
                      tone="positive"
                    />
                  </div>
                  <div>
                    <p className="mb-3 text-sm font-medium text-slate-950">Considerations</p>
                    <InsightList
                      items={selectedCandidate.cons}
                      emptyLabel="No considerations were recorded by the matcher."
                      tone="caution"
                    />
                  </div>
                </div>
              </div>
            </section>

            <section aria-labelledby="assessment-evidence-heading">
              <div className="mb-4 flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-slate-500" aria-hidden="true" />
                <h3 id="assessment-evidence-heading" className="text-sm font-semibold text-slate-950">
                  Assessment evidence
                </h3>
              </div>

              {assessmentDetails ? (
                <div className="grid gap-5 lg:grid-cols-[1fr_1.1fr]">
                  <div className="space-y-4 rounded-xl border border-slate-200 p-5">
                    <ScoreRow label="Overall" value={assessmentDetails.overall_score} />
                    <ScoreRow label="Technical" value={assessmentDetails.technical_score} />
                    <ScoreRow label="Psychometric" value={assessmentDetails.psychometric_score} />
                    <div className="grid grid-cols-2 gap-4 border-t border-slate-200 pt-4">
                      <div>
                        <p className="text-xs text-slate-500">MCQ</p>
                        <p className="mt-1 font-semibold tabular-nums text-slate-950">
                          {Math.round(clampScore(assessmentDetails.mcq_score))}%
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Coding</p>
                        <p className="mt-1 font-semibold tabular-nums text-slate-950">
                          {Math.round(clampScore(assessmentDetails.coding_score))}%
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50/70 p-5">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <p className="text-xs font-medium uppercase tracking-[0.12em] text-slate-500">
                        System recommendation
                      </p>
                      {assessmentDetails.automated_recommendation && (
                        <StatusBadge status={assessmentDetails.automated_recommendation} />
                      )}
                    </div>
                    <p className="text-sm leading-6 text-slate-700">
                      {assessmentDetails.automated_rationale || 'No automated rationale is available.'}
                    </p>
                    {assessmentDetails.recommended_next_step && (
                      <div className="border-t border-slate-200 pt-4">
                        <p className="text-xs font-medium text-slate-500">Recommended next step</p>
                        <p className="mt-1 text-sm leading-6 text-slate-700">
                          {assessmentDetails.recommended_next_step}
                        </p>
                      </div>
                    )}
                    <p className="text-xs leading-5 text-slate-500">
                      Use this as supporting evidence only. The final hiring decision remains with the reviewer.
                    </p>
                  </div>
                </div>
              ) : assessmentLoading ? (
                <div
                  className="flex items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 px-5 py-8 text-sm text-slate-500"
                  role="status"
                  aria-label="Loading assessment evidence"
                >
                  <LoaderCircle className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Loading assessment evidence
                </div>
              ) : (
                <div className="rounded-xl border border-dashed border-slate-300 px-5 py-8 text-center text-sm text-slate-500">
                  Assessment results are not available for this candidate yet.
                </div>
              )}
            </section>

            {assessmentDetails?.final_decision && (
              <section className="rounded-xl border border-slate-200 bg-slate-50 p-5" aria-labelledby="recorded-decision-heading">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 id="recorded-decision-heading" className="text-sm font-semibold text-slate-950">
                    Recorded final decision
                  </h3>
                  <StatusBadge status={assessmentDetails.final_decision} />
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-700">
                  {assessmentDetails.final_rationale || 'No reviewer rationale was recorded.'}
                </p>
              </section>
            )}

            {canMakeDecision && (
              <section className="border-t border-slate-200 pt-7" aria-labelledby="final-decision-heading">
                <div className="max-w-2xl">
                  <h3 id="final-decision-heading" className="text-base font-semibold text-slate-950">
                    Final hiring decision
                  </h3>
                  <p className="mt-1 text-sm leading-6 text-slate-500">
                    Record the reviewer rationale before closing the candidate. This action is final and may email the candidate.
                  </p>
                </div>

                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  <label className="space-y-2 text-sm font-medium text-slate-800">
                    Reviewer rationale
                    <textarea
                      value={rationale}
                      onChange={(event) => setRationale(event.target.value)}
                      maxLength={4000}
                      rows={4}
                      placeholder="Summarize the evidence behind this decision."
                      className="w-full resize-y rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm font-normal text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    />
                  </label>
                  <label className="space-y-2 text-sm font-medium text-slate-800">
                    Candidate next steps
                    <textarea
                      value={nextSteps}
                      onChange={(event) => setNextSteps(event.target.value)}
                      maxLength={4000}
                      rows={4}
                      placeholder="Optional instructions included in the decision email."
                      className="w-full resize-y rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm font-normal text-slate-950 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                    />
                  </label>
                </div>

                <DialogFooter className="mt-5 gap-2 sm:space-x-0">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => submitDecision('no-hire')}
                    disabled={decisionLoading}
                    className="border-red-200 text-red-700 hover:bg-red-50 hover:text-red-800"
                  >
                    {decisionLoading ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <X className="mr-2 h-4 w-4" />}
                    No hire
                  </Button>
                  <Button
                    type="button"
                    onClick={() => submitDecision('hire')}
                    disabled={decisionLoading}
                  >
                    {decisionLoading ? <LoaderCircle className="mr-2 h-4 w-4 animate-spin" /> : <Check className="mr-2 h-4 w-4" />}
                    Hire candidate
                  </Button>
                </DialogFooter>
              </section>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default CandidateDetailsModal;
