/**
 * Cygnusa Elite-Hire Theme Configuration
 * Based on Landing Page Design
 * 
 * Color Palette: Indigo primary with complementary accent colors
 * Design Philosophy: Clean, modern, professional with smooth animations
 */

export const theme = {
    // Color System
    colors: {
        // Primary Colors
        primary: {
            50: '#EEF2FF',
            100: '#E0E7FF',
            200: '#C7D2FE',
            300: '#A5B4FC',
            400: '#818CF8',
            500: '#6366F1',  // Main brand color
            600: '#4F46E5',  // Primary indigo (most used)
            700: '#4338CA',
            800: '#3730A3',
            900: '#312E81',
        },

        // Accent Colors
        accent: {
            blue: {
                100: '#DBEAFE',
                600: '#2563EB',
            },
            emerald: {
                100: '#D1FAE5',
                600: '#059669',
            },
            purple: {
                100: '#F3E8FF',
                600: '#9333EA',
            },
            amber: {
                100: '#FEF3C7',
                600: '#D97706',
            },
            rose: {
                100: '#FFE4E6',
                600: '#E11D48',
            },
        },

        // Neutral Colors
        slate: {
            50: '#F8FAFC',
            100: '#F1F5F9',
            200: '#E2E8F0',
            300: '#CBD5E1',
            400: '#94A3B8',
            500: '#64748B',
            600: '#475569',
            700: '#334155',
            800: '#1E293B',
            900: '#0F172A',
        },

        // Semantic Colors
        success: '#10B981',
        error: '#EF4444',
        warning: '#F59E0B',
        info: '#3B82F6',

        // Status Colors (for candidates)
        status: {
            pending: '#F59E0B',      // Amber
            underReview: '#3B82F6',  // Blue
            hired: '#10B981',        // Green
            rejected: '#EF4444',     // Red
        },
    },

    // Background Gradients
    backgrounds: {
        page: 'bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50',
        card: 'bg-white',
        cardHover: 'bg-gray-50',
        header: 'bg-white/80 backdrop-blur-md',
        modal: 'bg-white',
    },

    // Typography
    typography: {
        fontFamily: {
            sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
        },
        fontSize: {
            xs: '0.75rem',      // 12px
            sm: '0.875rem',     // 14px
            base: '1rem',       // 16px
            lg: '1.125rem',     // 18px
            xl: '1.25rem',      // 20px
            '2xl': '1.5rem',    // 24px
            '3xl': '1.875rem',  // 30px
            '4xl': '2.25rem',   // 36px
            '5xl': '3rem',      // 48px
            '6xl': '3.75rem',   // 60px
        },
        fontWeight: {
            normal: '400',
            medium: '500',
            semibold: '600',
            bold: '700',
        },
    },

    // Spacing (Tailwind-compliant)
    spacing: {
        xs: '0.25rem',    // 4px
        sm: '0.5rem',     // 8px
        md: '1rem',       // 16px
        lg: '1.5rem',     // 24px
        xl: '2rem',       // 32px
        '2xl': '3rem',    // 48px
        '3xl': '4rem',    // 64px
    },

    // Border Radius
    borderRadius: {
        none: '0',
        sm: '0.125rem',   // 2px
        default: '0.25rem', // 4px
        md: '0.375rem',   // 6px
        lg: '0.5rem',     // 8px
        xl: '0.75rem',    // 12px
        '2xl': '1rem',    // 16px
        full: '9999px',
    },

    // Shadows
    shadows: {
        sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        default: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    },

    // Component Styles
    components: {
        button: {
            primary: 'bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105',
            secondary: 'border-2 border-indigo-600 text-indigo-600 hover:bg-indigo-50 px-8 py-3 rounded-lg font-medium transition-all duration-300 hover:scale-105',
            ghost: 'text-slate-700 hover:text-indigo-600 transition-colors duration-300',
            danger: 'bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-medium shadow-md hover:shadow-lg transition-all duration-300',
        },

        card: {
            default: 'bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 rounded-lg',
            interactive: 'bg-white border-none shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1 rounded-lg cursor-pointer',
            dark: 'bg-slate-800/50 border-slate-700 shadow-md hover:shadow-xl transition-all duration-300 rounded-lg',
        },

        input: {
            default: 'w-full px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200',
            error: 'w-full px-4 py-2 border border-red-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent',
        },

        badge: {
            pending: 'bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-xs font-medium',
            underReview: 'bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-medium',
            hired: 'bg-green-100 text-green-800 px-3 py-1 rounded-full text-xs font-medium',
            rejected: 'bg-red-100 text-red-800 px-3 py-1 rounded-full text-xs font-medium',
            default: 'bg-gray-100 text-gray-800 px-3 py-1 rounded-full text-xs font-medium',
        },

        iconBackground: {
            primary: 'w-12 h-12 bg-indigo-100 rounded-lg flex items-center justify-center',
            blue: 'w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center',
            emerald: 'w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center',
            purple: 'w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center',
            amber: 'w-12 h-12 bg-amber-100 rounded-lg flex items-center justify-center',
            rose: 'w-12 h-12 bg-rose-100 rounded-lg flex items-center justify-center',
        },
    },

    // Animation & Transitions
    animation: {
        duration: {
            fast: '150ms',
            normal: '300ms',
            slow: '500ms',
        },
        timing: {
            default: 'cubic-bezier(0.4, 0, 0.2, 1)',
            in: 'cubic-bezier(0.4, 0, 1, 1)',
            out: 'cubic-bezier(0, 0, 0.2, 1)',
            inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
        },
    },

    // Breakpoints (for responsive design)
    breakpoints: {
        sm: '640px',
        md: '768px',
        lg: '1024px',
        xl: '1280px',
        '2xl': '1536px',
    },
};

// Utility function to get status color
export const getStatusColor = (status) => {
    const statusLower = status?.toLowerCase().replace(/[-_]/g, '');

    switch (statusLower) {
        case 'pending':
            return theme.colors.status.pending;
        case 'underreview':
        case 'under_review':
            return theme.colors.status.underReview;
        case 'hired':
        case 'selected':
            return theme.colors.status.hired;
        case 'rejected':
        case 'declined':
            return theme.colors.status.rejected;
        default:
            return theme.colors.slate[500];
    }
};

// Utility function to get status badge class
export const getStatusBadgeClass = (status) => {
    const statusLower = status?.toLowerCase().replace(/[-_]/g, '');

    switch (statusLower) {
        case 'pending':
            return theme.components.badge.pending;
        case 'underreview':
        case 'under_review':
            return theme.components.badge.underReview;
        case 'hired':
        case 'selected':
            return theme.components.badge.hired;
        case 'rejected':
        case 'declined':
            return theme.components.badge.rejected;
        default:
            return theme.components.badge.default;
    }
};

export default theme;
