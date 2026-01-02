import { useMemo } from 'react';
import './Charts.css';

interface DataPoint {
    label: string;
    value: number;
    color?: string;
}

interface BarChartProps {
    data: DataPoint[];
    title?: string;
    height?: number;
    showValues?: boolean;
}

export function BarChart({ data, title, height = 200, showValues = true }: BarChartProps) {
    const maxValue = useMemo(() => Math.max(...data.map(d => d.value), 1), [data]);

    const defaultColors = [
        'var(--accent-primary)',
        'var(--status-completed)',
        'var(--accent-secondary)',
        '#f59e0b',
        '#8b5cf6',
        '#ec4899'
    ];

    return (
        <div className="chart bar-chart">
            {title && <h3 className="chart-title">{title}</h3>}
            <div className="bar-chart-container" style={{ height }}>
                {data.map((item, index) => {
                    const percentage = (item.value / maxValue) * 100;
                    const color = item.color || defaultColors[index % defaultColors.length];

                    return (
                        <div key={item.label} className="bar-item">
                            <div className="bar-label">{item.label}</div>
                            <div className="bar-track">
                                <div
                                    className="bar-fill"
                                    style={{
                                        width: `${percentage}%`,
                                        backgroundColor: color
                                    }}
                                >
                                    {showValues && (
                                        <span className="bar-value">
                                            {typeof item.value === 'number' && item.value < 1
                                                ? (item.value * 100).toFixed(1) + '%'
                                                : item.value.toFixed(2)
                                            }
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}

interface DonutChartProps {
    data: DataPoint[];
    title?: string;
    size?: number;
}

export function DonutChart({ data, title, size = 160 }: DonutChartProps) {
    const total = useMemo(() => data.reduce((sum, d) => sum + d.value, 0), [data]);

    const defaultColors = [
        '#3b82f6',
        '#22c55e',
        '#f59e0b',
        '#ef4444',
        '#8b5cf6',
        '#ec4899'
    ];

    // Calculate segments
    let cumulativePercent = 0;
    const segments = data.map((item, index) => {
        const percent = total > 0 ? (item.value / total) * 100 : 0;
        const startPercent = cumulativePercent;
        cumulativePercent += percent;

        return {
            ...item,
            percent,
            startPercent,
            color: item.color || defaultColors[index % defaultColors.length]
        };
    });

    // Create conic-gradient
    const gradientStops = segments.map(seg =>
        `${seg.color} ${seg.startPercent}% ${seg.startPercent + seg.percent}%`
    ).join(', ');

    return (
        <div className="chart donut-chart">
            {title && <h3 className="chart-title">{title}</h3>}
            <div className="donut-container">
                <div
                    className="donut-ring"
                    style={{
                        width: size,
                        height: size,
                        background: `conic-gradient(${gradientStops})`
                    }}
                >
                    <div className="donut-center">
                        <span className="donut-total">{total.toFixed(0)}</span>
                        <span className="donut-label">Total</span>
                    </div>
                </div>
                <div className="donut-legend">
                    {segments.map(seg => (
                        <div key={seg.label} className="legend-item">
                            <span
                                className="legend-color"
                                style={{ backgroundColor: seg.color }}
                            />
                            <span className="legend-label">{seg.label}</span>
                            <span className="legend-value">{seg.percent.toFixed(1)}%</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

interface MetricCardProps {
    label: string;
    value: string | number;
    change?: number;
    icon?: React.ReactNode;
    color?: string;
}

export function MetricCard({ label, value, change, icon, color }: MetricCardProps) {
    const formattedValue = typeof value === 'number'
        ? (value < 1 ? (value * 100).toFixed(1) + '%' : value.toFixed(2))
        : value;

    return (
        <div className="metric-card" style={{ borderTopColor: color }}>
            {icon && <div className="metric-icon" style={{ color }}>{icon}</div>}
            <div className="metric-content">
                <div className="metric-value">{formattedValue}</div>
                <div className="metric-label">{label}</div>
                {change !== undefined && (
                    <div className={`metric-change ${change >= 0 ? 'positive' : 'negative'}`}>
                        {change >= 0 ? '↑' : '↓'} {Math.abs(change).toFixed(1)}%
                    </div>
                )}
            </div>
        </div>
    );
}

interface LineSparkProps {
    data: number[];
    color?: string;
    height?: number;
    width?: number;
}

export function LineSpark({ data, color = 'var(--accent-primary)', height = 40, width = 120 }: LineSparkProps) {
    if (data.length < 2) return null;

    const min = Math.min(...data);
    const max = Math.max(...data);
    const range = max - min || 1;

    const points = data.map((value, index) => {
        const x = (index / (data.length - 1)) * width;
        const y = height - ((value - min) / range) * height;
        return `${x},${y}`;
    }).join(' ');

    return (
        <svg className="line-spark" width={width} height={height}>
            <polyline
                fill="none"
                stroke={color}
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                points={points}
            />
        </svg>
    );
}

interface ProgressRingProps {
    value: number;
    max?: number;
    size?: number;
    strokeWidth?: number;
    color?: string;
    label?: string;
}

export function ProgressRing({
    value,
    max = 100,
    size = 80,
    strokeWidth = 8,
    color = 'var(--accent-primary)',
    label
}: ProgressRingProps) {
    const radius = (size - strokeWidth) / 2;
    const circumference = radius * 2 * Math.PI;
    const percent = Math.min(value / max, 1);
    const offset = circumference - (percent * circumference);

    return (
        <div className="progress-ring-container">
            <svg className="progress-ring" width={size} height={size}>
                <circle
                    className="progress-ring-bg"
                    stroke="var(--border-color)"
                    fill="none"
                    strokeWidth={strokeWidth}
                    r={radius}
                    cx={size / 2}
                    cy={size / 2}
                />
                <circle
                    className="progress-ring-fill"
                    stroke={color}
                    fill="none"
                    strokeWidth={strokeWidth}
                    strokeLinecap="round"
                    strokeDasharray={`${circumference} ${circumference}`}
                    strokeDashoffset={offset}
                    r={radius}
                    cx={size / 2}
                    cy={size / 2}
                    style={{ transform: 'rotate(-90deg)', transformOrigin: '50% 50%' }}
                />
            </svg>
            <div className="progress-ring-value">
                {(percent * 100).toFixed(0)}%
            </div>
            {label && <div className="progress-ring-label">{label}</div>}
        </div>
    );
}
