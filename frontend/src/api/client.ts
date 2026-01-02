import type {
    Job,
    JobListResponse,
    JobCreateRequest,
    WorkflowExecution,
    HealthResponse,
    ReadinessResponse,
    MetricsResponse
} from '../types';

const API_BASE = '/api/v1';

class ApiClient {
    private async request<T>(
        endpoint: string,
        options: RequestInit = {}
    ): Promise<T> {
        const url = endpoint.startsWith('/api') || endpoint.startsWith('/health') || endpoint.startsWith('/ready') || endpoint.startsWith('/metrics')
            ? endpoint
            : `${API_BASE}${endpoint}`;

        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        if (response.status === 204) {
            return undefined as T;
        }

        return response.json();
    }

    // Health endpoints
    async getHealth(): Promise<HealthResponse> {
        return this.request<HealthResponse>('/health');
    }

    async getReadiness(): Promise<ReadinessResponse> {
        return this.request<ReadinessResponse>('/ready');
    }

    async getMetrics(): Promise<MetricsResponse> {
        return this.request<MetricsResponse>('/metrics');
    }

    // Job endpoints
    async listJobs(params?: {
        status?: string;
        domain?: string;
        page?: number;
        page_size?: number;
    }): Promise<JobListResponse> {
        const searchParams = new URLSearchParams();
        if (params?.status) searchParams.append('status', params.status);
        if (params?.domain) searchParams.append('domain', params.domain);
        if (params?.page) searchParams.append('page', String(params.page));
        if (params?.page_size) searchParams.append('page_size', String(params.page_size));

        const query = searchParams.toString();
        return this.request<JobListResponse>(`/jobs${query ? `?${query}` : ''}`);
    }

    async getJob(jobId: string): Promise<Job> {
        return this.request<Job>(`/jobs/${jobId}`);
    }

    async createJob(data: JobCreateRequest): Promise<Job> {
        return this.request<Job>('/jobs', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async cancelJob(jobId: string): Promise<Job> {
        return this.request<Job>(`/jobs/${jobId}/cancel`, {
            method: 'POST',
        });
    }

    async retryJob(jobId: string): Promise<Job> {
        return this.request<Job>(`/jobs/${jobId}/retry`, {
            method: 'POST',
        });
    }

    async deleteJob(jobId: string): Promise<void> {
        return this.request<void>(`/jobs/${jobId}`, {
            method: 'DELETE',
        });
    }

    async getJobExecutions(jobId: string): Promise<{
        job_id: string;
        executions: WorkflowExecution[];
        total_iterations: number;
    }> {
        return this.request(`/jobs/${jobId}/executions`);
    }

    async exportJob(jobId: string, format: string): Promise<Blob> {
        const url = `${API_BASE}/jobs/${jobId}/export?format=${format}`;
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Export failed: HTTP ${response.status}`);
        }
        return response.blob();
    }
}

export const api = new ApiClient();
