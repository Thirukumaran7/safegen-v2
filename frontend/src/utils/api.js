import axios from 'axios';
import { BACKEND } from './constants';
export const analyzeText  = (text, policy, role, useRag) => axios.post(BACKEND + '/analyze', { text, policy, role, use_rag: useRag });
export const sendFeedback = (analysisId, agreed, comment) => axios.post(BACKEND + '/feedback', { analysis_id: analysisId, agreed, user_comment: comment });
export const fetchLogs    = (limit = 50) => axios.get(BACKEND + '/logs?limit=' + limit);
export const fetchStats   = () => axios.get(BACKEND + '/stats');
export const fetchHealth  = () => axios.get(BACKEND + '/health');
