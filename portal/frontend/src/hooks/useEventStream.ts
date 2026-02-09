
import { useEffect, useState, useRef } from 'react';
import { API_BASE } from '../config';

export interface LogEvent {
    id: string;
    type: string;
    step: number;
    payload: any;
    confidence: number;
    source: string;
    tags: string;
    timestamp: string;
}

interface UseEventStreamReturn {
    logs: LogEvent[];
    status: 'connected' | 'disconnected' | 'connecting';
    lastGraphUpdate: string | null;
}

export function useEventStream(token: string | null, projectId?: string): UseEventStreamReturn {
    const [logs, setLogs] = useState<LogEvent[]>([]);
    const [status, setStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
    const [lastGraphUpdate, setLastGraphUpdate] = useState<string | null>(null);
    const eventSourceRef = useRef<EventSource | null>(null);
    const logBuffer = useRef<LogEvent[]>([]);

    // Keep logs limited to last 100 to prevent memory issues
    const MAX_LOGS = 100;

    useEffect(() => {
        // Reset logs when project changes
        setLogs([]);

        if (!token) {
            setStatus('disconnected');
            return;
        }

        setStatus('connecting');
        const url = new URL(`${API_BASE}/stream`);
        url.searchParams.set('last_event_id', '0');
        url.searchParams.set('token', token);
        if (projectId) url.searchParams.set('project_id', projectId);

        const es = new EventSource(url.toString());
        eventSourceRef.current = es;

        es.onopen = () => {
            setStatus('connected');
            console.log('SSE connection opened');
        };

        es.onerror = (err) => {
            console.error('SSE error', err);
            setStatus('disconnected');
        };

        // Listen for 'log' events
        es.addEventListener('log', (event) => {
            try {
                const newLog = JSON.parse(event.data) as LogEvent;
                logBuffer.current.unshift(newLog);
            } catch (e) {
                console.error('Failed to parse log event', e);
            }
        });

        // Flush buffer every 200ms
        const flushInterval = setInterval(() => {
            if (logBuffer.current.length > 0) {
                setLogs(prev => {
                    const updated = [...logBuffer.current, ...prev];
                    logBuffer.current = [];
                    return updated.slice(0, MAX_LOGS);
                });
            }
        }, 200);

        // Listen for 'graph_update' signals
        es.addEventListener('graph_update', (event) => {
            const data = JSON.parse(event.data);
            console.log('Graph update signal received:', data.reason);
            setLastGraphUpdate(Date.now().toString());
        });clearInterval(flushInterval);
            

        // Listen for 'pulse'
        es.addEventListener('pulse', () => {
            // Just a heartbeat, maybe update connection status time
        });

        return () => {
            es.close();
            eventSourceRef.current = null;
        };
    }, [projectId, token]);

    return { logs, status, lastGraphUpdate };
}
