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

export default api;
