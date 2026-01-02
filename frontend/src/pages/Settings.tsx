import { useState, useEffect } from 'react';
import { RefreshCw, ExternalLink, Server, Database, Cpu, Wifi } from 'lucide-react';
import { api } from '../api/client';
import type { HealthResponse, ReadinessResponse, MetricsResponse } from '../types';
import './Settings.css';

export default function Settings() {
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);
    const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
    const [refreshing, setRefreshing] = useState(false);

    const fetchStatus = async () => {
        setRefreshing(true);
        try {
            const [h, r, m] = await Promise.all([
                api.getHealth(),
                api.getReadiness(),
                api.getMetrics()
            ]);
            setHealth(h);
            setReadiness(r);
            setMetrics(m);
        } catch (err) {
            console.error('Failed to fetch status:', err);
        } finally {
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 30000);
        return () => clearInterval(interval);
    }, []);

    const services = [
        { name: 'API Server', url: 'http://localhost:8000/docs', icon: <Server size={20} />, status: health?.status === 'healthy' },
        { name: 'PostgreSQL', url: null, icon: <Database size={20} />, status: readiness?.database },
        { name: 'Redis Queue', url: null, icon: <Cpu size={20} />, status: readiness?.queue },
        { name: 'MLflow', url: 'http://localhost:5000', icon: <Wifi size={20} />, status: readiness?.mlflow },
    ];

    return (
        <div className="settings-page">
            <div className="page-header">
                <div>
                    <h1 className="page-title">Settings & Status</h1>
                    <p className="page-subtitle">System configuration and service health</p>
                </div>
                <button
                    className="btn btn-secondary"
                    onClick={fetchStatus}
                    disabled={refreshing}
                >
                    <RefreshCw size={18} className={refreshing ? 'spin' : ''} />
                    Refresh
                </button>
            </div>

            {/* System Health */}
            <div className="card">
                <h2 className="card-title">System Health</h2>
                <div className="services-grid">
                    {services.map(service => (
                        <div key={service.name} className="service-card">
                            <div className="service-icon">{service.icon}</div>
                            <div className="service-info">
                                <div className="service-name">{service.name}</div>
                                <div className={`service-status ${service.status ? 'online' : 'offline'}`}>
                                    <span className="status-dot" />
                                    {service.status ? 'Online' : 'Offline'}
                                </div>
                            </div>
                            {service.url && (
                                <a
                                    href={service.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="service-link"
                                >
                                    <ExternalLink size={16} />
                                </a>
                            )}
                        </div>
                    ))}
                </div>
            </div>

            {/* API Information */}
            <div className="card">
                <h2 className="card-title">API Information</h2>
                <div className="info-grid">
                    <div className="info-item">
                        <span className="info-label">Version</span>
                        <span className="info-value">{health?.version || '-'}</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Base URL</span>
                        <span className="info-value">http://localhost:8000/api/v1</span>
                    </div>
                    <div className="info-item">
                        <span className="info-label">Documentation</span>
                        <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer" className="info-link">
                            OpenAPI Docs <ExternalLink size={14} />
                        </a>
                    </div>
                </div>
            </div>

            {/* Quick Stats */}
            {metrics && (
                <div className="card">
                    <h2 className="card-title">Current Statistics</h2>
                    <div className="stats-grid">
                        <div className="stat-item">
                            <div className="stat-value">{metrics.queue_length}</div>
                            <div className="stat-label">Queue Length</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">{metrics.running_jobs}</div>
                            <div className="stat-label">Running Jobs</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">{metrics.completed_jobs_24h}</div>
                            <div className="stat-label">Completed (24h)</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">{metrics.failed_jobs_24h}</div>
                            <div className="stat-label">Failed (24h)</div>
                        </div>
                    </div>
                </div>
            )}

            {/* External Links */}
            <div className="card">
                <h2 className="card-title">External Services</h2>
                <div className="links-grid">
                    <a href="http://localhost:5000" target="_blank" rel="noopener noreferrer" className="link-card">
                        <div className="link-icon">📊</div>
                        <div className="link-info">
                            <div className="link-name">MLflow</div>
                            <div className="link-desc">Experiment Tracking</div>
                        </div>
                        <ExternalLink size={16} />
                    </a>
                    <a href="http://localhost:9090" target="_blank" rel="noopener noreferrer" className="link-card">
                        <div className="link-icon">📈</div>
                        <div className="link-info">
                            <div className="link-name">Prometheus</div>
                            <div className="link-desc">Metrics Dashboard</div>
                        </div>
                        <ExternalLink size={16} />
                    </a>
                    <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" className="link-card">
                        <div className="link-icon">📉</div>
                        <div className="link-info">
                            <div className="link-name">Grafana</div>
                            <div className="link-desc">Visualization</div>
                        </div>
                        <ExternalLink size={16} />
                    </a>
                </div>
            </div>
        </div>
    );
}
