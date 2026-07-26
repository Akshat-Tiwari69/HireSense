import {
  ArrowRight,
  BarChart3,
  Check,
  ClipboardCheck,
  FileSearch,
  LockKeyhole,
  ScanSearch,
  ShieldCheck,
  Sparkles,
  UsersRound,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import Logo from '../components/Logo';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';

const workflow = [
  {
    number: '01',
    icon: FileSearch,
    title: 'Bring applicants into focus',
    description: 'Collect resumes against a live role and turn unstructured experience into a reviewable candidate profile.',
  },
  {
    number: '02',
    icon: ScanSearch,
    title: 'Review evidence, not noise',
    description: 'See fit signals, gaps, resume evidence, and the next required action in one consistent workspace.',
  },
  {
    number: '03',
    icon: ClipboardCheck,
    title: 'Assess with a clear trail',
    description: 'Schedule role-aware assessments, preserve responses, and keep automated guidance separate from human decisions.',
  },
];

const principles = [
  {
    icon: UsersRound,
    title: 'One hiring workflow',
    description: 'Admin, interviewer, proctor, and candidate experiences operate on the same lifecycle and vocabulary.',
  },
  {
    icon: ShieldCheck,
    title: 'Human review stays visible',
    description: 'Automated recommendations remain decision support. Final outcomes are explicit, attributable human actions.',
  },
  {
    icon: BarChart3,
    title: 'Signal with context',
    description: 'Scores sit beside stage, evidence, ownership, and timing—never as an unexplained number in isolation.',
  },
];

const LandingPage = () => (
  <div className="min-h-screen bg-background text-foreground">
    <section className="relative isolate overflow-hidden bg-[#0b1220] text-white">
      <div
        aria-hidden="true"
        className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(148,163,184,.09)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,.09)_1px,transparent_1px)] [background-size:40px_40px]"
      />
      <div aria-hidden="true" className="absolute left-1/2 top-0 h-[520px] w-[760px] -translate-x-1/2 rounded-full bg-primary/20 blur-[140px]" />

      <header className="relative z-10 border-b border-white/10">
        <div className="page-wrap flex h-[72px] items-center justify-between">
          <Link to="/" aria-label="HireSense home"><Logo className="text-white" /></Link>
          <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex" aria-label="Primary navigation">
            <a href="#workflow" className="transition-colors hover:text-white">Workflow</a>
            <a href="#principles" className="transition-colors hover:text-white">Platform</a>
            <Link to="/jobs" className="transition-colors hover:text-white">Open roles</Link>
          </nav>
          <div className="flex items-center gap-2">
            <Button asChild variant="ghost" className="hidden text-slate-200 hover:bg-white/10 hover:text-white sm:inline-flex">
              <Link to="/login">Staff sign in</Link>
            </Button>
            <Button asChild className="bg-white text-slate-950 hover:bg-slate-100">
              <Link to="/jobs">View roles <ArrowRight /></Link>
            </Button>
          </div>
        </div>
      </header>

      <div className="page-wrap relative z-10 grid items-center gap-14 py-20 lg:grid-cols-[1.02fr_.98fr] lg:py-28">
        <div className="page-enter max-w-3xl">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.06] px-3 py-1.5 text-xs font-medium text-slate-200">
            <Sparkles className="h-3.5 w-3.5 text-blue-300" />
            Structured hiring, without the system noise
          </div>
          <h1 className="display-face text-balance text-5xl leading-[1.02] sm:text-6xl lg:text-[4.75rem]">
            A calmer way to make consequential hires.
          </h1>
          <p className="mt-7 max-w-2xl text-balance text-lg leading-8 text-slate-300 sm:text-xl">
            HireSense brings applications, assessments, evidence, and final decisions into one secure hiring workspace—so teams can move quickly without losing judgment.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Button asChild size="lg" className="bg-primary text-white">
              <Link to="/jobs">Explore open roles <ArrowRight /></Link>
            </Button>
            <Button asChild size="lg" variant="outline" className="border-white/20 bg-white/[0.04] text-white hover:border-white/30 hover:bg-white/10 hover:text-white">
              <Link to="/apply">Submit a resume</Link>
            </Button>
          </div>
          <div className="mt-9 flex flex-wrap gap-x-6 gap-y-3 text-sm text-slate-400">
            {['Role-aware access', 'Auditable decisions', 'Candidate-first assessment'].map((item) => (
              <span key={item} className="inline-flex items-center gap-2"><Check className="h-4 w-4 text-emerald-400" />{item}</span>
            ))}
          </div>
        </div>

        <div className="page-enter relative mx-auto w-full max-w-[620px] [animation-delay:100ms]">
          <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-950/70 shadow-2xl shadow-black/30 backdrop-blur">
            <div className="flex items-center justify-between border-b border-white/10 px-5 py-4">
              <div>
                <p className="text-sm font-semibold">Engineering pipeline</p>
                <p className="mt-0.5 text-xs text-slate-400">Evidence review · 12 candidates</p>
              </div>
              <Badge className="border-emerald-400/20 bg-emerald-400/10 text-emerald-300">Live</Badge>
            </div>
            <div className="grid gap-3 p-4 sm:grid-cols-[1.1fr_.9fr]">
              <div className="space-y-2">
                {[
                  ['Maya Rao', 'Assessment complete', '88'],
                  ['Daniel Chen', 'Review resume', '82'],
                  ['Noah Williams', 'Scheduled today', '76'],
                ].map(([name, stage, score], index) => (
                  <div key={name} className={`rounded-xl border p-3.5 ${index === 0 ? 'border-blue-400/40 bg-blue-400/10' : 'border-white/10 bg-white/[0.035]'}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/10 text-xs font-semibold">{name.split(' ').map((part) => part[0]).join('')}</span>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-medium">{name}</p>
                          <p className="mt-0.5 truncate text-xs text-slate-400">{stage}</p>
                        </div>
                      </div>
                      <span className="text-sm font-semibold text-blue-300">{score}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="rounded-xl border border-white/10 bg-white/[0.035] p-4">
                <p className="text-xs font-semibold uppercase tracking-[.14em] text-slate-400">Review brief</p>
                <p className="mt-3 text-base font-semibold">Maya Rao</p>
                <div className="mt-5 space-y-4">
                  {[
                    ['Role match', '88%'],
                    ['Assessment', '84%'],
                    ['Integrity review', 'Clear'],
                  ].map(([label, value]) => (
                    <div key={label} className="flex items-center justify-between border-b border-white/10 pb-3 text-sm last:border-0">
                      <span className="text-slate-400">{label}</span><span className="font-medium">{value}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-5 rounded-lg bg-white/[0.06] p-3 text-xs leading-5 text-slate-300">
                  Strong systems experience. Review architecture depth before final decision.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <main>
      <section id="workflow" className="border-b bg-card py-20 sm:py-24">
        <div className="page-wrap">
          <div className="max-w-2xl">
            <p className="eyebrow">A deliberate workflow</p>
            <h2 className="display-face mt-3 text-balance text-4xl sm:text-5xl">Keep the evidence connected from application to outcome.</h2>
            <p className="mt-5 text-lg leading-8 text-muted-foreground">Every stage answers the same question: what does the team need to review or do next?</p>
          </div>
          <div className="mt-12 grid gap-px overflow-hidden rounded-xl border bg-border lg:grid-cols-3">
            {workflow.map(({ number, icon: Icon, title, description }) => (
              <article key={number} className="bg-card p-7 sm:p-8">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold tracking-[.14em] text-muted-foreground">{number}</span>
                  <Icon className="h-5 w-5 text-primary" />
                </div>
                <h3 className="mt-10 text-xl font-semibold tracking-tight">{title}</h3>
                <p className="mt-3 leading-7 text-muted-foreground">{description}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="principles" className="py-20 sm:py-24">
        <div className="page-wrap grid gap-12 lg:grid-cols-[.78fr_1.22fr] lg:items-start">
          <div className="lg:sticky lg:top-10">
            <p className="eyebrow">Built for hiring work</p>
            <h2 className="display-face mt-3 text-balance text-4xl sm:text-5xl">Professional software should make judgment clearer.</h2>
            <p className="mt-5 max-w-xl text-lg leading-8 text-muted-foreground">The interface stays quiet until a status, risk, or decision needs attention. No decorative dashboards. No mystery automation.</p>
          </div>
          <div className="space-y-4">
            {principles.map(({ icon: Icon, title, description }) => (
              <article key={title} className="surface-card grid gap-5 rounded-xl p-6 sm:grid-cols-[auto_1fr] sm:p-7">
                <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-accent text-primary"><Icon className="h-5 w-5" /></div>
                <div>
                  <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
                  <p className="mt-2 leading-7 text-muted-foreground">{description}</p>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="border-y bg-card py-20 sm:py-24">
        <div className="page-wrap grid gap-10 lg:grid-cols-2 lg:items-center">
          <div className="rounded-2xl bg-[#0b1220] p-7 text-white sm:p-10">
            <LockKeyhole className="h-6 w-6 text-blue-300" />
            <p className="mt-12 text-xs font-semibold uppercase tracking-[.16em] text-blue-300">Candidate trust</p>
            <blockquote className="display-face mt-4 text-3xl leading-tight sm:text-4xl">“Explain what is collected. Protect it by default. Let people focus on the work.”</blockquote>
          </div>
          <div className="max-w-xl lg:pl-8">
            <h2 className="text-2xl font-semibold tracking-tight">Assessment integrity without hostile design</h2>
            <p className="mt-4 leading-7 text-muted-foreground">Candidates see what monitoring is active before they begin. Browser and camera evidence is treated as a review signal, not an automatic verdict, and is available only to assigned staff.</p>
            <Button asChild variant="outline" className="mt-7">
              <Link to="/privacy">Read the candidate privacy notice <ArrowRight /></Link>
            </Button>
          </div>
        </div>
      </section>

      <section className="py-20 sm:py-24">
        <div className="page-wrap">
          <div className="overflow-hidden rounded-2xl bg-primary px-6 py-12 text-primary-foreground sm:px-12 sm:py-14 lg:flex lg:items-center lg:justify-between">
            <div className="max-w-2xl">
              <p className="text-sm font-semibold text-blue-100">Your next role may already be here.</p>
              <h2 className="display-face mt-3 text-4xl sm:text-5xl">Start with the work that fits you.</h2>
            </div>
            <Button asChild size="lg" className="mt-8 bg-white text-slate-950 hover:bg-blue-50 lg:mt-0">
              <Link to="/jobs">Browse open roles <ArrowRight /></Link>
            </Button>
          </div>
        </div>
      </section>
    </main>

    <footer className="border-t bg-card">
      <div className="page-wrap flex flex-col gap-6 py-8 sm:flex-row sm:items-center sm:justify-between">
        <Logo />
        <nav className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground" aria-label="Footer navigation">
          <Link to="/jobs" className="hover:text-foreground">Open roles</Link>
          <Link to="/privacy" className="hover:text-foreground">Privacy</Link>
          <Link to="/terms" className="hover:text-foreground">Terms</Link>
          <Link to="/login" className="hover:text-foreground">Staff sign in</Link>
        </nav>
      </div>
    </footer>
  </div>
);

export default LandingPage;
