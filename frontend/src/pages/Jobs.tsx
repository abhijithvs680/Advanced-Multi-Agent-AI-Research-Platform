import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    Plus,
    Filter,
    RefreshCw,
    Trash2,
    XCircle,
    RotateCcw,
    Eye,
    ChevronLeft,
    ChevronRight
} from 'lucide-react';
import { api } from '../api/client';
import type { Job, JobStatus } from '../types';
import StatusBadge from '../components/StatusBadge';
import './Jobs.css';

interface JobsProps {
    addToast: (message: string, type: 'success' | 'error' | 'warning') => void;
}

const STATUS_OPTIONS: JobStatus[] = ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED'];

export default function Jobs({ addToast }: JobsProps) {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [domainFilter, setDomainFilter] = useState('');
    const [refreshing, setRefreshing] = useState(false);

    const fetchJobs = async () => {
        try {
            setRefreshing(true);
            const data = await api.listJobs({
                status: statusFilter || undefined,
                domain: domainFilter || undefined,
                page,
                page_size: pageSize
            });
            setJobs(data.jobs);
            setTotal(data.total);
        } catch (err) {
            addToast('Failed to load jobs', 'error');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchJobs();
    }, [page, statusFilter, domainFilter]);

    const handleCancel = async (jobId: string, e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            await api.cancelJob(jobId);
            addToast('Job cancelled successfully', 'success');
            fetchJobs();
        } catch (err: any) {
            addToast(err.message || 'Failed to cancel job', 'error');
        }
    };

    const handleRetry = async (jobId: string, e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        try {
            await api.retryJob(jobId);
            addToast('Job retry initiated', 'success');
            fetchJobs();
        } catch (err: any) {
            addToast(err.message || 'Failed to retry job', 'error');
        }
    };

    const handleDelete = async (jobId: string, e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!confirm('Are you sure you want to delete this job?')) return;
        try {
            await api.deleteJob(jobId);
            addToast('Job deleted successfully', 'success');
            fetchJobs();
        } catch (err: any) {
            addToast(err.message || 'Failed to delete job', 'error');
        }
    };

    const totalPages = Math.ceil(total / pageSize);

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div className="jobs-page">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Jobs</h1>
                    <p className="page-subtitle">Manage your research workflows</p>
                </div>
                <Link to="/create-job" className="btn btn-primary">
                    <Plus size={18} />
                    New Job
                </Link>
            </div>

            {/* Filters */}
            <div className="filters-bar">
                <div className="filters-left">
                    <div className="filter-group">
                        <Filter size={16} />
                        <select
                            value={statusFilter}
                            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
                            className="filter-select"
                        >
                            <option value="">All Status</option>
                            {STATUS_OPTIONS.map(status => (
                                <option key={status} value={status}>{status}</option>
                            ))}
                        </select>
                    </div>

                    <input
                        type="text"
                        placeholder="Filter by domain..."
                        value={domainFilter}
                        onChange={(e) => { setDomainFilter(e.target.value); setPage(1); }}
                        className="filter-input"
                    />
                </div>

                <button
                    className="btn btn-secondary btn-sm"
                    onClick={fetchJobs}
                    disabled={refreshing}
                >
                    <RefreshCw size={16} className={refreshing ? 'spin' : ''} />
                    Refresh
                </button>
            </div>

            {/* Jobs Table */}
            <div className="jobs-table-container card">
                {jobs.length === 0 ? (
                    <div className="empty-state">
                        <p>No jobs found</p>
                        <Link to="/create-job" className="btn btn-primary mt-4">
                            Create your first job
                        </Link>
                    </div>
                ) : (
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Topic</th>
                                <th>Domain</th>
                                <th>Status</th>
                                <th>State</th>
                                <th>Created</th>
                                <th>Duration</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {jobs.map(job => (
                                <tr key={job.id}>
                                    <td>
                                        <Link to={`/jobs/${job.id}`} className="job-link">
                                            {job.topic}
                                        </Link>
                                    </td>
                                    <td>
                                        <span className="domain-badge">{job.domain}</span>
                                    </td>
                                    <td>
                                        <div className="job-status-container">
                                            <StatusBadge status={job.status} />
                                            {job.status === 'RUNNING' && job.progress !== undefined && (
                                                <div className="job-progress-mini">
                                                    <div className="progress-bar-fill" style={{ width: `${job.progress}%` }} />
                                                </div>
                                            )}
                                        </div>
                                    </td>
                                    <td>
                                        <div className="state-cell">
                                            <span className="state-text">{job.current_state || '-'}</span>
                                            {job.status === 'RUNNING' && job.progress !== undefined && (
                                                <div className="progress-inline">
                                                    <div className="progress-inline-fill" style={{ width: `${job.progress}%` }} />
                                                </div>
                                            )}
                                            {job.message && <div className="message-hint">{job.message}</div>}
                                        </div>
                                    </td>
                                    <td>
                                        <span className="date-text">
                                            {new Date(job.created_at).toLocaleString()}
                                        </span>
                                    </td>
                                    <td>
                                        <span className="duration-text">
                                            {job.completed_at && job.started_at
                                                ? `${Math.round((new Date(job.completed_at).getTime() - new Date(job.started_at).getTime()) / 1000)}s`
                                                : '-'}
                                        </span>
                                    </td>
                                    <td>
                                        <div className="action-buttons">
                                            <Link to={`/jobs/${job.id}`} className="btn btn-icon btn-secondary" title="View">
                                                <Eye size={16} />
                                            </Link>
                                            {(job.status === 'PENDING' || job.status === 'RUNNING') && (
                                                <button
                                                    className="btn btn-icon btn-secondary"
                                                    onClick={(e) => handleCancel(job.id, e)}
                                                    title="Cancel"
                                                >
                                                    <XCircle size={16} />
                                                </button>
                                            )}
                                            {job.status === 'FAILED' && (
                                                <button
                                                    className="btn btn-icon btn-secondary"
                                                    onClick={(e) => handleRetry(job.id, e)}
                                                    title="Retry"
                                                >
                                                    <RotateCcw size={16} />
                                                </button>
                                            )}
                                            {job.status !== 'RUNNING' && (
                                                <button
                                                    className="btn btn-icon btn-danger"
                                                    onClick={(e) => handleDelete(job.id, e)}
                                                    title="Delete"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="pagination">
                    <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                    >
                        <ChevronLeft size={16} />
                        Previous
                    </button>
                    <span className="pagination-info">
                        Page {page} of {totalPages} ({total} jobs)
                    </span>
                    <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                    >
                        Next
                        <ChevronRight size={16} />
                    </button>
                </div>
            )}
        </div>
    );
}
