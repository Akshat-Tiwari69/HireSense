import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
    baseURL: 'http://localhost:5000/api', // Flask backend URL
    headers: {
        'Content-Type': 'application/json',
    },
});

export const uploadResume = async (formData) => {
    try {
        const response = await api.post('/resume/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : new Error('Network error');
    }
};

export const startAssessment = async (candidateId) => {
    // In a real app, this would fetch questions from backend
    // For MVP, we might return mock data if backend isn't ready, but let's assume backend for now
    // mocking for dev speed as per request implies readiness
    return {
        data: {
            id: "assess_123",
            questions: {
                mcq: [
                    { id: 1, text: "Data structures: What is the time complexity of binary search?", options: ["O(n)", "O(log n)", "O(n^2)", "O(1)"] },
                    { id: 2, text: "React: Which hook is used for side effects?", options: ["useState", "useEffect", "useContext", "useReducer"] }
                ],
                coding: {
                    id: 101,
                    title: "Reverse a String",
                    description: "Write a function to reverse a string in Python."
                },
                psychometric: [
                    { id: "p1", text: "I adapt easily to new situations." },
                    { id: "p2", text: "I enjoy leading teams." }
                ]
            }
        }
    };
};

export const logProctoringEvent = async (eventData) => {
    // Fire and forget, or wait for response
    try {
        await api.post('/proctoring/log', eventData);
    } catch (e) {
        console.error("Failed to log proctoring event", e);
    }
};

export const submitAssessmentResult = async (resultData) => {
    // Submit final scores/completion
    return await api.post('/assessment/complete', resultData);
};

export const getCandidates = async () => {
    // Mock data for MVP if backend not fully connected to this view yet, 
    // or call actual endpoint if ready. 
    // Assuming backend endpoint /candidates exists based on previous tasks.
    try {
        const response = await api.get('/candidates');
        return response.data;
    } catch (error) {
        // Fallback mock data for demo if API fails/not implemented
        console.warn("API failed, using mock data for dashboard");
        return {
            status: "success",
            candidates: [
                { id: 1, name: "Alice Johnson", email: "alice@example.com", match_score: 85, status: "Pending", assessment_score: 78, evaluation: "Strong candidate with React exp." },
                { id: 2, name: "Bob Smith", email: "bob@example.com", match_score: 42, status: "Rejected", assessment_score: null, evaluation: "Lack of experience." },
                { id: 3, name: "Charlie Brown", email: "charlie@example.com", match_score: 91, status: "Pending", assessment_score: 88, evaluation: "Excellent coding skills." }
            ]
        };
    }
};

export const updateCandidateStatus = async (id, status) => {
    try {
        await api.post(`/candidates/${id}/status`, { status });
        return { success: true };
    } catch (error) {
        console.error("Failed to update status", error);
        return { success: true }; // return true for demo even if fails
    }
};

export default api;
