import React, { useMemo } from 'react';
import {
    Chart as ChartJS,
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    PointElement,
    LineElement,
} from 'chart.js';
import { Doughnut, Bar, Line } from 'react-chartjs-2';
import './Charts.css';

// Register Chart.js components
ChartJS.register(
    ArcElement,
    Tooltip,
    Legend,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    PointElement,
    LineElement
);

interface DataPoint {
    label: string;
    value: number | null | undefined;
    color?: string;
}

interface BarChartProps {
    data: DataPoint[];
    title?: string;
    height?: number;
    showValues?: boolean;
}

export function BarChart({ data, title, height = 200, showValues = true }: BarChartProps) {
    const chartData = {
        labels: data.map(d => d.label),
        datasets: [{
            data: data.map(d => d.value ?? 0),
            backgroundColor: data.map((d, i) => d.color || [
                'rgba(99, 102, 241, 0.8)',
                'rgba(16, 185, 129, 0.8)',
                'rgba(139, 92, 246, 0.8)',
                'rgba(245, 158, 11, 0.8)',
                'rgba(236, 72, 153, 0.8)'
            ][i % 5]),
            borderRadius: 6,
            borderWidth: 0,
        }]
    };

    const options = {
        indexAxis: 'y' as const,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: { display: false },
            title: { display: !!title, text: title, color: '#fff' },
            tooltip: {
                backgroundColor: 'rgba(15, 15, 25, 0.9)',
                titleColor: '#fff',
                bodyColor: '#fff',
                borderColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 1,
            }
        },
        scales: {
            x: {
                grid: { display: false, drawBorder: false },
                ticks: { color: 'rgba(255, 255, 255, 0.5)', font: { size: 10 } }
            },
            y: {
                grid: { display: false, drawBorder: false },
                ticks: { color: 'rgba(255, 255, 255, 0.8)', font: { size: 11 } }
            }
        }
    };

    return (
        <div className="chart bar-chart" style={{ height: height + 60 }}>
            <Bar data={chartData} options={options} />
        </div>
    );
}

interface DonutChartProps {
    data: DataPoint[];
    title?: string;
    size?: number;
}

export function DonutChart({ data, title, size = 160 }: DonutChartProps) {
    const total = useMemo(() => data.reduce((sum, d) => sum + (d.value || 0), 0), [data]);

    const chartData = {
        labels: data.map(d => d.label),
        datasets: [{
            data: data.map(d => d.value ?? 0),
            backgroundColor: data.map((d, i) => d.color || [
                '#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'
            ][i % 6]),
            borderWidth: 0,
            hoverOffset: 10
        }]
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
            legend: {
                position: 'right' as const,
                labels: { color: 'rgba(255, 255, 255, 0.7)', font: { size: 11 }, padding: 15 }
            },
            tooltip: {
                backgroundColor: 'rgba(15, 15, 25, 0.9)',
                padding: 12,
            }
        }
    };

    return (
        <div className="chart donut-chart" style={{ height: size + 80 }}>
            {title && <h3 className="chart-title">{title}</h3>}
            <div className="donut-wrapper" style={{ position: 'relative', height: size }}>
                <Doughnut data={chartData} options={options} />
                <div className="donut-center-overlay">
                    <span className="donut-total">{total.toFixed(0)}</span>
                    <span className="donut-label">Total</span>
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
        : (value ?? 'N/A');

    return (
        <div className="metric-card" style={{ borderTop: `2px solid ${color}` }}>
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
    const chartData = {
        labels: data.map((_, i) => i),
        datasets: [{
            data: data,
            borderColor: color,
            borderWidth: 2,
            pointRadius: 0,
            tension: 0.4,
            fill: false
        }]
    };

    const options = {
        responsive: false,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: false } },
        scales: {
            x: { display: false },
            y: { display: false }
        }
    };

    return <Line data={chartData} options={options} width={width} height={height} />;
}

interface ProgressRingProps {
    value: number | null | undefined;
    max?: number;
    size?: number;
    strokeWidth?: number;
    color?: string;
    label?: string;
}

export function ProgressRing({
    value,
    max = 100,
    size = 100,
    color = 'var(--accent-primary)',
    label
}: ProgressRingProps) {
    const safeValue = value ?? 0;
    const chartData = {
        datasets: [{
            data: [safeValue, max - safeValue],
            backgroundColor: [color, 'rgba(255, 255, 255, 0.05)'],
            borderWidth: 0,
            circumference: 360,
            rotation: 0,
        }]
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '80%',
        plugins: {
            legend: { display: false },
            tooltip: { enabled: false }
        }
    };

    return (
        <div className="progress-ring-chart-container" style={{ width: size }}>
            <div className="progress-ring-wrapper" style={{ height: size, width: size, position: 'relative' }}>
                <Doughnut data={chartData} options={options} />
                <div className="progress-ring-value-overlay">
                    {((safeValue / max) * 100).toFixed(0)}%
                </div>
            </div>
            {label && <div className="progress-ring-label">{label}</div>}
        </div>
    );
}
