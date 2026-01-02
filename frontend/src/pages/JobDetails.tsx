import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
    ArrowLeft,
    XCircle,
    RotateCcw,
    Trash2,
    ExternalLink,
    Clock,
    Calendar,
    AlertCircle,
    Download,
    FileText,
    FileCode,
    Wifi,
    WifiOff,
    Rocket,
    Search,
    Database,
    Target,
    BarChart,
    CheckSquare
} from 'lucide-react';
import { api } from '../api/client';
import type { Job, WorkflowExecution } from '../types';
import StatusBadge from '../components/StatusBadge';
import WorkflowDataTabs from '../components/WorkflowDataTabs';
import { useJobUpdates } from '../hooks/useWebSocket';
import './JobDetails.css';

interface JobDetailsProps {
    addToast: (message: string, type: 'success' | 'error' | 'warning') => void;
}

const WORKFLOW_STAGES = [
    { key: 'INITIALIZED', label: 'Initialized', icon: Rocket },
    { key: 'RESEARCHING', label: 'Research', icon: Search },
    { key: 'COLLECTING_DATA', label: 'Data Collection', icon: Database },
    { key: 'TRAINING', label: 'Training', icon: Target },
    { key: 'EVALUATING', label: 'Evaluation', icon: BarChart },
    { key: 'COMPLETED', label: 'Completed', icon: CheckSquare },
];

