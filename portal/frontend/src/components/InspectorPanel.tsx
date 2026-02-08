
import React, { useState } from 'react';
import { clsx } from 'clsx';
import { X, Search, Zap, Crosshair } from 'lucide-react';

interface InspectorPanelProps {
    node: any; // Using any for flexibility with graph data
    onClose: () => void;
    onDispatchMission: (type: string, findingId: string) => void;
}

const InspectorPanel: React.FC<InspectorPanelProps> = ({ node, onClose, onDispatchMission }) => {
    const [missionStatus, setMissionStatus] = useState<'idle' | 'dispatching' | 'acknowledged'>('idle');

    const handleDispatch = (type: string) => {
        setMissionStatus('dispatching');
        onDispatchMission(type, node.id);
        setTimeout(() => setMissionStatus('acknowledged'), 1000);
        setTimeout(() => setMissionStatus('idle'), 3000);
    };

    if (!node) return null;

    return (
        <div className="fixed right-4 top-4 bottom-4 w-96 bg-black/60 backdrop-blur-xl border border-white/10 p-6 shadow-[0_0_50px_rgba(0,0,0,0.5)] z-50 rounded-xl overflow-y-auto scrollbar-hide">
            <div className="flex justify-between items-center mb-6 border-b border-white/5 pb-4">
                <div className="flex flex-col">
                    <span className="text-[10px] text-cyan/50 font-mono uppercase tracking-[0.2em]">Finding Inspector</span>
                    <h2 className="text-xl font-mono text-cyan font-bold truncate pr-4 text-glow">
                        {node.label || "UNKNOWN ENTITY"}
                    </h2>
                </div>
                <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-full transition-colors text-gray-500 hover:text-white">
                    <X size={20} />
                </button>
            </div>

            <div className="space-y-6">
                {/* Connection Strength / Confidence */}
                <div className="bg-white/5 p-4 rounded-lg border border-white/5 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-cyan" />
                    <div className="flex justify-between text-[10px] text-gray-500 mb-2 uppercase tracking-widest font-bold">
                        <span>Confidence Score</span>
                        <span className="text-cyan">{(node.val / 10 * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-black/40 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-cyan shadow-[0_0_10px_#00f0ff]"
                            style={{ width: `${(node.val / 10) * 100}%` }}
                        />
                    </div>
                </div>

                {/* Metadata Grid */}
                <div className="grid grid-cols-2 gap-2 font-mono text-[10px]">
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <span className="text-gray-500 block uppercase mb-1">Entity ID</span>
                        <span className="text-gray-300 truncate block">{node.id}</span>
                    </div>
                    <div className="bg-white/5 p-2 rounded border border-white/5">
                        <span className="text-gray-500 block uppercase mb-1">Class</span>
                        <span className="text-bio-400 font-bold">{node.group?.toUpperCase()}</span>
                    </div>
                </div>

                {/* Content Area */}
                <div className="space-y-2">
                    <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Summary Content</span>
                    <div className="text-sm text-gray-300 bg-black/40 p-4 rounded-lg border border-white/5 max-h-64 overflow-y-auto whitespace-pre-wrap leading-relaxed font-sans scrollbar-thin">
                        {node.content || "No detailed summary data retrieved from neural vault."}
                    </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-2">
                    {node.tags && node.tags.filter((t: string) => t).map((tag: string) => (
                        <span key={tag} className="px-2 py-1 bg-cyan/5 border border-cyan/20 rounded text-cyan/70 text-[9px] font-mono uppercase tracking-tighter hover:bg-cyan/10 transition-colors">
                            #{tag}
                        </span>
                    ))}
                </div>

                {/* Actions / Steering */}
                <div className="pt-6 border-t border-white/10 space-y-4">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                        <Zap size={14} className="text-amber" />
                        Neural Directives
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <button
                            onClick={() => handleDispatch('SEARCH')}
                            disabled={missionStatus !== 'idle'}
                            className="flex flex-col items-center justify-center p-4 bg-black/40 hover:bg-cyan/10 border border-cyan/20 hover:border-cyan transition-all rounded-lg group active:scale-95"
                        >
                            <Search size={20} className="mb-2 text-cyan group-hover:text-white transition-colors" />
                            <span className="text-[10px] font-bold text-cyan group-hover:text-white uppercase tracking-tighter">Deep Scuttle</span>
                        </button>

                        <button
                            onClick={() => handleDispatch('REFUTE')}
                            disabled={missionStatus !== 'idle'}
                            className="flex flex-col items-center justify-center p-4 bg-black/40 hover:bg-amber/10 border border-amber/20 hover:border-amber transition-all rounded-lg group active:scale-95"
                        >
                            <Zap size={20} className="mb-2 text-amber group-hover:text-white transition-colors" />
                            <span className="text-[10px] font-bold text-amber group-hover:text-white uppercase tracking-tighter">Fact Check</span>
                        </button>
                    </div>

                    {missionStatus !== 'idle' && (
                        <div className="p-3 bg-cyan/5 border border-cyan/30 rounded-lg flex items-center justify-center gap-3">
                            <div className="w-2 h-2 bg-cyan rounded-full animate-ping" />
                            <span className="text-[10px] font-mono text-cyan uppercase tracking-widest">
                                {missionStatus === 'dispatching' ? 'Transmitting...' : 'Link Synchronized'}
                            </span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default InspectorPanel;
