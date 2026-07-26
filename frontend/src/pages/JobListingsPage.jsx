import { useEffect, useMemo, useState } from 'react';
import {
  ArrowLeft,
  ArrowRight,
  Banknote,
  BriefcaseBusiness,
  Building2,
  Clock3,
  GraduationCap,
  MapPin,
  RotateCw,
  Search,
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import Logo from '../components/Logo';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { api } from '../services/api';

const asSkills = (job, key) => {
  const existing = job?.[`${key}_list`];
  if (Array.isArray(existing)) return existing.filter(Boolean);
  return String(job?.[key] || '').split(/[,\n]/).map((skill) => skill.trim()).filter(Boolean);
};

const JobListingsPage = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState([]);
  const [sectors, setSectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [sectorFilter, setSectorFilter] = useState('all');
  const [levelFilter, setLevelFilter] = useState('all');
  const [selectedJob, setSelectedJob] = useState(null);

  const loadJobs = async () => {
    setLoading(true);
    setLoadError('');
    const [jobsResult, sectorsResult] = await Promise.allSettled([
      api.get('/api/jobs/postings?status=active'),
      api.get('/api/jobs/sectors'),
    ]);
    if (jobsResult.status === 'fulfilled') setJobs(jobsResult.value.data.data || []);
    else setLoadError('Open positions could not be loaded.');
    if (sectorsResult.status === 'fulfilled') setSectors(sectorsResult.value.data.data || []);
    setLoading(false);
  };

  useEffect(() => { loadJobs(); }, []);

  const filteredJobs = useMemo(() => {
    const query = search.trim().toLowerCase();
    return jobs.filter((job) => {
      const searchable = [job.title, job.department, job.work_mode, job.required_skills].join(' ').toLowerCase();
      return (!query || searchable.includes(query))
        && (sectorFilter === 'all' || String(job.sector_id) === sectorFilter)
        && (levelFilter === 'all' || job.experience_level === levelFilter);
    });
  }, [jobs, levelFilter, search, sectorFilter]);

  const applyTo = (job) => navigate(job ? `/apply/${job.id}` : '/apply', { state: job ? { job } : undefined });

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-40 border-b bg-card/90 backdrop-blur-md">
        <div className="page-wrap flex h-16 items-center justify-between">
          <Link to="/"><Logo /></Link>
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" className="hidden sm:inline-flex"><Link to="/"><ArrowLeft />Home</Link></Button>
            <Button onClick={() => applyTo(null)}>General application <ArrowRight /></Button>
          </div>
        </div>
      </header>

      <main>
        <section className="border-b bg-card">
          <div className="page-wrap py-14 sm:py-20">
            <div className="page-enter max-w-3xl">
              <p className="eyebrow">Open opportunities</p>
              <h1 className="display-face mt-3 text-balance text-5xl sm:text-6xl">Find work worth doing.</h1>
              <p className="mt-5 max-w-2xl text-lg leading-8 text-muted-foreground">Explore current roles, review the requirements, and apply directly to the position that matches your experience.</p>
            </div>
          </div>
        </section>

        <section className="page-wrap py-8 sm:py-10">
          <div className="surface-card grid gap-3 rounded-xl p-3 md:grid-cols-[minmax(0,1fr)_220px_190px]">
            <label className="relative block">
              <span className="sr-only">Search roles</span>
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search role, skill, or work mode" className="pl-9" />
            </label>
            <Select value={sectorFilter} onValueChange={setSectorFilter}>
              <SelectTrigger><Building2 className="mr-2 h-4 w-4 text-muted-foreground" /><SelectValue placeholder="All sectors" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All sectors</SelectItem>
                {sectors.map((sector) => <SelectItem key={sector.id} value={String(sector.id)}>{sector.name}</SelectItem>)}
              </SelectContent>
            </Select>
            <Select value={levelFilter} onValueChange={setLevelFilter}>
              <SelectTrigger><GraduationCap className="mr-2 h-4 w-4 text-muted-foreground" /><SelectValue placeholder="All levels" /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All levels</SelectItem>
                {['junior', 'mid', 'senior', 'lead', 'principal'].map((level) => <SelectItem key={level} value={level}>{level[0].toUpperCase() + level.slice(1)}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>

          <div className="mb-4 mt-7 flex items-center justify-between">
            <p className="text-sm text-muted-foreground" aria-live="polite">
              {loading ? 'Loading positions…' : loadError || `${filteredJobs.length} open ${filteredJobs.length === 1 ? 'position' : 'positions'}`}
            </p>
          </div>

          {loading && (
            <div className="space-y-3" aria-label="Loading positions">
              {[0, 1, 2].map((item) => <div key={item} className="h-40 animate-pulse rounded-xl border bg-card" />)}
            </div>
          )}

          {!loading && loadError && (
            <div role="alert" className="surface-card rounded-xl px-6 py-14 text-center">
              <RotateCw className="mx-auto h-6 w-6 text-muted-foreground" />
              <h2 className="mt-4 text-lg font-semibold">Positions are temporarily unavailable</h2>
              <p className="mt-2 text-muted-foreground">Nothing has been submitted. Please retry when the service is available.</p>
              <Button onClick={loadJobs} variant="outline" className="mt-6"><RotateCw />Try again</Button>
            </div>
          )}

          {!loading && !loadError && filteredJobs.length === 0 && (
            <div className="surface-card rounded-xl px-6 py-14 text-center">
              <BriefcaseBusiness className="mx-auto h-6 w-6 text-muted-foreground" />
              <h2 className="mt-4 text-lg font-semibold">No roles match those filters</h2>
              <p className="mt-2 text-muted-foreground">Try a broader search, or send a general application.</p>
              <Button onClick={() => { setSearch(''); setSectorFilter('all'); setLevelFilter('all'); }} variant="outline" className="mt-6">Clear filters</Button>
            </div>
          )}

          {!loading && !loadError && (
            <div className="space-y-3">
              {filteredJobs.map((job) => {
                const skills = asSkills(job, 'required_skills').slice(0, 5);
                return (
                  <article key={job.id} className="surface-card rounded-xl p-5 transition-[border-color,box-shadow,transform] hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-[0_10px_30px_rgba(15,23,42,.07)] sm:p-6">
                    <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-start">
                      <button type="button" onClick={() => setSelectedJob(job)} className="min-w-0 text-left focus-visible:rounded-lg">
                        <div className="flex flex-wrap items-center gap-2">
                          <h2 className="text-xl font-semibold tracking-tight sm:text-2xl">{job.title}</h2>
                          <Badge variant="secondary" className="capitalize">{job.experience_level || 'mid'}</Badge>
                          {job.employment_type && <Badge variant="outline" className="capitalize">{job.employment_type.replace('-', ' ')}</Badge>}
                        </div>
                        <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-muted-foreground">
                          {job.department && <span className="inline-flex items-center gap-1.5"><BriefcaseBusiness className="h-4 w-4" />{job.department}</span>}
                          {job.work_mode && <span className="inline-flex items-center gap-1.5"><MapPin className="h-4 w-4" />{job.work_mode}</span>}
                          <span className="inline-flex items-center gap-1.5"><Clock3 className="h-4 w-4" />{job.min_experience || 0}{job.max_experience ? `–${job.max_experience}` : '+'} years</span>
                          {job.salary_range && <span className="inline-flex items-center gap-1.5"><Banknote className="h-4 w-4" />{job.salary_range}</span>}
                        </div>
                        {job.description && <p className="mt-4 line-clamp-2 max-w-4xl leading-7 text-muted-foreground">{job.description}</p>}
                        {skills.length > 0 && <div className="mt-4 flex flex-wrap gap-2">{skills.map((skill) => <Badge key={skill} variant="outline" className="font-normal">{skill}</Badge>)}</div>}
                      </button>
                      <Button onClick={() => applyTo(job)} className="w-full lg:w-auto">Apply to this role <ArrowRight /></Button>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>
      </main>

      <Dialog open={Boolean(selectedJob)} onOpenChange={(open) => !open && setSelectedJob(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="pr-8 text-2xl">{selectedJob?.title}</DialogTitle>
            <DialogDescription>{[selectedJob?.department, selectedJob?.work_mode].filter(Boolean).join(' · ')}</DialogDescription>
          </DialogHeader>
          {selectedJob && (
            <div className="space-y-6">
              <p className="whitespace-pre-line leading-7 text-muted-foreground">{selectedJob.description || 'Role details will be discussed during the hiring process.'}</p>
              {asSkills(selectedJob, 'required_skills').length > 0 && (
                <div><h3 className="text-sm font-semibold">Required skills</h3><div className="mt-3 flex flex-wrap gap-2">{asSkills(selectedJob, 'required_skills').map((skill) => <Badge key={skill} variant="outline">{skill}</Badge>)}</div></div>
              )}
              <Button onClick={() => applyTo(selectedJob)} size="lg" className="w-full sm:w-auto">Apply to this role <ArrowRight /></Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default JobListingsPage;
