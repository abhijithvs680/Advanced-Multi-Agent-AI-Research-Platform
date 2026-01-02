import { useState, useEffect } from 'react';
import { Bell, User, Search, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import type { ReadinessResponse } from '../types';
import './Header.css';

export default function Header() {
    const [readiness, setReadiness] = useState<ReadinessResponse | null>(null);

    useEffect(() => {
        const fetchReadiness = async () => {
            try {
                const data = await api.getReadiness();
                setReadiness(data);
            } catch (err) {
                setReadiness(null);
            }
        };

        fetchReadiness();
        const interval = setInterval(fetchReadiness, 30000);
        return () => clearInterval(interval);
    }, []);

    const StatusIcon = ({ ready }: { ready: boolean | undefined }) => {
        if (ready === undefined) return <AlertCircle size={14} className="status-unknown" />;
        return ready ?
            <CheckCircle size={14} className="status-ok" /> :
            <XCircle size={14} className="status-error" />;
    };

    return (
        <header className="header">
            {/* Search */}
            <div className="header-search">
                <Search size={18} className="search-icon" />
                <input
                    type="text"
                    placeholder="Search jobs, topics..."
                    className="search-input"
                />
            </div>

            {/* Right Section */}
            <div className="header-right">
                {/* Service Status */}
                <div className="service-status">
                    <div className="status-item" title="Database">
                        <StatusIcon ready={readiness?.database} />
                        <span>DB</span>
                    </div>
                    <div className="status-item" title="Queue">
                        <StatusIcon ready={readiness?.queue} />
                        <span>Queue</span>
                    </div>
                    <div className="status-item" title="MLflow">
                        <StatusIcon ready={readiness?.mlflow} />
                        <span>MLflow</span>
                    </div>
                </div>

                {/* Notifications */}
                <button className="header-btn">
                    <Bell size={20} />
                    <span className="notification-badge">3</span>
                </button>

                {/* User */}
                <button className="header-btn user-btn">
                    <User size={20} />
                </button>
            </div>
        </header>
    );
}
