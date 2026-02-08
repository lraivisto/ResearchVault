
import { useRef, useEffect, useState, useCallback } from 'react';
import ForceGraph2D, { ForceGraphMethods } from 'react-force-graph-2d';
import { useQuery } from '@tanstack/react-query';

interface GraphNode {
    id: string;
    label: string;
    val: number;
    tags: string[];
    group: string;
    cluster?: string;
    x?: number;
    y?: number;
}

interface GraphLink {
    source: string;
    target: string;
    type: string;
    color: string;
}

interface GraphData {
    nodes: GraphNode[];
    links: GraphLink[];
}

interface KnowledgeGraphProps {
    onNodeSelect: (node: GraphNode) => void;
    lastUpdateTimestamp: string | null;
    projectId?: string;
}

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ onNodeSelect, lastUpdateTimestamp, projectId }) => {
    const fgRef = useRef<ForceGraphMethods>();
    const [highlightNodes, setHighlightNodes] = useState(new Set());
    const [highlightLinks, setHighlightLinks] = useState(new Set());
    const [hoverNode, setHoverNode] = useState<GraphNode | null>(null);

    // Fetch graph data
    const { data: graphData, refetch } = useQuery<GraphData>({
        queryKey: ['graphData', projectId],
        queryFn: async () => {
            const token = (import.meta.env.VITE_RESEARCHVAULT_PORTAL_TOKEN as string | undefined) || undefined;
            const url = new URL('http://localhost:8000/api/graph');
            if (token) url.searchParams.set('token', token);
            if (projectId) url.searchParams.set('project_id', projectId);

            const res = await fetch(url.toString());
            return res.json();
        },
        // We rely on manual invalidation via SSE signal (lastUpdateTimestamp)
        staleTime: Infinity,
    });

    // Re-fetch when timestamp updates
    useEffect(() => {
        if (lastUpdateTimestamp) {
            refetch();
        }
    }, [lastUpdateTimestamp, refetch]);

    // Adjust graph view on first load
    useEffect(() => {
        if (fgRef.current && graphData?.nodes.length) {
            fgRef.current.d3Force('charge')?.strength(-100);
            fgRef.current.zoomToFit(400);
        }
    }, [graphData]);

    const handleNodeClick = useCallback((node: GraphNode) => {
        console.log('Clicked node:', node);
        onNodeSelect(node);

        // Center view on node
        fgRef.current?.centerAt(node.x, node.y, 1000);
        fgRef.current?.zoom(4, 1000); // Zoom in
    }, [onNodeSelect]);

    return (
        <div className="w-full h-full bg-void overflow-hidden relative">
            {!graphData && (
                <div className="absolute inset-0 flex items-center justify-center text-cyan-400 font-mono animate-pulse">
                    INITIALIZING NEURAL LINK...
                </div>
            )}

            {graphData && graphData.nodes.length === 0 && (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-gray-500 font-mono pointer-events-none">
                    <div className="text-xl mb-2 text-cyan/50">NO FINDINGS DETECTED</div>
                    <div className="text-xs">Run 'python3 main.py scuttle' to populate the vault.</div>
                </div>
            )}

            {graphData && (
                <ForceGraph2D
                    ref={fgRef}
                    graphData={graphData}
                    nodeLabel="label"
                    nodeColor={node =>
                        hoverNode === node || highlightNodes.has(node.id)
                            ? '#ffae00'
                            : (node.group === 'finding' ? '#00f0ff' : '#bd00ff')
                    }
                    linkColor={link => highlightLinks.has(link) ? '#ffae00' : link.color}
                    nodeRelSize={4}
                    linkWidth={link => highlightLinks.has(link) ? 3 : 1}
                    linkDirectionalParticles={1}
                    linkDirectionalParticleWidth={2}
                    onNodeClick={handleNodeClick}
                    onNodeHover={node => setHoverNode(node || null)}
                    backgroundColor="#050505"
                    // Optimize for performance
                    cooldownTicks={100}
                    onEngineStop={() => fgRef.current?.zoomToFit(400)}
                />
            )}
        </div>
    );
};

export default KnowledgeGraph;
