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

export const login = async (email, password) => {
    // MOCK LOGIN IMPLEMENTATION (Task S4)
    // To be replaced by actual API call when Backend Task A5 is done
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            if (email && password) {
                resolve({
                    data: {
                        token: "mock_jwt_token_12345",
                        user: {
                            name: "Interviewer Name",
                            role: "interviewer",
                            email: email
                        }
                    }
                });
            } else {
                reject({ message: "Invalid credentials" });
            }
        }, 1000); // Simulate network delay
    });

    /*
    // REAL IMPLEMENTATION (Future)
    try {
        const response = await api.post('/auth/login', { email, password });
        return response.data;
    } catch (error) {
        throw error.response ? error.response.data : new Error('Network error');
    }
    */
};

export default api;
