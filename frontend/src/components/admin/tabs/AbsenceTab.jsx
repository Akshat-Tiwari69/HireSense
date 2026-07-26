import { Badge } from '../../ui/badge';
import { Button } from '../../ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../ui/card';
import { Input } from '../../ui/input';
import { Label } from '../../ui/label';
import { TabsContent } from '../../ui/tabs';
import { AlertTriangle, Check, CheckCircle2, Edit, Loader2, RefreshCw, Trash2 } from 'lucide-react';

const AbsenceTab = ({
  absenceCandidates,
  absenceLoading,
  absenceEditing,
  absenceForm,
  setAbsenceForm,
  absenceSaving,
  fetchAbsenceCandidates,
  startEditAbsence,
  cancelEditAbsence,
  saveAbsenceDetails,
  handleDeleteCandidate,
}) => (
  <TabsContent value="absence-details">
    <Card>
      <CardHeader className="gap-4 border-b sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-700">
              <AlertTriangle className="h-4 w-4" />
            </span>
            <CardTitle>Missing candidate details</CardTitle>
            <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700">
              {absenceCandidates.length}
            </Badge>
          </div>
          <CardDescription>
            Complete critical contact details before moving imported candidates into the active pipeline.
          </CardDescription>
        </div>
        <Button type="button" variant="outline" onClick={fetchAbsenceCandidates} disabled={absenceLoading}>
          <RefreshCw className={absenceLoading ? 'animate-spin' : ''} />
          Refresh
        </Button>
      </CardHeader>

      <CardContent className="pt-5">
        {absenceLoading ? (
          <div className="flex min-h-56 items-center justify-center text-muted-foreground" role="status">
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Loading candidate records
          </div>
        ) : absenceCandidates.length === 0 ? (
          <div className="flex min-h-56 flex-col items-center justify-center rounded-lg border border-dashed px-6 text-center">
            <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
              <CheckCircle2 className="h-5 w-5" />
            </span>
            <p className="font-medium text-foreground">All candidate records are complete</p>
            <p className="mt-1 text-sm text-muted-foreground">New imports with missing information will appear here.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {absenceCandidates.map((candidate) => {
              const isEditing = absenceEditing === candidate.id;
              const candidateName = candidate.name || 'Name unavailable';

              return (
                <article key={candidate.id} className="rounded-xl border bg-card p-4 sm:p-5">
                  {isEditing ? (
                    <div className="space-y-4">
                      <div>
                        <p className="font-medium text-foreground">Complete candidate record</p>
                        <p className="mt-1 text-sm text-muted-foreground">Candidate ID {candidate.id}</p>
                      </div>
                      <div className="grid gap-4 md:grid-cols-3">
                        <div className="space-y-2">
                          <Label htmlFor={`absence-name-${candidate.id}`}>Name <span aria-hidden="true">*</span></Label>
                          <Input
                            id={`absence-name-${candidate.id}`}
                            value={absenceForm.name}
                            onChange={(event) => setAbsenceForm((form) => ({ ...form, name: event.target.value }))}
                            placeholder="Full name"
                            required
                            aria-required="true"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`absence-email-${candidate.id}`}>Email <span aria-hidden="true">*</span></Label>
                          <Input
                            id={`absence-email-${candidate.id}`}
                            type="email"
                            value={absenceForm.email}
                            onChange={(event) => setAbsenceForm((form) => ({ ...form, email: event.target.value }))}
                            placeholder="candidate@example.com"
                            required
                            aria-required="true"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor={`absence-phone-${candidate.id}`}>Phone</Label>
                          <Input
                            id={`absence-phone-${candidate.id}`}
                            type="tel"
                            value={absenceForm.phone}
                            onChange={(event) => setAbsenceForm((form) => ({ ...form, phone: event.target.value }))}
                            placeholder="+91 98765 43210"
                          />
                        </div>
                      </div>
                      <div className="flex flex-col-reverse gap-2 sm:flex-row">
                        <Button type="button" variant="outline" onClick={cancelEditAbsence}>Cancel</Button>
                        <Button
                          type="button"
                          onClick={() => saveAbsenceDetails(candidate.id)}
                          disabled={absenceSaving}
                          className="bg-emerald-700 hover:bg-emerald-800"
                        >
                          {absenceSaving ? <Loader2 className="animate-spin" /> : <Check />}
                          Save and mark applied
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                      <div className="min-w-0 space-y-3">
                        <div>
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="font-semibold text-foreground">{candidateName}</h3>
                            {candidate.job_title && candidate.job_title !== 'N/A' ? (
                              <Badge variant="outline" className="border-slate-200 bg-slate-50 text-slate-700">
                                {candidate.job_title}
                              </Badge>
                            ) : null}
                          </div>
                          <p className="mt-1 break-all text-sm text-muted-foreground">
                            {candidate.email || 'Email unavailable'} · Candidate ID {candidate.id}
                          </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-xs font-semibold uppercase tracking-[0.08em] text-amber-700">Missing</span>
                          {(candidate.missing_fields || []).map((field) => (
                            <Badge key={field} variant="outline" className="border-amber-200 bg-amber-50 text-amber-700 capitalize">
                              {field}
                            </Badge>
                          ))}
                          {candidate.created_at ? (
                            <span className="text-xs text-muted-foreground">
                              Imported {new Date(candidate.created_at).toLocaleDateString()}
                            </span>
                          ) : null}
                        </div>
                      </div>
                      <div className="flex shrink-0 flex-wrap gap-2">
                        <Button type="button" variant="outline" onClick={() => startEditAbsence(candidate)}>
                          <Edit />
                          Complete details
                        </Button>
                        <Button
                          type="button"
                          variant="ghost"
                          onClick={() => handleDeleteCandidate(candidate.id)}
                          className="text-red-600 hover:bg-red-50 hover:text-red-700"
                          aria-label={`Delete ${candidateName}`}
                        >
                          <Trash2 />
                          Delete
                        </Button>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  </TabsContent>
);

export default AbsenceTab;
