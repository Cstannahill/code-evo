import React, { useCallback, useMemo } from "react";
import ReactFlow, {
  type Node,
  type Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
  addEdge,
  type Connection,
} from "reactflow";
import "reactflow/dist/style.css";
import { motion } from "framer-motion";
import {
  type TechnologiesByCategory,
  type Technology,
} from "../../types/analysis";

interface TechnologyRelationshipGraphProps {
  analysis: {
    technologies: TechnologiesByCategory;
    // Add other properties of analysis if needed
  };
}

interface CustomNodeData {
  label: string;
  usage?: number;
}

// Define a more specific type for your nodes if needed, extending the base Node type
type CustomNode = Node<CustomNodeData>;

export const TechnologyRelationshipGraph: React.FC<
  TechnologyRelationshipGraphProps
> = ({ analysis }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<CustomNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  useMemo(() => {
    const newNodes: CustomNode[] = [];
    const newEdges: Edge[] = [];
    const nodeMap = new Map<string, CustomNode>();

    // Create central node
    const centralNode: CustomNode = {
      id: "central",
      position: { x: 400, y: 200 },
      data: { label: "Project Core" },
      type: "input", // or 'default' or a custom type
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      style: {
        background: "#8b5cf6", // purple-500
        color: "white",
        border: "2px solid #6d28d9", // purple-700
        fontSize: "14px",
        fontWeight: "bold",
        width: 120,
        height: 60,
        borderRadius: "8px",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
      },
    };
    newNodes.push(centralNode);
    nodeMap.set("central", centralNode);

    // Add technology nodes
    let categoryIndex = 0;
    Object.entries(analysis.technologies).forEach(
      ([category, techs]: [string, Technology[] | undefined]) => {
        if (Array.isArray(techs) && techs.length > 0) {
          const categoryNodeId = `category-${category}`;
          const categoryNode: CustomNode = {
            id: categoryNodeId,
            position: {
              x: 200 + (categoryIndex % 3) * 300, // Adjust layout
              y: 50 + Math.floor(categoryIndex / 3) * 250, // Adjust layout
            },
            data: {
              label: category.charAt(0).toUpperCase() + category.slice(1),
            },
            type: "default",
            sourcePosition: Position.Bottom,
            targetPosition: Position.Top,
            style: {
              background: "#3b82f6", // blue-500
              color: "white",
              border: "2px solid #2563eb", // blue-700
              fontSize: "12px",
              fontWeight: "bold",
              borderRadius: "8px",
              padding: "10px 15px",
            },
          };
          newNodes.push(categoryNode);
          nodeMap.set(categoryNodeId, categoryNode);

          // Connect to central
          newEdges.push({
            id: `central-${categoryNodeId}`,
            source: "central",
            target: categoryNodeId,
            animated: true,
            style: { stroke: "#6b7280", strokeWidth: 2 }, // gray-500
            markerEnd: { type: MarkerType.ArrowClosed, color: "#6b7280" },
          });

          // Add individual tech nodes (max 3-4 per category for clarity)
          techs.slice(0, 4).forEach((tech: Technology, techIndex: number) => {
            const techNodeId = `${categoryNodeId}-${tech.name.replace(
              /\s+/g,
              "-"
            )}`;
            const techNode: CustomNode = {
              id: techNodeId,
              position: {
                // Position relative to category node or use a layout algorithm
                x: categoryNode.position.x + (techIndex - 1.5) * 150,
                y: categoryNode.position.y + 100,
              },
              data: {
                label: tech.name,
                usage: tech.usage_count,
              },
              type: "output", // or 'default'
              sourcePosition: Position.Bottom,
              targetPosition: Position.Top,
              style: {
                background: "#4B5563", // bg-gray-600 (darker for dark theme)
                color: "#F3F4F6", // text-gray-100
                border: "1px solid #6B7280", // border-gray-500
                fontSize: "11px",
                borderRadius: "4px",
                padding: "8px 12px",
                textAlign: "center",
                minWidth: 80,
              },
            };
            newNodes.push(techNode);

            newEdges.push({
              id: `${categoryNodeId}-${techNodeId}-edge`,
              source: categoryNodeId,
              target: techNodeId,
              style: { stroke: "#9CA3AF", strokeWidth: 1.5 }, // gray-400
              markerEnd: { type: MarkerType.ArrowClosed, color: "#9CA3AF" },
            });
          });
          categoryIndex++;
        }
      }
    );
    setNodes(newNodes);
    setEdges(newEdges);
  }, [analysis, setNodes, setEdges]);

  if (!analysis || !analysis.technologies) {
    return (
      <div className="text-center p-4 text-gray-400">
        No technology relationship data available.
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="w-full h-[600px] bg-gray-800 rounded-lg shadow-xl p-1 border border-gray-700" // Adjusted for dark theme
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
        attributionPosition="bottom-left"
        className="bg-gray-800" // Ensure ReactFlow canvas also has dark background
      >
        <Controls className="text-white" />
        <Background color="#4B5563" gap={16} /> {/* Darker background grid */}
      </ReactFlow>
    </motion.div>
  );
};

export default TechnologyRelationshipGraph;
