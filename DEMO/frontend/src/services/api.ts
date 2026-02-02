import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const api = {
    // Check backend health
    health: () => axios.get(`${API_URL}/`),

    // Jobs
    createJob: (name: string, keywords: string[], polygon: any) =>
        axios.post(`${API_URL}/jobs`, { name, keywords, polygon }),

    getJobs: () =>
        axios.get(`${API_URL}/jobs`),

    getJob: (jobId: number) =>
        axios.get(`${API_URL}/jobs/${jobId}`),

    getJobResults: (jobId: number) => axios.get(`${API_URL}/jobs/${jobId}/results`),

    exportJob: (jobId: number, format: 'json' | 'csv' | 'excel', cleanPhones: boolean = false) =>
        axios.get(`${API_URL}/jobs/${jobId}/export`, {
            params: { format, clean_phones: cleanPhones },
            responseType: 'blob'
        }),

    startJob: (jobId: number) =>
        axios.post(`${API_URL}/jobs/${jobId}/start`),

    // --- Configuration: Queries ---
    getSavedQueries: () => axios.get(`${API_URL}/config/queries`),
    addSavedQuery: (query: string) => axios.post(`${API_URL}/config/queries`, { query }),
    updateSavedQuery: (id: string, query: string) => axios.put(`${API_URL}/config/queries/${id}`, { query }),
    removeSavedQuery: (id: string) => axios.delete(`${API_URL}/config/queries/${id}`),

    // --- Configuration: Profiles ---
    getProfiles: () => axios.get(`${API_URL}/config/profiles`),
    createProfile: (name: string, fields: string[]) => axios.post(`${API_URL}/config/profiles`, { name, fields }),
    updateProfile: (id: string, data: any) => axios.put(`${API_URL}/config/profiles/${id}`, data),
    setProfileDefault: (id: string) => axios.put(`${API_URL}/config/profiles/${id}/default`),
    deleteProfile: (id: string) => axios.delete(`${API_URL}/config/profiles/${id}`),

    // --- Configuration: Performance ---
    getPerformance: () => axios.get(`${API_URL}/config/performance`),
    updatePerformance: (max_concurrency: number, request_delay: number, random_delay: boolean) =>
        axios.post(`${API_URL}/config/performance`, { max_concurrency, request_delay, random_delay }),

    // --- Configuration: Selectors ---
    getSelectors: () => axios.get(`${API_URL}/config/selectors`),
    updateSelectors: (selectors: any) => axios.post(`${API_URL}/config/selectors`, { selectors }),

    // --- System ---
    systemCheck: () => axios.get(`${API_URL}/system/check`),
    setupSystem: (two_captcha_key: string, proxies: string[]) =>
        axios.post(`${API_URL}/system/setup`, { two_captcha_key, proxies }),
    getSystemHealth: () => axios.get(`${API_URL}/system/health`),
};
