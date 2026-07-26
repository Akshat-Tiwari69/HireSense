import Logo from '../Logo';
import LoadingSpinner from './LoadingSpinner';

const LoadingScreen = ({ message = 'Loading…' }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 backdrop-blur-sm" role="status" aria-live="polite">
    <div className="flex flex-col items-center text-center">
      <Logo variant="icon" size="large" />
      <LoadingSpinner size="sm" className="mt-5 text-primary" />
      <p className="mt-3 text-sm font-medium text-foreground">{message}</p>
    </div>
  </div>
);

export default LoadingScreen;
