import React from 'react';
import { Database, FileText, Activity, AlertCircle } from 'lucide-react';
import { DataStageResults } from '../types';
import { MetricCard, ProgressRing, BarChart } from './Charts';

interface DataCollectionPanelProps {
    data?: DataStageResults;
}

export default function DataCollectionPanel({ data }: DataCollectionPanelProps) {
    if (!data) {
        return (
            <div className="stage-pending">
                <Database className="spin" size={32} />
                <p>Data collection stage in progress or pending...</p>
            </div>
        );
    }

    const qualityMetrics = [
        { label: 'Missing Values (avg)', value: Object.values(data.data_quality?.missing_values || {}).reduce((a, b) => a + b, 0) / (Object.keys(data.data_quality?.missing_values || {}).length || 1) },
        { label: 'High Correlations', value: Object.values(data.data_quality?.correlations || {}).filter(c => Math.abs(c) > 0.8).length },
        { label: 'Detected Outliers', value: Object.values(data.data_quality?.outliers || {}).reduce((a, b) => a + b, 0) }
    ];

    const missingData = Object.entries(data.data_quality?.missing_values || {})
        .slice(0, 5)
        .map(([key, val]) => ({ label: key, value: val * 100 }));

    return (
        <div className="stage-panel data-panel">
            {/* Metric Overview */}
            <div className="metrics-grid">
                <MetricCard
                    label="Total Samples"
                    value={data.summary?.total_samples || 0}
                    icon={<FileText />}
                    color="var(--accent-primary)"
                />
                <MetricCard
                    label="Feature Count"
                    value={data.summary?.features?.length || 0}
                    icon={<Activity />}
                    color="var(--accent-secondary)"
                />
                <div className="quality-score-container card-bg">
                    <ProgressRing
                        value={(data.summary?.quality_score || 0) * 100}
                        label="Data Quality"
                        size={100}
                        color={(data.summary?.quality_score || 0) > 0.8 ? '#22c55e' : '#f59e0b'}
                    />
                </div>
            </div>

            <div className="panel-row">
                {/* Missing values distribution */}
                {missingData.length > 0 && (
                    <div className="panel-section half-width">
                        <h3 className="section-title">
                            <AlertCircle size={16} /> Missing Values (%)
                        </h3>
                        <div className="">
                            <BarChart
                                data={missingData}
                                height={180}
                                showValues={true}
                            />
                        </div>
                    </div>
                )}

                {/* Summary list */}
                <div className="panel-section half-width">
                    <h3 className="section-title">Stage Metadata</h3>
                    <div className="metadata-list card-bg">
                        <div className="metadata-item">
                            <span>Target Variable</span>
                            <span className="badge">{data.summary?.target || 'N/A'}</span>
                        </div>
                        <div className="metadata-item">
                            <span>High Correlation Features</span>
                            <span>{qualityMetrics[1].value}</span>
                        </div>
                        <div className="metadata-item">
                            <span>Features Analyzed</span>
                            <span>{data.summary?.features?.length || 0}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
