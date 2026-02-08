
import React, { useState } from 'react';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';
import { useEventStream } from './hooks/useEventStream';
import KnowledgeGraph from './components/KnowledgeGraph';
import TelemetryConsole from './components/TelemetryConsole';
import InspectorPanel from './components/InspectorPanel';
import { Activity, Radio, FolderTree } from 'lucide-react';

const queryClient = new QueryClient();

function AppContent() {
    const [projectId, setProjectId] = useState<string>('');
    const { logs, status, lastGraphUpdate } = useEventStream(projectId);
    const [selectedNode, setSelectedNode] = useState<any>(null);

    // Fetch projects for selector
    const { data: projectsData } = useQuery({
        queryKey: ['projects'],
        queryFn: async () => {
            const token = (import.meta.env.VITE_RESEARCHVAULT_PORTAL_TOKEN as string | undefined) || undefined;
            const url = new URL('http://localhost:8000/api/projects');
            if (token) url.searchParams.set('token', token);
            const res = await fetch(url.toString());
            return res.json();
        }
    });

    // Fetch stats
    const { data: graphData } = useQuery({
        queryKey: ['graphData', projectId],
        queryFn: async () => {
            const token = (import.meta.env.VITE_RESEARCHVAULT_PORTAL_TOKEN as string | undefined) || undefined;
            const url = new URL('http://localhost:8000/api/graph');
            if (token) url.searchParams.set('token', token);
            if (projectId) url.searchParams.set('project_id', projectId);
            const res = await fetch(url.toString());
            return res.json();
        }
    });

    const handleNodeSelect = (node: any) => {
        setSelectedNode(node);
    };

    const handleDispatchMission = async (type: string, findingId: string) => {
        try {
            const token = (import.meta.env.VITE_RESEARCHVAULT_PORTAL_TOKEN as string | undefined) || undefined;
            const url = new URL('http://localhost:8000/api/missions');
            if (token) url.searchParams.set('token', token);

            await fetch(url.toString(), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: selectedNode?.project_id || projectId || 'unknown',
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
        <div className="relative w-screen h-screen bg-[#050505] text-gray-200 overflow-hidden font-sans">
            {/* Background Graph Layer */}
            <div className="absolute inset-0 z-0">
                <KnowledgeGraph
                    onNodeSelect={handleNodeSelect}
                    lastUpdateTimestamp={lastGraphUpdate}
                    projectId={projectId}
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

                {/* Stats HUD (Top Center-ish) */}
                <div className="flex gap-8 pointer-events-auto bg-black/40 backdrop-blur-md border border-cyan/10 p-2 px-6 rounded-lg font-mono">
                    <div className="flex flex-col">
                        <span className="text-[9px] text-gray-500 uppercase">Vault State</span>
                        <span className="text-cyan font-bold">{projectsData?.projects?.length || 0} PROJ / {graphData?.nodes?.length || 0} NODES</span>
                    </div>
                    <div className="flex flex-col border-l border-white/10 pl-8">
                        <span className="text-[9px] text-gray-500 uppercase">Uptime</span>
                        <span className="text-gray-300">6D 02H</span>
                    </div>
                </div>

                {/* Project Selector */}
                <div className="flex items-center gap-4 pointer-events-auto bg-black/40 backdrop-blur-md border border-cyan/20 p-2 rounded-lg">
                    <div className="flex items-center gap-2 text-cyan/70 font-mono text-xs uppercase tracking-widest px-2">
                        <FolderTree size={16} />
                        Project
                    </div>
                    <select 
                        className="bg-void border border-cyan/30 text-cyan font-mono text-xs p-1 px-3 rounded outline-none focus:border-cyan hover:bg-cyan/10 transition-colors"
                        value={projectId}
                        onChange={(e) => setProjectId(e.target.value)}
                    >
                        <option value="">ALL PROJECTS</option>
                        {projectsData?.projects?.map((p: string) => (
                            <option key={p} value={p}>{p.toUpperCase()}</option>
                        ))}
                    </select>
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
