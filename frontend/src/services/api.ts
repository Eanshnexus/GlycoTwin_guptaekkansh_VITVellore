/**
 * GlycoTwin Centralized API Client.
 * Connects directly to the Phase 3 FastAPI backend.
 */
import type {
  HealthResponse,
  MetadataResponse,
  PatientListResponse,
  PatientDetail,
  ObservationResponse,
  HistoricalPredictionResponse,
  EvaluationResponse,
  PersonalisationResponse,
  InferenceRequest,
  InferenceResponse,
} from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  try {
    const res = await fetch(url, config);
    if (!res.ok) {
      let errDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson && errorJson.detail) {
          errDetail = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to status text
      }
      throw new ApiError(errDetail, res.status);
    }
    return (await res.json()) as T;
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.message || 'Network request failed', 0);
  }
}

// Named function exports for pages
export const fetchHealth = () => request<HealthResponse>('/api/health');
export const fetchMetadata = () => request<MetadataResponse>('/api/metadata');

export const fetchPatients = (page: number = 1, pageSize: number = 25) =>
  request<PatientListResponse>(`/api/patients?page=${page}&page_size=${pageSize}`);

export const fetchPatientDetail = (patientId: string) =>
  request<PatientDetail>(`/api/patients/${encodeURIComponent(patientId)}`);

export const fetchPatientObservations = (
  patientId: string,
  params?: { start_time?: string; end_time?: string; startTime?: string; endTime?: string; limit?: number; offset?: number }
) => {
  const query = new URLSearchParams();
  const st = params?.start_time || params?.startTime;
  const et = params?.end_time || params?.endTime;
  if (st) query.set('start_time', st);
  if (et) query.set('end_time', et);
  if (params?.limit) query.set('limit', params.limit.toString());
  if (params?.offset !== undefined) query.set('offset', params.offset.toString());
  const qs = query.toString() ? `?${query.toString()}` : '';
  return request<ObservationResponse>(`/api/patients/${encodeURIComponent(patientId)}/observations${qs}`);
};

export const fetchPatientPredictions = (
  patientId: string,
  params?: { task?: string; model?: string; limit?: number; offset?: number }
) => {
  const query = new URLSearchParams();
  if (params?.task) query.set('task', params.task);
  if (params?.model) query.set('model', params.model);
  if (params?.limit) query.set('limit', params.limit.toString());
  if (params?.offset !== undefined) query.set('offset', params.offset.toString());
  const qs = query.toString() ? `?${query.toString()}` : '';
  return request<HistoricalPredictionResponse>(`/api/patients/${encodeURIComponent(patientId)}/predictions${qs}`);
};

export const fetchModelEvaluation = (task: string = 'onset') =>
  request<EvaluationResponse>(`/api/models/evaluation?task=${encodeURIComponent(task)}`);

export const fetchPersonalisationResults = (patientId?: string) => {
  const qs = patientId ? `?participant_id=${encodeURIComponent(patientId)}` : '';
  return request<PersonalisationResponse>(`/api/models/personalisation${qs}`);
};

export const postPredictionInference = (payload: InferenceRequest) =>
  request<InferenceResponse>('/api/predictions', {
    method: 'POST',
    body: JSON.stringify(payload),
  });

// Consolidated API object
export const api = {
  getHealth: fetchHealth,
  getMetadata: fetchMetadata,
  getPatients: fetchPatients,
  getPatientDetail: fetchPatientDetail,
  getPatientObservations: fetchPatientObservations,
  getPatientPredictions: fetchPatientPredictions,
  getModelEvaluation: fetchModelEvaluation,
  getPersonalisation: fetchPersonalisationResults,
  predictInference: postPredictionInference,
};

export default api;
