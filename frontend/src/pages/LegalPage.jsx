import { ArrowLeft, FileCheck2, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

import Logo from '../components/Logo';
import { Button } from '../components/ui/button';

const privacySections = [
  ['What we process', 'When you apply, the hiring organization may process your resume, contact details, employment history, education, skills, assessment answers, scores, and security events produced during a proctored assessment.'],
  ['Why it is processed', 'The information is used to review your application, match you to a role, administer an assessment, protect assessment integrity, communicate decisions, and maintain an auditable hiring process.'],
  ['Automated assistance', 'Configured AI services may help extract resume details, compare qualifications, or prepare assessment material. Their output supports—not replaces—review by authorized hiring staff.'],
  ['Who can access it', 'Access is limited by role to authorized administrators, interviewers, and proctors. Assessment evidence is served through authenticated, assignment-checked endpoints rather than public file links.'],
  ['Retention and your choices', 'Retention and deletion periods are set by the organization running this deployment. To request access, correction, deletion, or information about its providers, contact the recruiter or privacy contact named in the original job posting.'],
];

const termsSections = [
  ['Using the service', 'Provide accurate information, submit only files you are entitled to share, and use assessment access links only for the candidate to whom they were issued.'],
  ['Assessment integrity', 'Do not share questions, impersonate another person, interfere with monitoring, or attempt to bypass time and access controls. Proctored sessions may record declared browser and camera evidence for authorized human review.'],
  ['Hiring decisions', 'Scores, matches, and recommendations are decision-support signals. Employment decisions remain with the hiring organization and are subject to its policies and applicable law.'],
  ['Availability', 'The service may be interrupted for maintenance or by external providers. If a technical issue affects an assessment, contact the recruiter rather than repeatedly submitting the session.'],
  ['Organization-specific terms', 'The organization operating this deployment is responsible for publishing any additional employment, regional, or contractual terms that apply to its candidates.'],
];

const LegalPage = ({ document }) => {
  const isPrivacy = document === 'privacy';
  const title = isPrivacy ? 'Candidate privacy notice' : 'Platform terms';
  const sections = isPrivacy ? privacySections : termsSections;
  const Icon = isPrivacy ? ShieldCheck : FileCheck2;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card/90 backdrop-blur">
        <div className="page-wrap flex h-16 items-center justify-between">
          <Link to="/" aria-label="HireSense home"><Logo /></Link>
          <Button asChild variant="ghost" size="sm">
            <Link to="/"><ArrowLeft />Back to home</Link>
          </Button>
        </div>
      </header>

      <main className="page-wrap py-12 sm:py-16">
        <article className="page-enter mx-auto max-w-3xl">
          <div className="mb-10 border-b pb-8">
            <div className="mb-5 inline-flex h-11 w-11 items-center justify-center rounded-xl bg-accent text-primary">
              <Icon className="h-5 w-5" />
            </div>
            <p className="eyebrow">HireSense candidate information</p>
            <h1 className="display-face mt-3 text-4xl text-foreground sm:text-5xl">{title}</h1>
            <p className="mt-4 max-w-2xl text-muted-foreground">
              Effective 15 July 2026. This notice describes the platform’s default behavior;
              the organization running this deployment remains responsible for its hiring policy.
            </p>
          </div>

          <div className="space-y-9">
            {sections.map(([heading, body]) => (
              <section key={heading}>
                <h2 className="text-lg font-semibold tracking-tight">{heading}</h2>
                <p className="mt-2 leading-7 text-muted-foreground">{body}</p>
              </section>
            ))}
          </div>
        </article>
      </main>
    </div>
  );
};

export default LegalPage;
