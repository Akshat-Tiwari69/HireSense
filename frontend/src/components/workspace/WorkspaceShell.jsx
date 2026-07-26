import { LogOut, RefreshCw, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

import Logo from '../Logo';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';

const roleLabels = {
  admin: 'Admin workspace',
  interviewer: 'Interviewer workspace',
  proctor: 'Proctor workspace',
  recruiter: 'Recruiter workspace',
  sector_admin: 'Sector admin workspace',
  super_admin: 'Super admin workspace',
};

const WorkspaceShell = ({
  role,
  title,
  description,
  user,
  onRefresh,
  refreshing = false,
  onSignOut,
  children,
}) => (
  <div className="min-h-screen bg-background lg:grid lg:grid-cols-[240px_minmax(0,1fr)]">
    <aside className="hidden min-h-screen border-r bg-[#111827] text-white lg:flex lg:flex-col">
      <div className="border-b border-white/10 px-5 py-5">
        <Link to="/" className="inline-flex"><Logo className="text-white" /></Link>
      </div>
      <div className="flex-1 px-4 py-6">
        <p className="px-2 text-[11px] font-semibold uppercase tracking-[.16em] text-slate-500">Current workspace</p>
        <div className="mt-3 rounded-lg bg-white/[0.07] px-3 py-3">
          <div className="flex items-center gap-3">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-white"><ShieldCheck className="h-4 w-4" /></span>
            <div><p className="text-sm font-medium">{roleLabels[role]}</p><p className="mt-0.5 text-xs text-slate-400">Role-scoped access</p></div>
          </div>
        </div>
        <div className="mt-8 border-t border-white/10 px-2 pt-6 text-xs leading-5 text-slate-500">
          Candidate data and actions shown here are limited by your server-verified role and assignment.
        </div>
      </div>
      <div className="border-t border-white/10 p-4">
        <div className="mb-3 min-w-0 px-2">
          <p className="truncate text-sm font-medium text-slate-200">{user?.name || 'HireSense staff'}</p>
          <p className="truncate text-xs text-slate-500">{user?.email || roleLabels[role]}</p>
        </div>
        <Button variant="ghost" onClick={onSignOut} className="w-full justify-start text-slate-300 hover:bg-white/10 hover:text-white"><LogOut aria-hidden="true" />Sign out</Button>
      </div>
    </aside>

    <div className="min-w-0">
      <header className="sticky top-0 z-40 border-b bg-card/90 backdrop-blur-md">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
          <div className="lg:hidden"><Logo size="small" /></div>
          <Badge variant="outline" className="hidden capitalize sm:inline-flex lg:hidden">{role}</Badge>
          <div className="ml-auto flex items-center gap-2">
            {onRefresh && <Button variant="outline" onClick={() => onRefresh()} disabled={refreshing} aria-label="Refresh workspace"><RefreshCw className={refreshing ? 'animate-spin' : ''} aria-hidden="true" /><span className="hidden sm:inline">Refresh</span></Button>}
            <Button variant="ghost" onClick={onSignOut} className="lg:hidden" aria-label="Sign out"><LogOut aria-hidden="true" /><span className="hidden sm:inline">Sign out</span></Button>
          </div>
        </div>
      </header>

      <main className="page-enter px-4 py-7 sm:px-6 sm:py-8 lg:px-8 lg:py-10">
        <div className="mx-auto max-w-[1280px]">
          <div className="mb-8">
            <p className="eyebrow">{roleLabels[role]}</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">{title}</h1>
            {description && <p className="mt-3 max-w-3xl text-muted-foreground">{description}</p>}
          </div>
          {children}
        </div>
      </main>
    </div>
  </div>
);

export default WorkspaceShell;
