import { z } from 'zod';

// Email validation schema
export const emailSchema = z.string()
    .email('Invalid email format')
    .min(1, 'Email is required');

// Password validation schema
export const passwordSchema = z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(100, 'Password is too long');

// Login form schema
export const loginSchema = z.object({
    email: emailSchema,
    password: z.string().min(1, 'Password is required'),
});

// User registration schema
export const userRegistrationSchema = z.object({
    name: z.string().min(2, 'Name must be at least 2 characters'),
    email: emailSchema,
    password: passwordSchema,
    role: z.enum(['admin', 'interviewer', 'proctor'], {
        errorMap: () => ({ message: 'Invalid role selected' })
    }),
});

// Job posting schema
export const jobPostingSchema = z.object({
    title: z.string().min(3, 'Title must be at least 3 characters'),
    description: z.string().min(10, 'Description must be at least 10 characters'),
    department: z.string().min(1, 'Department is required'),
    location: z.string().min(1, 'Location is required'),
    required_skills: z.string().min(1, 'Required skills are required'),
    min_experience: z.number().min(0, 'Experience must be positive').max(50, 'Experience too high'),
});

// Candidate form schema  
export const candidateSchema = z.object({
    name: z.string().min(2, 'Name must be at least 2 characters'),
    email: emailSchema,
    phone: z.string()
        .regex(/^\+?[\d\s()-]+$/, 'Invalid phone number format')
        .optional()
        .or(z.literal('')),
    status: z.enum(['pending', 'under_review', 'hired', 'rejected']),
    match_score: z.number().min(0).max(100).optional(),
});

// Assessment scheduling schema
export const assessmentScheduleSchema = z.object({
    scheduled_time: z.string().min(1, 'Scheduled time is required'),
    additional_info: z.string().optional(),
});

// File upload schema
export const resumeUploadSchema = z.object({
    file: z.instanceof(File)
        .refine((file) => file.size <= 5 * 1024 * 1024, 'File must be less than 5MB')
        .refine(
            (file) => ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(file.type),
            'File must be PDF or DOCX'
        ),
});

// Utility function to format Zod errors
export const formatZodError = (error) => {
    const formatted = {};
    error.errors.forEach((err) => {
        if (err.path.length > 0) {
            formatted[err.path[0]] = err.message;
        }
    });
    return formatted;
};

// Utility function to validate data
export const validateData = (schema, data) => {
    const result = schema.safeParse(data);
    if (!result.success) {
        return {
            valid: false,
            errors: formatZodError(result.error),
        };
    }
    return {
        valid: true,
        data: result.data,
    };
};
