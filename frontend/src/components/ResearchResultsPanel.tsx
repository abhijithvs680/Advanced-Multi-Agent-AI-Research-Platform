import React from 'react';
import { Search, BookOpen, Lightbulb, CheckCircle2 } from 'lucide-react';
import { ResearchStageResults } from '../types';

interface ResearchResultsPanelProps {
    data?: ResearchStageResults;
}

export default function ResearchResultsPanel({ data }: ResearchResultsPanelProps) {
    if (!data) {
        return (
            <div className="stage-pending">
                <Search className="spin" size={32} />
                <p>Research stage in progress or pending...</p>
            </div>
        );
    }

    return (
        <div className="stage-panel research-panel">
            {/* Summary Section */}
            <div className="panel-section">
                <h3 className="section-title">
                    <BookOpen size={16} /> Literature Summary
                </h3>
                <div className="summary-content card-bg">
                    <p>{data.summary}</p>
                </div>
            </div>

            {/* Key Findings */}
            <div className="panel-section">
                <h3 className="section-title">
                    <CheckCircle2 size={16} /> Key Findings
                </h3>
                <div className="findings-list grid-auto">
                    {data.key_findings?.map((finding, idx) => (
                        <div key={idx} className="finding-item card-bg">
                            <span className="finding-bullet">•</span>
                            <span className="finding-text">{finding}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Hypotheses */}
            {data.hypotheses && data.hypotheses.length > 0 && (
                <div className="panel-section">
                    <h3 className="section-title">
                        <Lightbulb size={16} /> Generated Hypotheses
                    </h3>
                    <div className="hypotheses-grid">
                        {data.hypotheses.map((h, idx) => (
                            <div key={idx} className="hypothesis-card card-bg">
                                <div className="hypothesis-header">
                                    <span className="hypothesis-tag">H{idx + 1}</span>
                                    <div className="confidence-badge" title="Confidence Score">
                                        {((h.confidence || 0) * 100).toFixed(0)}% Confidence
                                    </div>
                                </div>
                                <p className="hypothesis-statement">{h.statement}</p>
                                <div className="hypothesis-rationale">
                                    <strong>Rationale:</strong> {h.rationale}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
