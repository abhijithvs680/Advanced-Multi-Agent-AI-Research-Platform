import { useState, useEffect, useCallback, useRef } from 'react';

export interface WSEvent {
    type: 'job_status' | 'agent_progress' | 'metrics_update' | 'system_status' | 'log_message';
    data: Record<string, any>;
    timestamp: string;
    job_id?: string;
}

export interface UseWebSocketOptions {
    url?: string;
    jobId?: string;
    onMessage?: (event: WSEvent) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    reconnectInterval?: number;
    autoReconnect?: boolean;
}

export interface UseWebSocketReturn {
    connected: boolean;
    lastEvent: WSEvent | null;
    events: WSEvent[];
    send: (action: string, data?: Record<string, any>) => void;
    subscribe: (jobId: string) => void;
    unsubscribe: (jobId: string) => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
    const {
        url = `ws://${window.location.hostname}:8000/ws`,
        jobId,
        onMessage,
        onConnect,
        onDisconnect,
        reconnectInterval = 3000,
        autoReconnect = true
    } = options;

    const [connected, setConnected] = useState(false);
    const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
    const [events, setEvents] = useState<WSEvent[]>([]);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        if (wsRef.current?.readyState === WebSocket.OPEN) return;

        const wsUrl = jobId ? `${url}/job/${jobId}` : url;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            setConnected(true);
            onConnect?.();
            console.log('WebSocket connected');
        };

        ws.onclose = () => {
            setConnected(false);
            onDisconnect?.();
            console.log('WebSocket disconnected');

            if (autoReconnect) {
                reconnectTimeoutRef.current = setTimeout(() => {
                    connect();
                }, reconnectInterval);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.onmessage = (message) => {
            try {
                const event: WSEvent = JSON.parse(message.data);
                setLastEvent(event);
                setEvents(prev => [...prev.slice(-99), event]); // Keep last 100 events
                onMessage?.(event);
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        };

        wsRef.current = ws;
    }, [url, jobId, onConnect, onDisconnect, onMessage, reconnectInterval, autoReconnect]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        wsRef.current?.close();
    }, []);

    const send = useCallback((action: string, data: Record<string, any> = {}) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ action, ...data }));
        }
    }, []);

    const subscribe = useCallback((subscribeJobId: string) => {
        send('subscribe', { job_id: subscribeJobId });
    }, [send]);

    const unsubscribe = useCallback((unsubscribeJobId: string) => {
        send('unsubscribe', { job_id: unsubscribeJobId });
    }, [send]);

    // Connect on mount
    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    // Ping to keep connection alive
    useEffect(() => {
        const pingInterval = setInterval(() => {
            if (connected) {
                send('ping');
            }
        }, 30000);

        return () => clearInterval(pingInterval);
    }, [connected, send]);

    return {
        connected,
        lastEvent,
        events,
        send,
        subscribe,
        unsubscribe
    };
}

// Hook for job-specific updates
export function useJobUpdates(jobId: string | undefined) {
    const [status, setStatus] = useState<string | null>(null);
    const [currentState, setCurrentState] = useState<string | null>(null);
    const [progress, setProgress] = useState<number>(0);
    const [message, setMessage] = useState<string | null>(null);
    const [agentSteps, setAgentSteps] = useState<Record<string, any>[]>([]);
    const [logs, setLogs] = useState<{ level: string; message: string; timestamp: string }[]>([]);

    const handleMessage = useCallback((event: WSEvent) => {
        if (event.job_id !== jobId) return;

        switch (event.type) {
            case 'job_status':
                if (event.data.status) {
                    setStatus(event.data.status);
                }
                if (event.data.current_state) {
                    setCurrentState(event.data.current_state);
                }
                if (event.data.progress !== undefined) {
                    setProgress(event.data.progress);
                }
                if (event.data.message) {
                    setMessage(event.data.message);
                }
                break;

            case 'agent_progress':
                setAgentSteps(prev => [...prev, {
                    agent: event.data.agent_name,
                    step: event.data.step,
                    progress: event.data.progress,
                    timestamp: event.timestamp
                }]);
                break;

            case 'log_message':
                setLogs(prev => [...prev.slice(-49), {
                    level: event.data.level,
                    message: event.data.message,
                    timestamp: event.timestamp
                }]);
                break;
        }
    }, [jobId]);

    const ws = useWebSocket({
        jobId,
        onMessage: handleMessage
    });

    return {
        connected: ws.connected,
        status,
        currentState,
        progress,
        message,
        agentSteps,
        logs,
        lastEvent: ws.lastEvent
    };
}

// Hook for system metrics
export function useMetricsStream() {
    const [metrics, setMetrics] = useState<Record<string, any>>({});

    const handleMessage = useCallback((event: WSEvent) => {
        if (event.type === 'metrics_update') {
            setMetrics(event.data);
        }
    }, []);

    const ws = useWebSocket({ onMessage: handleMessage });

    return {
        connected: ws.connected,
        metrics
    };
}
