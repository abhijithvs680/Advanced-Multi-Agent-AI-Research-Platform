import React from 'react';
import { Award, BarChart3, ListTree, Info } from 'lucide-react';
import { EvaluationStageResults } from '../types';
import { BarChart, MetricCard } from './Charts';

interface EvaluationResultsPanelProps {
    data?: EvaluationStageResults;
}

export default function EvaluationResultsPanel({ data }: EvaluationResultsPanelProps) {
    if (!data) {
        return (
            <div className="stage-pending">
                < Award className="spin" size={32} />
                <p>Evaluating best models... (Final Stage)</p>
            </div>
        );
    }

    const importanceData = Object.entries(data.feature_importance || {})
        .sort((a, b) => b[1] - a[1])
        .slice(0, 8)
        .map(([key, val]) => ({ label: key, value: val }));

    return (
        <div className="stage-panel evaluation-panel">
            {/* Recommendation Card */}
            <div className="recommendation-hero card-bg border-accent">
                <div className="hero-icon">
                    <Award size={48} color="var(--accent-primary)" />
                </div>
                <div className="hero-content">
                    <div className="hero-label">Recommended Model</div>
                    <div className="hero-value">{data.recommendation?.model_type ?? 'Pending'}</div>
                    <div className="hero-score">Overall Score: {data.recommendation?.score != null ? (data.recommendation.score * 100).toFixed(1) : 'N/A'}%</div>
                    <p className="hero-reasoning">
                        <Info size={14} className="inline mr-1" />
                        {data.recommendation?.reasoning ?? 'Evaluation in progress...'}
                    </p>
                </div>
            </div>

            <div className="panel-row">
                {/* Feature Importance */}
                <div className="panel-section half-width">
                    <h3 className="section-title">
                        <ListTree size={16} /> Feature Importance
                    </h3>
                    <div className="">
                        <BarChart data={importanceData} height={250} />
                    </div>
                </div>

                {/* Rank Comparison */}
                <div className="panel-section half-width">
                    <h3 className="section-title">
                        <BarChart3 size={16} /> Detailed Ranking
                    </h3>
                    <div className="comparison-table-container card-bg">
                        <table className="comparison-table">
                            <thead>
                                <tr>
                                    <th>Rank</th>
                                    <th>Model Type</th>
                                    <th>Score</th>
                                </tr>
                            </thead>
                            <tbody>
                                {(data.comparisons || []).map((c) => (
                                    <tr key={c.model_type} className={c.rank === 1 ? 'rank-1' : ''}>
                                        <td>#{c.rank}</td>
                                        <td>{c.model_type}</td>
                                        <td>{c.metrics && Object.values(c.metrics).length > 0 ? (Object.values(c.metrics)[0] * 100).toFixed(1) : 'N/A'}%</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    );
}
