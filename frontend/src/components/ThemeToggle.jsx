import React from 'react';
import { Moon, Sun } from 'lucide-react';
import { Button } from './ui/button';
import { useTheme } from '../context/ThemeProvider';

/**
 * Theme toggle button component
 * Switches between light and dark mode
 */
export const ThemeToggle = ({ variant = 'ghost', size = 'default', className = '' }) => {
    const { theme, toggleTheme, isDark } = useTheme();

    return (
        <Button
            variant={variant}
            size={size}
            onClick={toggleTheme}
            className={`transition-all duration-300 ${className}`}
            aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
            title={`Current theme: ${theme}`}
        >
            {isDark ? (
                <Sun className="w-5 h-5 text-amber-500 transition-transform duration-300 rotate-0 hover:rotate-180" />
            ) : (
                <Moon className="w-5 h-5 text-indigo-600 transition-transform duration-300 rotate-0 hover:-rotate-12" />
            )}
        </Button>
    );
};

export default ThemeToggle;
