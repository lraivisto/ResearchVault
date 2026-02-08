
import { useRef } from 'react';
import { clsx } from 'clsx';
import { LogEvent } from '../hooks/useEventStream';

interface TelemetryConsoleProps {
    logs: LogEvent[];
    className?: string; // Additional classes
}

const TelemetryConsole: React.FC<TelemetryConsoleProps> = ({ logs, className }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    return (
        <div
            className={clsx(
                "bg-black/40 backdrop-blur-md border border-cyan/20 rounded-lg h-64 overflow-y-auto font-mono text-[10px] scrollbar-thin scrollbar-thumb-cyan/20 shadow-[0_0_15px_rgba(0,240,255,0.05)]",
                className
            )}
            ref={containerRef}
        >
            <div className="flex flex-col">
                {logs.map((log) => (
                    <div key={log.id} className="group border-b border-white/5 hover:bg-cyan/5 p-2 transition-colors">
                        <div className="flex justify-between items-center mb-1">
                            <span
                                className={clsx(
                                    "font-bold uppercase tracking-tighter",
                                    log.type === 'SCUTTLE' && "text-amber-500",
                                    log.type === 'INGEST' && "text-cyan-400",
                                    log.type === 'SYNTHESIS' && "text-bio-400",
                                    log.type === 'ERROR' && "text-red-500",
                                    !['SCUTTLE', 'INGEST', 'SYNTHESIS', 'ERROR'].includes(log.type) && "text-gray-400"
                                )}
                            >
                                {log.type}
                            </span>
                            <span className="text-[9px] text-gray-600 group-hover:text-cyan/40">
                                {new Date(log.timestamp).toLocaleTimeString()}
                            </span>
                        </div>
                        <div className="text-gray-400 leading-tight line-clamp-2 group-hover:line-clamp-none transition-all">
                            {typeof log.payload === 'string' ? log.payload : JSON.stringify(log.payload)}
                        </div>
                    </div>
                ))}
                {logs.length === 0 && (
                    <div className="text-gray-600 italic text-center py-20 animate-pulse">
                        WAITING FOR NEURAL UPLINK...
                    </div>
                )}
            </div>
        </div>
    );
};

export default TelemetryConsole;
