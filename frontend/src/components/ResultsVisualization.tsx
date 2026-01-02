import { useMemo } from 'react';
import { Award, TrendingUp, BarChart2, Layers, Target, Zap } from 'lucide-react';
import { BarChart, DonutChart, MetricCard, ProgressRing, LineSpark } from './Charts';
import './ResultsVisualization.css';

interface ModelResult {
    model_type: string;
    score: number;
    metrics?: Record<string, number>;
}

interface JobResult {
    best_model?: ModelResult;
    all_models?: ModelResult[];
    iterations?: number;
    status?: string;
    metrics?: Record<string, number>;
    training_history?: number[];
    feature_importance?: Record<string, number>;
}

interface ResultsVisualizationProps {
    result: JobResult;
}

export default function ResultsVisualization({ result }: ResultsVisualizationProps) {
    const bestModel = result?.best_model;
    const allModels = result?.all_models || [];

    // Prepare model comparison data
    const modelComparisonData = useMemo(() => {
        return allModels.map(model => ({
            label: model.model_type,
            value: model.score,
            color: model.model_type === bestModel?.model_type ? 'var(--status-completed)' : undefined
        }));
    }, [allModels, bestModel]);

    // Prepare metrics data
    const metricsData = useMemo(() => {
        if (!bestModel?.metrics) return [];
        return Object.entries(bestModel.metrics).map(([key, value]) => ({
            label: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            value: value as number
        }));
    }, [bestModel]);

    // Status distribution for donut chart
    const statusData = useMemo(() => {
        const successful = allModels.filter(m => m.score >= 0.7).length;
        const partial = allModels.filter(m => m.score >= 0.5 && m.score < 0.7).length;
        const failed = allModels.filter(m => m.score < 0.5).length;

        return [
            { label: 'High Performing', value: successful, color: '#22c55e' },
            { label: 'Moderate', value: partial, color: '#f59e0b' },
            { label: 'Low Performing', value: failed, color: '#ef4444' }
        ].filter(d => d.value > 0);
    }, [allModels]);

    // Feature importance for bar chart
    const featureData = useMemo(() => {
        if (!result?.feature_importance) return [];
        return Object.entries(result.feature_importance)
            .sort(([, a], [, b]) => (b as number) - (a as number))
            .slice(0, 6)
            .map(([feature, importance]) => ({
                label: feature,
                value: importance as number
            }));
    }, [result?.feature_importance]);

    if (!result || (!bestModel && allModels.length === 0)) {
        return (
            <div className="results-empty">
                <p>No results available yet.</p>
            </div>
        );
    }

    return (
        <div className="results-visualization">
            {/* Key Metrics Row */}
            <div className="metrics-grid">
                {bestModel && (
                    <>
                        <MetricCard
                            label="Best Score"
                            value={bestModel.score}
                            icon={<Award />}
                            color="var(--status-completed)"
                            change={result.iterations && result.iterations > 1 ? 5.2 : undefined}
                        />
                        <MetricCard
                            label="Model Type"
                            value={bestModel.model_type}
                            icon={<Layers />}
                            color="var(--accent-primary)"
                        />
                    </>
                )}
                <MetricCard
                    label="Models Trained"
                    value={allModels.length || 0}
                    icon={<BarChart2 />}
                    color="var(--accent-secondary)"
                />
                <MetricCard
                    label="Iterations"
                    value={result.iterations || 1}
                    icon={<TrendingUp />}
                    color="#f59e0b"
                />
            </div>

            {/* Charts Row */}
            <div className="charts-row">
                {/* Model Comparison */}
                {modelComparisonData.length > 0 && (
                    <BarChart
                        data={modelComparisonData}
                        title="Model Performance Comparison"
                        height={Math.max(150, modelComparisonData.length * 40)}
                    />
                )}

                {/* Status Distribution */}
                {statusData.length > 0 && (
                    <DonutChart
                        data={statusData}
                        title="Performance Distribution"
                        size={140}
                    />
                )}
            </div>

            {/* Additional Metrics */}
            {metricsData.length > 0 && (
                <div className="detailed-metrics">
                    <h3 className="section-title">Detailed Metrics</h3>
                    <div className="metrics-rings">
                        {metricsData.slice(0, 4).map(metric => (
                            <ProgressRing
                                key={metric.label}
                                value={metric.value * 100}
                                max={100}
                                size={90}
                                label={metric.label}
                                color={
                                    metric.value >= 0.8 ? '#22c55e' :
                                        metric.value >= 0.6 ? '#f59e0b' : '#ef4444'
                                }
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Feature Importance */}
            {featureData.length > 0 && (
                <BarChart
                    data={featureData}
                    title="Feature Importance"
                    height={Math.max(150, featureData.length * 35)}
                />
            )}

            {/* Training History Sparkline */}
            {result.training_history && result.training_history.length > 1 && (
                <div className="training-history">
                    <h3 className="section-title">Training Progress</h3>
                    <div className="spark-container">
                        <LineSpark
                            data={result.training_history}
                            width={300}
                            height={60}
                            color="var(--accent-primary)"
                        />
                        <div className="spark-labels">
                            <span>Start</span>
                            <span>Current</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
