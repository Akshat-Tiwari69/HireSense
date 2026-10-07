import { twMerge } from 'tailwind-merge';

// Later classes win on Tailwind conflicts, so callers can override component defaults.
export function cn(...classes) {
  return twMerge(classes.flat().filter(Boolean).join(' '));
}
