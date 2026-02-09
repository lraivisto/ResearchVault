
// Configuration for the ResearchVault Portal
export const BACKEND_URL = (import.meta.env.VITE_RESEARCHVAULT_BACKEND_URL as string) || 'http://localhost:8000';
export const API_BASE = `${BACKEND_URL}/api`;
