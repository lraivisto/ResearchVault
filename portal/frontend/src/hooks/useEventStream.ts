
import { useEffect, useState, useRef } from 'react';

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

export function useEventStream(): UseEventStreamReturn {
    const [logs, setLogs] = useState<LogEvent[]>([]);
    const [status, setStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');
    const [lastGraphUpdate, setLastGraphUpdate] = useState<string | null>(null);
    const eventSourceRef = useRef<EventSource | null>(null);

    // Keep logs limited to last 100 to prevent memory issues
    const MAX_LOGS = 100;

    useEffect(() => {
        // Only connect if not already connected
        if (eventSourceRef.current) return;

        setStatus('connecting');

        const token = (import.meta.env.VITE_RESEARCHVAULT_PORTAL_TOKEN as string | undefined) || undefined;
        const url = new URL('http://localhost:8000/api/stream');
        url.searchParams.set('last_event_id', '0');
        if (token) url.searchParams.set('token', token);

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
                setLogs(prev => {
                    const updated = [newLog, ...prev];
                    return updated.slice(0, MAX_LOGS);
                });
            } catch (e) {
                console.error('Failed to parse log event', e);
            }
        });

        // Listen for 'graph_update' signals
        es.addEventListener('graph_update', (event) => {
            const data = JSON.parse(event.data);
            console.log('Graph update signal received:', data.reason);
            setLastGraphUpdate(Date.now().toString());
        });

        // Listen for 'pulse'
        es.addEventListener('pulse', () => {
            // Just a heartbeat, maybe update connection status time
        });

        return () => {
            es.close();
            eventSourceRef.current = null;
        };
    }, []);

    return { logs, status, lastGraphUpdate };
}
