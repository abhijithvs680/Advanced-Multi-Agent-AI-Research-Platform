import type { JobStatus } from '../types';
import './StatusBadge.css';

interface StatusBadgeProps {
    status: JobStatus;
    showIcon?: boolean;
}

export default function StatusBadge({ status, showIcon = true }: StatusBadgeProps) {
    return (
        <span className={`status-badge status-${status}`}>
            {showIcon && <span className="status-dot" />}
            {status}
        </span>
    );
}