export default function JobDetails({ addToast }: JobDetailsProps) {
    const { jobId } = useParams<{ jobId: string }>();
    const navigate = useNavigate();
    const [job, setJob] = useState<Job | null>(null);
    const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
    const [loading, setLoading] = useState(true);
    const [showExportMenu, setShowExportMenu] = useState(false);

    // WebSocket for real-time updates
    const {
        status,
        currentState,
        progress,
        message,
        stageResults: wsStageResults,
        connected: isConnected
    } = useJobUpdates(jobId || '');

    // Update job when WebSocket receives update
    useEffect(() => {
        if (status || currentState || message || progress !== undefined) {
            setJob((prev: Job | null) => {
                if (!prev) return prev;
                return {
                    ...prev,
                    ...(status && { status: status as any }),
                    ...(currentState && { current_state: currentState as any }),
                    ...(message && { message }),
                    ...(progress !== undefined && { progress })
                };
            });
        }
    }, [status, currentState, message, progress]);

    const handleExport = async (format: string) => {
        if (!job) return;
        setShowExportMenu(false);
        try {
            const blob = await api.exportJob(job.id, format);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `research_report_${job.id}.${format === 'jupyter' ? 'ipynb' : format}`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            addToast(`Exported as ${format.toUpperCase()}`, 'success');
        } catch (err: any) {
            addToast(`Export failed: ${err.message}`, 'error');
        }
    };

    const fetchJobDetails = async () => {
        if (!jobId) return;
        try {
            const [jobData, execData] = await Promise.all([
                api.getJob(jobId),
                api.getJobExecutions(jobId)
            ]);
            setJob((prev) => {
                if (!prev) return jobData;

                // Determine state priority for UI updates
                const getStatePriority = (state: string) => {
                    const index = WORKFLOW_STAGES.findIndex(s => s.key === state);
                    return index === -1 ? 0 : index;
                };

                const newState = { ...jobData };

                // If currently running, prevent regression to an earlier state unless API indicates success/failure
                if (prev.status === 'RUNNING' && jobData.status === 'RUNNING') {
                    const currentRank = getStatePriority(prev.current_state || 'INITIALIZED');
                    const newRank = getStatePriority(jobData.current_state || 'INITIALIZED');

                    if (newRank < currentRank) {
                        newState.current_state = prev.current_state;
                        newState.progress = prev.progress;
                        newState.message = prev.message;
                    }
                }
                // If UI is already showing running but API says pending/initialized, ignore stale API
                else if (prev.status === 'RUNNING' && (jobData.status === 'PENDING' || jobData.current_state === 'INITIALIZED')) {
                    newState.status = prev.status;
                    newState.current_state = prev.current_state;
                    newState.progress = prev.progress;
                    newState.message = prev.message;
                }

                return newState;
            });
            setExecutions(execData.executions);
        } catch (err) {
            addToast('Failed to load job details', 'error');
            navigate('/jobs');
        } finally {
            setLoading(false);
        }
    };

    // Initial fetch on mount
    useEffect(() => {
        fetchJobDetails();
    }, [jobId]);

    // Merge stage results from job (persisted) and websocket (live)
    // prioritized order: raw results < transformed UI results < live updates
    const mergedStageResults = {
        ...(job?.result?.final_results || {}),
        ...(job?.state_results || {}),
        ...wsStageResults
    };

    // Use live values from WebSocket if available, otherwise fallback to API data
    const activeState = currentState || job?.current_state || 'INITIALIZED';
    const activeStatus = status || job?.status || 'PENDING';
    const activeProgress = progress !== undefined ? progress : (job?.progress || 0);

    // Re-fetch details when significant state changes occur via WebSocket
    // This replaces constant polling with event-driven updates
    // Re-fetch details when significant state changes occur via WebSocket
    useEffect(() => {
        if (currentState || status === 'COMPLETED' || status === 'FAILED') {
            fetchJobDetails();
        }
    }, [currentState, status]);

    const handleCancel = async () => {
        if (!job) return;
        try {
            await api.cancelJob(job.id);
            addToast('Job cancelled', 'success');
            fetchJobDetails();
        } catch (err: any) {
            addToast(err.message || 'Failed to cancel job', 'error');
        }
    };

    const handleRetry = async () => {
        if (!job) return;
        try {
            await api.retryJob(job.id);
            addToast('Job retry initiated', 'success');
            fetchJobDetails();
        } catch (err: any) {
            addToast(err.message || 'Failed to retry job', 'error');
        }
    };

    const handleDelete = async () => {
        if (!job || !confirm('Are you sure you want to delete this job?')) return;
        try {
            await api.deleteJob(job.id);
            addToast('Job deleted', 'success');
            navigate('/jobs');
        } catch (err: any) {
            addToast(err.message || 'Failed to delete job', 'error');
        }
    };

    const getCurrentStageIndex = () => {
        if (!job?.current_state) return -1;
        return WORKFLOW_STAGES.findIndex(s => s.key === job.current_state);
    };

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
            </div>
        );
    }

    if (!job) {
        return (
            <div className="empty-state">
                <p>Job not found</p>
                <Link to="/jobs" className="btn btn-primary mt-4">Back to Jobs</Link>
            </div>
        );
    }

    const currentStageIndex = getCurrentStageIndex();

    return (
        <div className="job-details-page">
            {/* Header */}
            <div className="details-header">
                <div className="header-left">
                    <Link to="/jobs" className="back-link">
                        <ArrowLeft size={20} />
                        Back to Jobs
                    </Link>
                    <h1 className="page-title">{job.topic}</h1>
                    <div className="header-meta">
                        <span className="domain-badge">{job.domain}</span>
                        <StatusBadge status={job.status} />
                        {/* Real-time connection indicator */}
                        <span className={`connection-indicator ${isConnected ? 'connected' : ''}`}>
                            {isConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
                            {isConnected ? 'Live' : 'Offline'}
                        </span>
                    </div>
                </div>
                <div className="header-actions">
                    {/* Export dropdown */}
                    {job.status === 'COMPLETED' && (
                        <div className="export-dropdown">
                            <button className="btn btn-secondary" onClick={() => setShowExportMenu(!showExportMenu)}>
                                <Download size={18} />
                                Export
                            </button>
                            {showExportMenu && (
                                <div className="export-menu">
                                    <button onClick={() => handleExport('pdf')}>
                                        <FileText size={16} /> PDF Report
                                    </button>
                                    <button onClick={() => handleExport('markdown')}>
                                        <FileCode size={16} /> Markdown
                                    </button>
                                    <button onClick={() => handleExport('latex')}>
                                        <FileCode size={16} /> LaTeX
                                    </button>
                                    <button onClick={() => handleExport('jupyter')}>
                                        <FileCode size={16} /> Jupyter
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                    {(job.status === 'PENDING' || job.status === 'RUNNING') && (
                        <button className="btn btn-warning" onClick={handleCancel}>
                            <XCircle size={18} />
                            Cancel
                        </button>
                    )}
                    {job.status === 'FAILED' && (
                        <button className="btn btn-success" onClick={handleRetry}>
                            <RotateCcw size={18} />
                            Retry
                        </button>
                    )}
                    {job.status !== 'RUNNING' && (
                        <button className="btn btn-danger" onClick={handleDelete}>
                            <Trash2 size={18} />
                            Delete
                        </button>
                    )}
                </div>
            </div>

            {/* Workflow Progress */}
            <div className="card progress-card">
                <h2 className="card-title">Workflow Progress</h2>
                <div className="workflow-stages">
                    {WORKFLOW_STAGES.map((stage, index) => {
                        const StageIcon = stage.icon;
                        return (
                            <div
                                key={stage.key}
                                className={`stage ${index < currentStageIndex ? 'completed' :
                                    index === currentStageIndex ? 'active' :
                                        job.status === 'FAILED' && index === currentStageIndex ? 'failed' :
                                            ''
                                    }`}
                            >
                                <div className="stage-icon"><StageIcon size={20} /></div>
                                <div className="stage-label">{stage.label}</div>
                                {index < WORKFLOW_STAGES.length - 1 && (
                                    <div className="stage-connector" />
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Details Grid */}
            <div className="details-grid">
                {/* Info Card */}
                <div className="card info-card">
                    <h2 className="card-title">Job Information</h2>
                    <div className="info-list">
                        <div className="info-item">
                            <Calendar size={16} />
                            <span className="info-label">Created</span>
                            <span className="info-value">{new Date(job.created_at).toLocaleString()}</span>
                        </div>
                        {job.started_at && (
                            <div className="info-item">
                                <Clock size={16} />
                                <span className="info-label">Started</span>
                                <span className="info-value">{new Date(job.started_at).toLocaleString()}</span>
                            </div>
                        )}
                        {job.completed_at && (
                            <div className="info-item">
                                <Clock size={16} />
                                <span className="info-label">Completed</span>
                                <span className="info-value">{new Date(job.completed_at).toLocaleString()}</span>
                            </div>
                        )}
                        {job.started_at && job.completed_at && (
                            <div className="info-item">
                                <Clock size={16} />
                                <span className="info-label">Duration</span>
                                <span className="info-value">
                                    {Math.round((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000)}s
                                </span>
                            </div>
                        )}
                        <div className="info-item">
                            <RotateCcw size={16} />
                            <span className="info-label">Retries</span>
                            <span className="info-value">{job.retry_count} / {job.max_retries}</span>
                        </div>
                        {job.mlflow_experiment_id && (
                            <div className="info-item">
                                <ExternalLink size={16} />
                                <span className="info-label">MLflow</span>
                                <a
                                    href={`http://localhost:5000/#/experiments/${job.mlflow_experiment_id}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="info-link"
                                >
                                    View Experiment
                                </a>
                            </div>
                        )}
                    </div>
                </div>

                <div className="card result-card full-width">
                    <WorkflowDataTabs
                        jobId={job.id}
                        stageResults={mergedStageResults}
                        currentState={activeState}
                        progress={activeProgress}
                    />
                </div>

                {/* Error Card */}
                {job.error_message && (
                    <div className="card error-card">
                        <h2 className="card-title">
                            <AlertCircle size={18} />
                            Error
                        </h2>
                        <div className="error-message">{job.error_message}</div>
                    </div>
                )}
            </div>

            {/* Executions Timeline */}
            {executions.length > 0 && (
                <div className="card executions-card">
                    <h2 className="card-title">Execution History</h2>
                    <div className="timeline">
                        {executions.map((exec) => (
                            <div key={exec.id} className={`timeline-item ${exec.status}`}>
                                <div className="timeline-content">
                                    <div className="timeline-header">
                                        <span className="timeline-state">{exec.state}</span>
                                        <StatusBadge status={exec.status} />
                                    </div>
                                    <div className="timeline-time">
                                        {new Date(exec.started_at).toLocaleString()}
                                    </div>
                                    {exec.metrics && (
                                        <div className="timeline-metrics">
                                            {Object.entries(exec.metrics).map(([key, value]) => (
                                                <span key={key} className="metric-tag">
                                                    {key}: {typeof value === 'number' ? value.toFixed(4) : String(value)}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Raw Data */}
            {job.result && (
                <details className="card raw-data-card">
                    <summary className="raw-data-toggle">
                        View Raw Result Data
                    </summary>
                    <pre className="raw-data-content">
                        {JSON.stringify(job.result, null, 2)}
                    </pre>
                </details>
            )}
        </div>
    );
}
