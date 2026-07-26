import { ArrowLeft, Home } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

import Logo from '../components/Logo';
import { Button } from '../components/ui/button';

const NotFoundPage = () => {
  const navigate = useNavigate();
  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-5 py-12">
      <div className="page-enter w-full max-w-xl text-center">
        <Link to="/" className="inline-flex"><Logo /></Link>
        <p className="eyebrow mt-12">Error 404</p>
        <h1 className="display-face mt-3 text-5xl sm:text-6xl">This page is no longer in the pipeline.</h1>
        <p className="mx-auto mt-5 max-w-md leading-7 text-muted-foreground">The address may be outdated, or the page may have moved to a different part of HireSense.</p>
        <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
          <Button variant="outline" onClick={() => navigate(-1)}><ArrowLeft />Go back</Button>
          <Button asChild><Link to="/"><Home />HireSense home</Link></Button>
        </div>
      </div>
    </main>
  );
};

export default NotFoundPage;
