
import { useRef, useEffect, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import type { ForceGraphMethods, LinkObject, NodeObject } from 'react-force-graph-2d';
import { useQuery } from '@tanstack/react-query';
import { API_BASE } from '../config';

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
    searchQuery?: string;
    token: string | null;
}

const KnowledgeGraph: React.FC<KnowledgeGraphProps> = ({ onNodeSelect, lastUpdateTimestamp, projectId, searchQuery, token }) => {
    const fgRef = useRef<
        ForceGraphMethods<NodeObject<GraphNode>, LinkObject<GraphNode, GraphLink>>
    >();
    const isInitialized = useRef(false);
    const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
    const [hoverNode, setHoverNode] = useState<GraphNode | null>(null);

    // Color palette for different entity types/groups
    const COLORS = {
        finding: '#00f0ff',
        artifact: '#bd00ff',
        insight: '#ffae00',
        cluster: ['#00ff95', '#00bcff', '#7000ff', '#ff0055', '#ff9500']
    };

    const getNodeColor = (node: GraphNode) => {
        if (hoverNode === node) return '#ffffff';
        if (searchQuery && highlightNodes.has(node.id)) return '#ffae00'; // Amber for search matches
        
        let baseColor = node.group === 'finding' ? COLORS.finding : COLORS.artifact;
        
        // Dim if search is active and this node doesn't match
        if (searchQuery && !highlightNodes.has(node.id)) {
            return `${baseColor}20`; // 20% opacity
        }

        // Simple cluster-based coloring if available
        if (node.cluster) {
            const clusterIdx = parseInt(node.cluster) % COLORS.cluster.length;
            return COLORS.cluster[clusterIdx];
        }

        return baseColor;
    };

    // Fetch graph data
    const { data: graphData, refetch } = useQuery<GraphData>({
        queryKey: ['graphData', projectId, token],
        queryFn: async () => {
            if (!token) throw new Error('AUTH_REQUIRED');
            const url = new URL(`${API_BASE}/graph`);
            url.searchParams.set('token', token);
            if (projectId) url.searchParams.set('project_id', projectId);

            const res = await fetch(url.toString());
            return res.json();
        },
        enabled: !!token,
        // We rely on manual invalidation via SSE signal (lastUpdateTimestamp)
        staleTime: Infinity,
    });

    // Filter nodes based on search query
    useEffect(() => {
        if (!searchQuery) {
            setHighlightNodes(new Set());
            return;
        }

        const q = searchQuery.toLowerCase();
        const matches =
            graphData?.nodes
                .filter(
                    (n) =>
                        n.label.toLowerCase().includes(q) ||
                        n.tags?.some((t) => t.toLowerCase().includes(q)),
                )
                .map((n) => n.id) || [];

        setHighlightNodes(new Set(matches));
    }, [searchQuery, graphData]);

    // Re-fetch when timestamp updates
    useEffect(() => {
        if (lastUpdateTimestamp) {
            refetch();
        }
    }, [lastUpdateTimestamp, refetch]);

    // Adjust graph view on first load
    useEffect(() => {
        if (fgRef.current && graphData?.nodes.length && !isInitialized.current) {
            fgRef.current.d3Force('charge')?.strength(-100);
            fgRef.current.zoomToFit(400);
            isInitialized.current = true;
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
                    nodeColor={getNodeColor}
                    linkColor="color"
                    nodeRelSize={8}
                    linkWidth={1.5}
                    linkDirectionalParticles={2}
                    linkDirectionalParticleWidth={3}
                    linkDirectionalParticleSpeed={0.005}
                    onNodeClick={handleNodeClick}
                    onNodeHover={node => setHoverNode(node || null)}
                    backgroundColor="#050505"
                    // Optimize for performance
                    cooldownTicks={100}
                    onEngineStop={() => {
                        if (!isInitialized.current) {
                            fgRef.current?.zoomToFit(600, 100);
                        }
                    }}
                />
            )}
        </div>
    );
};

export default KnowledgeGraph;
