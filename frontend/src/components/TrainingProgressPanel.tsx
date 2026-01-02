import React from 'react';
import { Zap, Target, ShieldCheck, Timer, BarChart as BarChartIcon } from 'lucide-react';
import { TrainingStageResults } from '../types';
import { MetricCard, BarChart } from './Charts';

interface TrainingProgressPanelProps {
    data?: TrainingStageResults | Record<string, any>;
    progress?: number;
}

export default function TrainingProgressPanel({ data, progress }: TrainingProgressPanelProps) {
    if (!data || Object.keys(data).length === 0) {
        return (
            <div className="stage-pending">
                <Zap className="spin" size={32} />
                <p>Training models... ({progress?.toFixed(0) || 0}%)</p>
                <div className="overall-progress-bar">
                    <div
                        className="progress-fill"
                        style={{ width: `${progress || 0}%` }}
                    />
                </div>
            </div>
        );
    }

    // Identify valid model entries (must contain metric accuracy/f1/etc)
    const allKeys = Object.keys(data);
    const modelTypes = allKeys.filter(key => {
        const item = data[key];
        return typeof item === 'object' && item !== null && (
            'accuracy' in item || 'f1' in item || 'auc_roc' in item
        );
    });

    const hasDetailedModels = modelTypes.length > 0;
    const latestModelKey = hasDetailedModels ? modelTypes[modelTypes.length - 1] : null;
    const latestModel = latestModelKey ? data[latestModelKey] : null;

    // Fallback: Check for raw summary metrics if no detailed models found
    if (!hasDetailedModels) {
        const rawMetrics = data as Record<string, any>;
        // If we have at least some summary metrics, display them
        if (rawMetrics.best_score !== undefined || rawMetrics.models_trained !== undefined) {
            return (
                <div className="stage-panel training-panel">
                    <div className="metrics-grid">
                        <MetricCard
                            label="Best Accuracy"
                            value={rawMetrics.best_score ?? 'N/A'}
                            icon={<Target />}
                            color="#22c55e"
                        />
                        <MetricCard
                            label="Models Trained"
                            value={rawMetrics.models_trained ?? 0}
                            icon={<BarChartIcon />}
                            color="var(--accent-primary)"
                        />
                        <MetricCard
                            label="Training Time"
                            value={rawMetrics.total_training_time ? `${Number(rawMetrics.total_training_time).toFixed(1)}s` : 'N/A'}
                            icon={<Timer />}
                            color="var(--text-secondary)"
                        />
                    </div>
                    <div className="panel-section">
                        <div className="alert-info">
                            Detailed model comparisons are not available for this job.
                        </div>
                    </div>
                </div>
            );
        }

        return <div className="stage-pending">Waiting for training metrics...</div>;
    }

    const comparisonData = modelTypes.map(type => ({
        label: type,
        value: data[type].accuracy
    }));

    return (
        <div className="stage-panel training-panel">
            {/* Latest Trained Model Metrics */}
            <div className="metrics-grid">
                <MetricCard
                    label="Latest Accuracy"
                    value={latestModel.accuracy ?? 'N/A'}
                    icon={<Target />}
                    color="#22c55e"
                />
                <MetricCard
                    label="F1 Score"
                    value={latestModel.f1 ?? 'N/A'}
                    icon={<ShieldCheck />}
                    color="var(--accent-primary)"
                />
                <MetricCard
                    label="AUC-ROC"
                    value={latestModel.auc_roc ?? 'N/A'}
                    icon={<Zap />}
                    color="#f59e0b"
                />
                <MetricCard
                    label="Training Time"
                    value={latestModel.training_time != null ? `${latestModel.training_time.toFixed(1)}s` : 'N/A'}
                    icon={<Timer />}
                    color="var(--text-secondary)"
                />
            </div>

            {/* Model Comparison */}
            <div className="panel-section">
                <h3 className="section-title">Model Comparison (Accuracy)</h3>
                <div className="card-bg p-4">
                    <BarChart
                        data={comparisonData}
                        height={Math.max(160, modelTypes.length * 40)}
                    />
                </div>
            </div>

            {/* Hyperparameters */}
            <div className="panel-section">
                <h3 className="section-title">Latest Hyperparameters ({latestModelKey})</h3>
                <div className="params-grid card-bg">
                    {Object.entries(latestModel.params || {}).map(([param, val]) => (
                        <div key={param} className="param-item">
                            <span className="param-name">{param}</span>
                            <span className="param-value">{String(val)}</span>
                        </div>
                    ))}
                    {(!latestModel.params || Object.keys(latestModel.params).length === 0) && (
                        <div className="param-item"><span className="param-name">No hyperparameters available</span></div>
                    )}
                </div>
            </div>
        </div>
    );
}
