// Job Status Enum
export type JobStatus = 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export type JobType = 'Machine Learning' | 'Data Analysis' | 'Research' | 'Report Generation';

// Workflow State Enum
export type WorkflowState =
    | 'INITIALIZED'
    | 'RESEARCHING'
    | 'COLLECTING_DATA'
    | 'TRAINING'
    | 'EVALUATING'
    | 'COMPLETED'
    | 'FAILED';

// Job Interface
export interface Job {
    id: string;
    topic: string;
    domain: string;
    status: JobStatus;
    current_state: WorkflowState | null;
    created_at: string;
    updated_at: string;
    started_at: string | null;
    completed_at: string | null;
    config: Record<string, unknown> | null;
    result: JobResult | null;
    error_message: string | null;
    mlflow_experiment_id: string | null;
    mlflow_run_id: string | null;
    retry_count: number;
    max_retries: number;
    message: string | null;
    progress: number | null;
}

// Job Result Interface
export interface JobResult {
    workflow_id: string;
    status: string;
    final_results?: {
        research?: Record<string, unknown>;
        data?: Record<string, unknown>;
        training?: Record<string, unknown>;
        evaluation?: Record<string, unknown>;
    };
    best_model?: {
        model_type: string;
        score: number;
        rank: number;
        metrics?: Record<string, number>;
    };
    iterations: number;
    state_history?: Array<{
        from_state: WorkflowState;
        to_state: WorkflowState;
        reason: string;
        timestamp: string;
    }>;
}

// Job Create Request
export interface JobCreateRequest {
    topic: string;
    domain: string;
    config?: Record<string, unknown>;
    priority?: number;
}

// Job List Response
export interface JobListResponse {
    jobs: Job[];
    total: number;
    page: number;
    page_size: number;
}

// Workflow Execution
export interface WorkflowExecution {
    id: string;
    job_id: string;
    iteration: number;
    state: WorkflowState;
    status: JobStatus;
    started_at: string;
    completed_at: string | null;
    state_results: Record<string, unknown> | null;
    metrics: Record<string, unknown> | null;
    error_message: string | null;
    mlflow_run_id: string | null;
}

// Health Response
export interface HealthResponse {
    status: string;
    version: string;
    timestamp: string;
}

// Readiness Response
export interface ReadinessResponse {
    ready: boolean;
    database: boolean;
    queue: boolean;
    mlflow: boolean;
    timestamp: string;
}

// Metrics Response
export interface MetricsResponse {
    queue_length: number;
    running_jobs: number;
    completed_jobs_24h: number;
    failed_jobs_24h: number;
    average_duration_minutes: number;
}

// API Error
export interface ApiError {
    detail: string;
    error_code?: string;
    timestamp?: string;
}
