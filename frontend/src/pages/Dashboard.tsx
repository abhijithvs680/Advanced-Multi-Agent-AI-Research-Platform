import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    Briefcase,
    Clock,
    CheckCircle,
    XCircle,
    TrendingUp,
    ArrowRight,
    Zap
} from 'lucide-react';
import { api } from '../api/client';
import type { MetricsResponse, Job } from '../types';
import StatusBadge from '../components/StatusBadge';
import './Dashboard.css';

interface DashboardProps {
    addToast: (message: string, type: 'success' | 'error' | 'warning') => void;
}

export default function Dashboard({ addToast }: DashboardProps) {
    const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
    const [recentJobs, setRecentJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [metricsData, jobsData] = await Promise.all([
                    api.getMetrics(),
                    api.listJobs({ page_size: 5 })
                ]);
                setMetrics(metricsData);
                setRecentJobs(jobsData.jobs);
            } catch (err) {
                addToast('Failed to load dashboard data', 'error');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, [addToast]);

    if (loading) {
        return (
            <div className="loading">
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div className="dashboard">
            <div className="page-header">
                <h1 className="page-title">Dashboard</h1>
                <p className="page-subtitle">Monitor your AI research workflows in real-time</p>
            </div>

            {/* Metrics Grid */}
            <div className="metrics-grid">
                <div className="metric-card accent">
                    <div className="metric-icon">
                        <Briefcase size={24} />
                    </div>
                    <div className="metric-content">
                        <div className="metric-value">{metrics?.queue_length || 0}</div>
                        <div className="metric-label">Queue Length</div>
                    </div>
                </div>

                <div className="metric-card">
                    <div className="metric-icon running">
                        <Zap size={24} />
                    </div>
                    <div className="metric-content">
                        <div className="metric-value">{metrics?.running_jobs || 0}</div>
                        <div className="metric-label">Running Jobs</div>
                    </div>
                </div>

                <div className="metric-card">
                    <div className="metric-icon success">
                        <CheckCircle size={24} />
                    </div>
                    <div className="metric-content">
                        <div className="metric-value">{metrics?.completed_jobs_24h || 0}</div>
                        <div className="metric-label">Completed (24h)</div>
                    </div>
                </div>

                <div className="metric-card">
                    <div className="metric-icon error">
                        <XCircle size={24} />
                    </div>
                    <div className="metric-content">
                        <div className="metric-value">{metrics?.failed_jobs_24h || 0}</div>
                        <div className="metric-label">Failed (24h)</div>
                    </div>
                </div>

                <div className="metric-card wide">
                    <div className="metric-icon">
                        <Clock size={24} />
                    </div>
                    <div className="metric-content">
                        <div className="metric-value">
                            {metrics?.average_duration_minutes?.toFixed(1) || '0'} min
                        </div>
                        <div className="metric-label">Average Duration</div>
                    </div>
                </div>

                <div className="metric-card wide">
                    <div className="metric-icon success">
                        <TrendingUp size={24} />
                    </div>
                    <div className="metric-content">
                        <div className="metric-value">
                            {metrics && metrics.completed_jobs_24h + metrics.failed_jobs_24h > 0
                                ? Math.round((metrics.completed_jobs_24h / (metrics.completed_jobs_24h + metrics.failed_jobs_24h)) * 100)
                                : 0}%
                        </div>
                        <div className="metric-label">Success Rate (24h)</div>
                    </div>
                </div>
            </div>

            {/* Recent Jobs */}
            <div className="recent-jobs-section">
                <div className="section-header">
                    <h2 className="section-title">Recent Jobs</h2>
                    <Link to="/jobs" className="btn btn-secondary btn-sm">
                        View All <ArrowRight size={14} />
                    </Link>
                </div>

                <div className="jobs-list">
                    {recentJobs.length === 0 ? (
                        <div className="empty-state">
                            <Briefcase size={48} className="empty-state-icon" />
                            <p>No jobs yet. Create your first research job!</p>
                            <Link to="/create-job" className="btn btn-primary mt-4">
                                Create Job
                            </Link>
                        </div>
                    ) : (
                        recentJobs.map(job => (
                            <Link to={`/jobs/${job.id}`} key={job.id} className="job-card">
                                <div className="job-main">
                                    <div className="job-title">{job.topic}</div>
                                    <div className="job-meta">
                                        <span className="job-domain">{job.domain}</span>
                                        <span className="job-time">
                                            {new Date(job.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                                <div className="job-status-container">
                                    <StatusBadge status={job.status} />
                                    {job.status === 'RUNNING' && job.progress !== undefined && (
                                        <div className="job-progress-mini">
                                            <div className="progress-bar-fill" style={{ width: `${job.progress}%` }} />
                                        </div>
                                    )}
                                </div>
                            </Link>
                        ))
                    )}
                </div>
            </div>

            {/* Quick Actions */}
            <div className="quick-actions">
                <h2 className="section-title">Quick Actions</h2>
                <div className="actions-grid">
                    <Link to="/create-job" className="action-card">
                        <div className="action-icon">
                            <Briefcase size={24} />
                        </div>
                        <div className="action-content">
                            <div className="action-title">New Research Job</div>
                            <div className="action-desc">Start a new AI research workflow</div>
                        </div>
                        <ArrowRight size={20} className="action-arrow" />
                    </Link>
                </div>
            </div>
        </div>
    );
}
