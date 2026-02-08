
import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEventStream } from './hooks/useEventStream';
import KnowledgeGraph from './components/KnowledgeGraph';
import TelemetryConsole from './components/TelemetryConsole';
import InspectorPanel from './components/InspectorPanel';
import { Activity, Radio } from 'lucide-react';

const queryClient = new QueryClient();

function AppContent() {
    const { logs, status, lastGraphUpdate } = useEventStream();
    const [selectedNode, setSelectedNode] = useState<any>(null);

    const handleNodeSelect = (node: any) => {
        setSelectedNode(node);
    };

    const handleDispatchMission = async (type: string, findingId: string) => {
        try {
            await fetch('http://localhost:8000/api/missions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: selectedNode?.project_id || 'unknown', // Ideally node data has project_id
                    finding_id: findingId,
                    mission_type: type,
                }),
            });
            // Optimistic or rely on stream for update
        } catch (e) {
            console.error('Mission dispatch failed', e);
        }
    };

    return (
        <div className="relative w-screen h-screen bg-void text-gray-200 overflow-hidden font-sans">
            {/* Background Graph Layer */}
            <div className="absolute inset-0 z-0">
                <KnowledgeGraph
                    onNodeSelect={handleNodeSelect}
                    lastUpdateTimestamp={lastGraphUpdate}
                />
            </div>

            {/* Header / HUD */}
            <header className="absolute top-0 left-0 w-full p-4 z-10 pointer-events-none flex justify-between items-start">
                <div className="flex flex-col gap-1 pointer-events-auto">
                    <div className="flex items-center gap-3">
                        <div className="relative">
                            <div className={`w-3 h-3 rounded-full ${status === 'connected' ? 'bg-cyan animate-pulse' : 'bg-red-500'}`} />
                            {status === 'connected' && (
                                <div className="absolute inset-0 w-3 h-3 rounded-full bg-cyan animate-ping opacity-75" />
                            )}
                        </div>
                        <h1 className="text-2xl font-mono font-bold tracking-tighter text-glow">
                            RESEARCH<span className="text-cyan">VAULT</span> PORTAL
                        </h1>
                    </div>
                    <div className="text-[10px] text-gray-500 font-mono pl-6 flex items-center gap-2">
                        <Radio size={12} />
                        <span>SIGNAL: {status.toUpperCase()}</span>
                        <span className="mx-2">|</span>
                        <Activity size={12} />
                        <span>ACTIVE AGENT: ONLINE</span>
                    </div>
                </div>
            </header>

            {/* Telemetry Console (Bottom Left) */}
            <div className="absolute bottom-6 left-6 w-96 z-10 pointer-events-auto">
                <div className="mb-2 text-xs font-mono text-cyan/70 uppercase tracking-widest flex items-center gap-2">
                    <div className="w-2 h-2 bg-cyan/50" />
                    Live Telemetry
                </div>
                <TelemetryConsole logs={logs} />
            </div>

            {/* Inspector Panel (Right Interaction Zone) */}
            {selectedNode && (
                <InspectorPanel
                    node={selectedNode}
                    onClose={() => setSelectedNode(null)}
                    onDispatchMission={handleDispatchMission}
                />
            )}

            {/* Scanline Overlay */}
            <div className="absolute inset-0 z-50 pointer-events-none bg-scanlines opacity-10 mix-blend-overlay animate-scanline" />
        </div>
    );
}

export default function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <AppContent />
        </QueryClientProvider>
    );
}
