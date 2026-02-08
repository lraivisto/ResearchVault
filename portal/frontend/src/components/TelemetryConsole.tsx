
import React, { useEffect, useRef } from 'react';
import { clsx } from 'clsx';
import { LogEvent } from '../hooks/useEventStream';

interface TelemetryConsoleProps {
    logs: LogEvent[];
    className?: string; // Additional classes
}

const TelemetryConsole: React.FC<TelemetryConsoleProps> = ({ logs, className }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom if user is near bottom
    // But wait, our logs are ordered newest-first (descending)?
    // Usually logs are appended to bottom.
    // In `useEventStream`, we did `[newLog, ...prev]`, so newest is at top.
    // A terminal usually scrolls up as new lines appear at bottom.
    // Let's reverse the display for a traditional terminal feel or keep it news-feed style.
    // News-feed (newest top) is better for monitoring without scrolling.

    return (
        <div
            className={clsx(
                "bg-void-panel/80 backdrop-blur-md border border-white/10 rounded-lg p-4 h-64 overflow-y-auto font-mono text-xs",
                className
            )}
            ref={containerRef}
        >
            <div className="flex flex-col gap-1">
                {logs.map((log) => (
                    <div key={log.id} className="flex gap-2 items-start hover:bg-white/5 p-1 rounded transition-colors">
                        <span className="text-gray-500 shrink-0 w-20 text-right">
                            {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <span
                            className={clsx(
                                "font-bold shrink-0 w-24",
                                log.type === 'SCUTTLE' && "text-amber-500",
                                log.type === 'INGEST' && "text-cyan-400",
                                log.type === 'SYNTHESIS' && "text-bio-400",
                                log.type === 'ERROR' && "text-red-500",
                                !['SCUTTLE', 'INGEST', 'SYNTHESIS', 'ERROR'].includes(log.type) && "text-gray-400"
                            )}
                        >
                            [{log.type}]
                        </span>
                        <span className="text-gray-300 break-all">
                            {JSON.stringify(log.payload)}
                        </span>
                    </div>
                ))}
                {logs.length === 0 && (
                    <div className="text-gray-600 italic text-center mt-10">
                        Waiting for telemetry...
                    </div>
                )}
            </div>
        </div>
    );
};

export default TelemetryConsole;
