import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Briefcase, Globe, Settings as SettingsIcon, Zap } from 'lucide-react';
import { api } from '../api/client';
import './CreateJob.css';

interface CreateJobProps {
    addToast: (message: string, type: 'success' | 'error' | 'warning') => void;
}

const DOMAIN_SUGGESTIONS = [
    'AI', 'Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision',
    'Robotics', 'Healthcare', 'Finance', 'Biotechnology', 'Climate'
];

export default function CreateJob({ addToast }: CreateJobProps) {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        topic: '',
        domain: '',
        priority: 0
    });
    const [submitting, setSubmitting] = useState(false);
    const [showAdvanced, setShowAdvanced] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!formData.topic.trim() || !formData.domain.trim()) {
            addToast('Please fill in all required fields', 'warning');
            return;
        }

        setSubmitting(true);
        try {
            const job = await api.createJob({
                topic: formData.topic.trim(),
                domain: formData.domain.trim(),
                priority: formData.priority
            });
            addToast('Job created successfully!', 'success');
            navigate(`/jobs/${job.id}`);
        } catch (err: any) {
            addToast(err.message || 'Failed to create job', 'error');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="create-job-page">
            <div className="page-header">
                <h1 className="page-title">Create New Research Job</h1>
                <p className="page-subtitle">Define your research topic and domain to start an autonomous AI workflow</p>
            </div>

            <div className="create-container">
                <form onSubmit={handleSubmit} className="create-form card">
                    {/* Topic Field */}
                    <div className="form-group">
                        <label className="form-label">
                            <Briefcase size={16} />
                            Research Topic *
                        </label>
                        <input
                            type="text"
                            className="form-input"
                            placeholder="e.g., Transformer architectures for time series forecasting"
                            value={formData.topic}
                            onChange={(e) => setFormData({ ...formData, topic: e.target.value })}
                            maxLength={255}
                            required
                        />
                        <div className="form-hint">
                            Describe the research topic you want the AI agents to investigate
                        </div>
                    </div>

                    {/* Domain Field */}
                    <div className="form-group">
                        <label className="form-label">
                            <Globe size={16} />
                            Domain *
                        </label>
                        <input
                            type="text"
                            className="form-input"
                            placeholder="e.g., Machine Learning"
                            value={formData.domain}
                            onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                            maxLength={100}
                            required
                        />
                        <div className="domain-suggestions">
                            {DOMAIN_SUGGESTIONS.map(domain => (
                                <button
                                    key={domain}
                                    type="button"
                                    className={`domain-tag ${formData.domain === domain ? 'active' : ''}`}
                                    onClick={() => setFormData({ ...formData, domain })}
                                >
                                    {domain}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Advanced Settings Toggle */}
                    <button
                        type="button"
                        className="advanced-toggle"
                        onClick={() => setShowAdvanced(!showAdvanced)}
                    >
                        <SettingsIcon size={16} />
                        {showAdvanced ? 'Hide' : 'Show'} Advanced Settings
                    </button>

                    {/* Advanced Settings */}
                    {showAdvanced && (
                        <div className="advanced-settings">
                            <div className="form-group">
                                <label className="form-label">
                                    <Zap size={16} />
                                    Priority
                                </label>
                                <select
                                    className="form-select"
                                    value={formData.priority}
                                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) })}
                                >
                                    <option value={0}>Normal</option>
                                    <option value={1}>High</option>
                                    <option value={2}>Urgent</option>
                                </select>
                                <div className="form-hint">
                                    Higher priority jobs are processed first
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Submit Button */}
                    <div className="form-actions">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={() => navigate('/jobs')}
                            disabled={submitting}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            className="btn btn-primary"
                            disabled={submitting || !formData.topic.trim() || !formData.domain.trim()}
                        >
                            {submitting ? (
                                <>
                                    <div className="spinner" style={{ width: 18, height: 18 }} />
                                    Creating...
                                </>
                            ) : (
                                <>
                                    <Send size={18} />
                                    Create Job
                                </>
                            )}
                        </button>
                    </div>
                </form>

                {/* Info Panel */}
                <div className="info-panel">
                    <div className="info-card card">
                        <h3>What happens next?</h3>
                        <ol className="info-steps">
                            <li>
                                <span className="step-icon">🔍</span>
                                <div>
                                    <strong>Research Phase</strong>
                                    <p>AI agents search literature and analyze relevant papers</p>
                                </div>
                            </li>
                            <li>
                                <span className="step-icon">📊</span>
                                <div>
                                    <strong>Data Collection</strong>
                                    <p>Gather and preprocess datasets for experiments</p>
                                </div>
                            </li>
                            <li>
                                <span className="step-icon">🎯</span>
                                <div>
                                    <strong>Model Training</strong>
                                    <p>Train multiple models with hyperparameter optimization</p>
                                </div>
                            </li>
                            <li>
                                <span className="step-icon">📈</span>
                                <div>
                                    <strong>Evaluation</strong>
                                    <p>Compare results and select the best model</p>
                                </div>
                            </li>
                        </ol>
                    </div>
                </div>
            </div>
        </div>
    );
}
