import { useEffect, useState } from 'react';
import { ArrowLeft, Check, Eye, EyeOff, Loader2, LockKeyhole } from 'lucide-react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import Logo from '../components/Logo';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../hooks/use-toast';
import { api } from '../services/api';

const routeForRole = (role) => {
  if (['admin', 'super_admin'].includes(role)) return '/admin';
  if (role === 'proctor') return '/proctor';
  return '/dashboard';
};

const LoginPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();
  const { signIn, signOut, status, user } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [loginError, setLoginError] = useState('');

  useEffect(() => {
    if (status === 'authenticated') {
      navigate(routeForRole(user?.role), { replace: true });
    }
  }, [navigate, status, user?.role]);

  const validateForm = () => {
    const nextErrors = {};
    const normalizedEmail = email.trim();
    if (!normalizedEmail) nextErrors.email = 'Enter your work email.';
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normalizedEmail)) nextErrors.email = 'Enter a valid email address.';
    if (!password) nextErrors.password = 'Enter your password.';
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleLogin = async (event) => {
    event.preventDefault();
    if (!validateForm()) return;

    setLoading(true);
    setLoginError('');
    signOut();
    try {
      const response = await api.post('/api/auth/login', {
        email: email.trim(),
        password,
      });
      const token = response?.data?.data?.access_token;
      const authenticatedUser = response?.data?.data?.user;
      if (!token || !authenticatedUser?.role) throw new Error('Invalid login response');

      signIn({ token, user: authenticatedUser });
      toast({ title: 'Signed in', description: `Welcome back${authenticatedUser.name ? `, ${authenticatedUser.name}` : ''}.` });
      navigate(routeForRole(authenticatedUser.role), { replace: true });
    } catch (error) {
      signOut();
      const message = error?.response?.data?.message || 'We could not sign you in with those credentials.';
      setLoginError(message);
    } finally {
      setLoading(false);
    }
  };

  const accessMessage = loginError || (location.state?.accessDenied
    ? 'This account is not authorized for the requested workspace.'
    : '');

  return (
    <main className="grid min-h-screen bg-card lg:grid-cols-[.92fr_1.08fr]">
      <section className="relative hidden overflow-hidden bg-[#0b1220] p-10 text-white lg:flex lg:flex-col lg:justify-between xl:p-14">
        <div aria-hidden="true" className="absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(148,163,184,.09)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,.09)_1px,transparent_1px)] [background-size:40px_40px]" />
        <div aria-hidden="true" className="absolute -left-32 top-1/3 h-96 w-96 rounded-full bg-primary/25 blur-[120px]" />
        <Link to="/" className="relative z-10 w-fit"><Logo className="text-white" /></Link>
        <div className="relative z-10 max-w-lg">
          <p className="text-xs font-semibold uppercase tracking-[.16em] text-blue-300">Secure staff workspace</p>
          <h1 className="display-face mt-4 text-5xl leading-tight">The right context, before the next decision.</h1>
          <p className="mt-5 text-lg leading-8 text-slate-300">Review applicants, coordinate assessments, and record outcomes in the workspace assigned to your role.</p>
          <div className="mt-8 space-y-3 text-sm text-slate-300">
            {['Server-verified staff sessions', 'Role-scoped candidate access', 'Separate automated and human decisions'].map((item) => (
              <div key={item} className="flex items-center gap-3"><span className="flex h-6 w-6 items-center justify-center rounded-md bg-white/10"><Check className="h-3.5 w-3.5 text-emerald-300" /></span>{item}</div>
            ))}
          </div>
        </div>
        <p className="relative z-10 text-xs text-slate-500">HireSense hiring operations</p>
      </section>

      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-8">
        <div className="page-enter w-full max-w-[430px]">
          <div className="mb-10 flex items-center justify-between lg:hidden">
            <Link to="/"><Logo /></Link>
            <Button asChild variant="ghost" size="sm"><Link to="/"><ArrowLeft />Home</Link></Button>
          </div>

          <div className="mb-8">
            <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-xl bg-accent text-primary"><LockKeyhole className="h-5 w-5" /></div>
            <p className="eyebrow">Staff access</p>
            <h1 className="mt-2 text-3xl font-semibold tracking-[-0.035em] sm:text-4xl">Sign in to HireSense</h1>
            <p className="mt-3 text-muted-foreground">Use the account issued by your hiring administrator.</p>
          </div>

          {accessMessage && (
            <div role="alert" className="mb-5 rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive">
              {accessMessage}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-5" noValidate>
            <div className="space-y-2">
              <Label htmlFor="email">Work email</Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={email}
                onChange={(event) => { setEmail(event.target.value); setErrors((current) => ({ ...current, email: '' })); setLoginError(''); }}
                placeholder="name@company.com"
                autoComplete="email"
                aria-invalid={Boolean(errors.email)}
                aria-describedby={errors.email ? 'email-error' : undefined}
                autoFocus
              />
              {errors.email && <p id="email-error" className="text-sm text-destructive">{errors.email}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(event) => { setPassword(event.target.value); setErrors((current) => ({ ...current, password: '' })); setLoginError(''); }}
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                  className="pr-11"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((visible) => !visible)}
                  className="absolute right-1.5 top-1/2 flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              {errors.password && <p id="password-error" className="text-sm text-destructive">{errors.password}</p>}
            </div>

            <Button type="submit" size="lg" className="w-full" disabled={loading}>
              {loading ? <><Loader2 className="animate-spin" />Verifying account…</> : 'Continue to workspace'}
            </Button>
          </form>

          <p className="mt-7 text-center text-xs leading-5 text-muted-foreground">
            Access is logged and restricted to your assigned role. Need access? Contact your HireSense administrator.
          </p>
        </div>
      </section>
    </main>
  );
};

export default LoginPage;
