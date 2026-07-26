import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  Check,
  CheckCircle2,
  FileText,
  Loader2,
  LockKeyhole,
  MapPin,
  UploadCloud,
  X,
} from 'lucide-react';
import { Link, useLocation, useParams } from 'react-router-dom';

import Logo from '../components/Logo';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { api } from '../services/api';

const MAX_FILE_SIZE_MB = 10;
const MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024;
const ACCEPTED_EXTENSIONS = new Set(['pdf', 'docx']);

const ApplyPage = () => {
  const location = useLocation();
  const { jobId } = useParams();
  const fileInputRef = useRef(null);
  const [jobs, setJobs] = useState([]);
  const [jobsState, setJobsState] = useState('loading');
  const [selectedJobId, setSelectedJobId] = useState(jobId || String(location.state?.job?.id || ''));
  const [contact, setContact] = useState({ name: '', email: '', phone: '' });
  const [file, setFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [errors, setErrors] = useState({});
  const [uploadError, setUploadError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [receipt, setReceipt] = useState(null);

  useEffect(() => {
    let active = true;
    api.get('/api/jobs/postings?status=active')
      .then(({ data }) => {
        if (!active) return;
        const openJobs = data?.data || [];
        setJobs(openJobs);
        setJobsState('ready');
        if (jobId && !openJobs.some((job) => String(job.id) === String(jobId))) {
          setSelectedJobId('');
          setUploadError('That role is no longer open. Choose another position before submitting.');
        }
      })
      .catch(() => active && setJobsState('error'));
    return () => { active = false; };
  }, [jobId]);

  const selectedJob = useMemo(
    () => jobs.find((job) => String(job.id) === String(selectedJobId)) || location.state?.job || null,
    [jobs, location.state?.job, selectedJobId],
  );

  const chooseFile = (nextFile) => {
    if (!nextFile) return;
    const extension = nextFile.name.split('.').pop()?.toLowerCase();
    if (!ACCEPTED_EXTENSIONS.has(extension)) {
      setErrors((current) => ({ ...current, file: 'Choose a PDF or DOCX resume.' }));
      return;
    }
    if (nextFile.size > MAX_FILE_SIZE) {
      setErrors((current) => ({ ...current, file: `Resume files must be ${MAX_FILE_SIZE_MB} MB or smaller.` }));
      return;
    }
    setFile(nextFile);
    setErrors((current) => ({ ...current, file: '' }));
    setUploadError('');
  };

  const validate = () => {
    const nextErrors = {};
    if (!selectedJobId) nextErrors.job = 'Choose the position you are applying for.';
    if (!contact.name.trim()) nextErrors.name = 'Enter your full name.';
    if (!contact.email.trim()) nextErrors.email = 'Enter your email address.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(contact.email.trim())) nextErrors.email = 'Enter a valid email address.';
    if (!file) nextErrors.file = 'Attach your resume.';
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    setUploadError('');

    const form = new FormData();
    form.append('file', file);
    form.append('job_id', selectedJobId);
    form.append('name', contact.name.trim());
    form.append('email', contact.email.trim());
    if (contact.phone.trim()) form.append('phone', contact.phone.trim());

    try {
      const response = await api.post('/api/resume/upload', form);
      const data = response?.data?.data || {};
      setReceipt({
        name: contact.name.trim(),
        email: contact.email.trim(),
        jobTitle: data.selected_job?.title || selectedJob?.title,
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (error) {
      setUploadError(error?.response?.data?.message || 'The application could not be submitted. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (receipt) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background px-5 py-12">
        <div className="page-enter surface-card w-full max-w-xl rounded-2xl bg-card p-7 text-center sm:p-10">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-success"><CheckCircle2 className="h-7 w-7" /></div>
          <p className="eyebrow mt-7">Application received</p>
          <h1 className="display-face mt-3 text-4xl">Thank you, {receipt.name}.</h1>
          <p className="mx-auto mt-4 max-w-md leading-7 text-muted-foreground">Your application{receipt.jobTitle ? ` for ${receipt.jobTitle}` : ''} is safely in the hiring queue. The team will contact you at <span className="font-medium text-foreground">{receipt.email}</span> if the process moves forward.</p>
          <div className="mt-7 rounded-xl border bg-muted/45 p-4 text-left text-sm">
            <div className="flex gap-3"><Check className="mt-0.5 h-4 w-4 shrink-0 text-success" /><span>Your resume and application were stored successfully.</span></div>
            <div className="mt-3 flex gap-3"><LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-primary" /><span>Do not submit the same application again; updates should go through the recruiter.</span></div>
          </div>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Button asChild><Link to="/">Return home</Link></Button>
            <Button asChild variant="outline"><Link to="/jobs">View other roles</Link></Button>
          </div>
        </div>
      </main>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="page-wrap flex h-16 items-center justify-between">
          <Link to="/"><Logo /></Link>
          <Button asChild variant="ghost" size="sm"><Link to="/jobs"><ArrowLeft />Open roles</Link></Button>
        </div>
      </header>

      <main className="page-wrap grid gap-10 py-10 lg:grid-cols-[.68fr_1.32fr] lg:py-14">
        <aside className="lg:sticky lg:top-10 lg:h-fit">
          <p className="eyebrow">Candidate application</p>
          <h1 className="display-face mt-3 text-balance text-4xl sm:text-5xl">Tell us where your experience can make an impact.</h1>
          <p className="mt-5 max-w-md leading-7 text-muted-foreground">Choose one open role, provide reliable contact details, and attach the resume you want the hiring team to review.</p>
          <div className="mt-8 space-y-4 border-t pt-6 text-sm text-muted-foreground">
            <p className="flex gap-3"><LockKeyhole className="mt-0.5 h-4 w-4 shrink-0 text-primary" />Your resume is available only to authorized hiring staff.</p>
            <p className="flex gap-3"><Check className="mt-0.5 h-4 w-4 shrink-0 text-success" />Automated extraction supports review; people make the final hiring decision.</p>
          </div>
        </aside>

        <form onSubmit={handleSubmit} className="page-enter surface-card rounded-2xl bg-card p-5 sm:p-8" noValidate>
          <section className="border-b pb-8">
            <div className="mb-5 flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-sm font-semibold text-primary">1</span>
              <div><h2 className="text-lg font-semibold">Choose a role</h2><p className="text-sm text-muted-foreground">Applications are evaluated against a specific open position.</p></div>
            </div>
            {jobsState === 'loading' && <div className="flex h-10 items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" />Loading open positions…</div>}
            {jobsState === 'error' && <div role="alert" className="rounded-lg border border-destructive/25 bg-destructive/5 p-3 text-sm text-destructive">Open positions could not be loaded. Refresh before submitting.</div>}
            {jobsState === 'ready' && jobs.length === 0 && <div className="rounded-lg border bg-muted/40 p-4 text-sm text-muted-foreground">There are no active positions accepting applications right now.</div>}
            {jobs.length > 0 && (
              <Select value={selectedJobId} onValueChange={(value) => { setSelectedJobId(value); setErrors((current) => ({ ...current, job: '' })); }}>
                <SelectTrigger
                  aria-label="Open role"
                  aria-invalid={Boolean(errors.job)}
                  aria-describedby={errors.job ? 'job-error' : undefined}
                ><BriefcaseBusiness className="mr-2 h-4 w-4 text-muted-foreground" /><SelectValue placeholder="Select an open position" /></SelectTrigger>
                <SelectContent>{jobs.map((job) => <SelectItem key={job.id} value={String(job.id)}>{job.title}{job.work_mode ? ` · ${job.work_mode}` : ''}</SelectItem>)}</SelectContent>
              </Select>
            )}
            {errors.job && <p id="job-error" className="mt-2 text-sm text-destructive">{errors.job}</p>}
            {selectedJob && (
              <div className="mt-4 rounded-xl border bg-muted/35 p-4">
                <div className="flex flex-wrap items-center gap-2"><span className="font-semibold">{selectedJob.title}</span>{selectedJob.experience_level && <Badge variant="secondary" className="capitalize">{selectedJob.experience_level}</Badge>}</div>
                <div className="mt-2 flex flex-wrap gap-4 text-sm text-muted-foreground">{selectedJob.department && <span>{selectedJob.department}</span>}{selectedJob.work_mode && <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" />{selectedJob.work_mode}</span>}</div>
              </div>
            )}
          </section>

          <section className="border-b py-8">
            <div className="mb-5 flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-sm font-semibold text-primary">2</span>
              <div><h2 className="text-lg font-semibold">Contact details</h2><p className="text-sm text-muted-foreground">We use these details for application communication.</p></div>
            </div>
            <div className="grid gap-5 sm:grid-cols-2">
              <div className="space-y-2 sm:col-span-2"><Label htmlFor="name">Full name</Label><Input id="name" value={contact.name} onChange={(event) => setContact((current) => ({ ...current, name: event.target.value }))} autoComplete="name" aria-invalid={Boolean(errors.name)} aria-describedby={errors.name ? 'name-error' : undefined} />{errors.name && <p id="name-error" className="text-sm text-destructive">{errors.name}</p>}</div>
              <div className="space-y-2"><Label htmlFor="email">Email address</Label><Input id="email" type="email" value={contact.email} onChange={(event) => setContact((current) => ({ ...current, email: event.target.value }))} autoComplete="email" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? 'email-error' : undefined} />{errors.email && <p id="email-error" className="text-sm text-destructive">{errors.email}</p>}</div>
              <div className="space-y-2"><Label htmlFor="phone">Phone <span className="font-normal text-muted-foreground">(optional)</span></Label><Input id="phone" type="tel" value={contact.phone} onChange={(event) => setContact((current) => ({ ...current, phone: event.target.value }))} autoComplete="tel" /></div>
            </div>
          </section>

          <section className="pt-8">
            <div className="mb-5 flex items-center gap-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-sm font-semibold text-primary">3</span>
              <div><h2 className="text-lg font-semibold">Attach your resume</h2><p className="text-sm text-muted-foreground">PDF or DOCX · maximum {MAX_FILE_SIZE_MB} MB.</p></div>
            </div>
            <div
              onDragEnter={(event) => { event.preventDefault(); setDragActive(true); }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={(event) => { event.preventDefault(); setDragActive(false); }}
              onDrop={(event) => { event.preventDefault(); setDragActive(false); chooseFile(event.dataTransfer.files?.[0]); }}
              className={`rounded-xl border border-dashed p-5 transition-colors ${dragActive ? 'border-primary bg-accent' : errors.file ? 'border-destructive bg-destructive/5' : 'border-input bg-muted/25'}`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                className="sr-only"
                aria-label="Resume file"
                aria-invalid={Boolean(errors.file)}
                aria-describedby={errors.file ? 'resume-error' : undefined}
                onChange={(event) => chooseFile(event.target.files?.[0])}
              />
              {file ? (
                <div className="flex items-center gap-4">
                  <span className="flex h-11 w-11 items-center justify-center rounded-lg bg-card text-primary shadow-sm"><FileText className="h-5 w-5" /></span>
                  <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{file.name}</p><p className="mt-0.5 text-xs text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p></div>
                  <Button type="button" variant="ghost" size="icon" onClick={() => { setFile(null); if (fileInputRef.current) fileInputRef.current.value = ''; }} aria-label="Remove resume"><X /></Button>
                </div>
              ) : (
                <button type="button" onClick={() => fileInputRef.current?.click()} className="flex w-full flex-col items-center py-5 text-center">
                  <UploadCloud className="h-7 w-7 text-primary" />
                  <span className="mt-3 text-sm font-semibold">Drop your resume here or choose a file</span>
                  <span className="mt-1 text-xs text-muted-foreground">The server validates the document before it is accepted.</span>
                </button>
              )}
            </div>
            {errors.file && <p id="resume-error" className="mt-2 text-sm text-destructive">{errors.file}</p>}

            {uploadError && <div role="alert" className="mt-5 rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-sm text-destructive">{uploadError}</div>}

            <div className="mt-6 rounded-lg border bg-muted/30 p-4 text-sm leading-6 text-muted-foreground">
              By submitting, you confirm the information is yours to share and acknowledge the <Link to="/privacy" className="font-medium text-primary hover:underline">candidate privacy notice</Link>.
            </div>

            <Button type="submit" size="lg" className="mt-6 w-full sm:w-auto" disabled={submitting || jobsState !== 'ready' || jobs.length === 0}>
              {submitting ? <><Loader2 className="animate-spin" />Submitting securely…</> : <>Submit application <ArrowRight /></>}
            </Button>
          </section>
        </form>
      </main>
    </div>
  );
};

export default ApplyPage;
