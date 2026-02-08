
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
        <div className="fixed right-0 top-0 h-full w-96 bg-void-panel/90 backdrop-blur-xl border-l border-white/10 p-6 shadow-2xl z-50 transform transition-transform duration-300 translate-x-0">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-mono text-cyan font-bold truncate pr-4">
                    {node.label || "UNKNOWN ENTITY"}
                </h2>
                <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                    <X size={20} />
                </button>
            </div>

            <div className="space-y-6">
                {/* Connection Strength / Confidence */}
                <div className="bg-void-surface p-4 rounded border border-white/5">
                    <div className="flex justify-between text-xs text-gray-400 mb-2 uppercase tracking-wider">
                        Confidence Matrix
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="h-2 flex-grow bg-gray-800 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-cyan"
                                style={{ width: `${(node.val / 10) * 100}%` }}
                            />
                        </div>
                        <span className="font-mono text-cyan-400">{(node.val / 10).toFixed(2)}</span>
                    </div>
                </div>

                {/* Metadata */}
                <div className="space-y-2 font-mono text-xs">
                    <div className="flex justify-between border-b border-white/5 pb-1">
                        <span className="text-gray-500">ID</span>
                        <span className="text-gray-300">{node.id}</span>
                    </div>
                    <div className="flex justify-between border-b border-white/5 pb-1">
                        <span className="text-gray-500">TYPE</span>
                        <span className="text-bio-400">{node.group?.toUpperCase()}</span>
                    </div>
                    <div className="py-2 border-b border-white/5">
                        <span className="text-gray-500 block mb-1 uppercase tracking-tighter">Content</span>
                        <div className="text-gray-300 bg-black/20 p-2 rounded max-h-48 overflow-y-auto whitespace-pre-wrap leading-relaxed">
                            {node.content || "No content summary available."}
                        </div>
                    </div>
                    <div className="flex flex-wrap gap-2 pt-2">
                        {node.tags && node.tags.map((tag: string) => (
                            <span key={tag} className="px-2 py-0.5 bg-white/5 rounded text-gray-400 text-[10px] uppercase">
                                #{tag}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Actions / Steering */}
                <div className="pt-6 border-t border-white/10">
                    <h3 className="text-sm font-bold text-gray-300 mb-4 flex items-center gap-2">
                        <Crosshair size={16} className="text-amber" />
                        AGENT COMMANDS
                    </h3>

                    <div className="grid grid-cols-2 gap-3">
                        <button
                            onClick={() => handleDispatch('SEARCH')}
                            disabled={missionStatus !== 'idle'}
                            className="flex flex-col items-center justify-center p-4 bg-void-surface hover:bg-cyan/10 border border-cyan/20 hover:border-cyan transition-all rounded group"
                        >
                            <Search size={24} className="mb-2 text-cyan group-hover:text-white transition-colors" />
                            <span className="text-xs font-bold text-cyan group-hover:text-white">DEEP DIVE</span>
                        </button>

                        <button
                            onClick={() => handleDispatch('REFUTE')}
                            disabled={missionStatus !== 'idle'}
                            className="flex flex-col items-center justify-center p-4 bg-void-surface hover:bg-amber/10 border border-amber/20 hover:border-amber transition-all rounded group"
                        >
                            <Zap size={24} className="mb-2 text-amber group-hover:text-white transition-colors" />
                            <span className="text-xs font-bold text-amber group-hover:text-white">VERIFY</span>
                        </button>
                    </div>

                    {missionStatus !== 'idle' && (
                        <div className="mt-4 p-2 bg-cyan/10 border border-cyan/30 text-cyan text-xs font-mono text-center animate-pulse">
                            {missionStatus === 'dispatching' ? 'TRANSMITTING COMMAND...' : 'MISSION ACKNOWLEDGED'}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default InspectorPanel;
