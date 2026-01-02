import React, { useState, useEffect } from 'react';
import { Search, Database, Zap, Award, History } from 'lucide-react';
import './WorkflowDataTabs.css';

import ResearchResultsPanel from './ResearchResultsPanel';
import DataCollectionPanel from './DataCollectionPanel';
import TrainingProgressPanel from './TrainingProgressPanel';
import EvaluationResultsPanel from './EvaluationResultsPanel';

interface WorkflowDataTabsProps {
    jobId: string;
    stageResults: Record<string, any>;
    currentState: string;
    progress: number;
}

type TabType = 'research' | 'data' | 'training' | 'evaluation' | 'history';

export default function WorkflowDataTabs({
    jobId,
    stageResults,
    currentState,
    progress
}: WorkflowDataTabsProps) {
    const [activeTab, setActiveTab] = useState<TabType>('research');

    // Automatically switch tabs based on current state transitions
    useEffect(() => {
        if (currentState === 'RESEARCHING') setActiveTab('research');
        if (currentState === 'COLLECTING_DATA') setActiveTab('data');
        if (currentState === 'TRAINING') setActiveTab('training');
        if (currentState === 'EVALUATING') setActiveTab('evaluation');
        if (currentState === 'COMPLETED') setActiveTab('evaluation');
    }, [currentState]);

    const tabs = [
        { id: 'research', label: 'Research', icon: <Search size={16} /> },
        { id: 'data', label: 'Data', icon: <Database size={16} /> },
        { id: 'training', label: 'Training', icon: <Zap size={16} /> },
        { id: 'evaluation', label: 'Evaluation', icon: <Award size={16} /> }
    ];

    const getTabStatus = (tabId: string) => {
        const stateMap: Record<string, string[]> = {
            research: ['RESEARCHING'],
            data: ['COLLECTING_DATA'],
            training: ['TRAINING'],
            evaluation: ['EVALUATING', 'COMPLETED']
        };

        if (stateMap[tabId].includes(currentState)) return 'active';
        if (stageResults[tabId]) return 'completed';
        return 'pending';
    };

    return (
        <div className="workflow-data-tabs card">
            <div className="tabs-header">
                <div className="tabs-list">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            className={`tab-item ${activeTab === tab.id ? 'active' : ''} ${getTabStatus(tab.id)}`}
                            onClick={() => setActiveTab(tab.id as TabType)}
                        >
                            {tab.icon}
                            <span>{tab.label}</span>
                            {getTabStatus(tab.id) === 'active' && <span className="status-dot pulse" />}
                        </button>
                    ))}
                </div>
            </div>

            <div className="tab-panel">
                {activeTab === 'research' && (
                    <ResearchResultsPanel data={stageResults.research} />
                )}
                {activeTab === 'data' && (
                    <DataCollectionPanel data={stageResults.data} />
                )}
                {activeTab === 'training' && (
                    <TrainingProgressPanel
                        data={stageResults.training}
                        progress={currentState === 'TRAINING' ? progress : 100}
                    />
                )}
                {activeTab === 'evaluation' && (
                    <EvaluationResultsPanel data={stageResults.evaluation} />
                )}
            </div>
        </div>
    );
}
