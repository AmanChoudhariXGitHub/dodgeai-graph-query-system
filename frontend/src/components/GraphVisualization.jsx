import { useCallback, useEffect, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MiniMap,
} from 'reactflow'
import 'reactflow/dist/style.css'

export default function GraphVisualization({ data, selectedNode, onNodeSelect }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Convert API data to ReactFlow format
  useEffect(() => {
    if (data?.nodes && data?.edges) {
      const flowNodes = data.nodes.map((node) => ({
        id: node.id,
        data: { label: node.label, icon: node.icon },
        position: calculatePosition(node.id, data.nodes.length),
        style: {
          background: node.color,
          color: '#fff',
          border: selectedNode === node.id ? '3px solid #000' : '2px solid rgba(0,0,0,0.1)',
          borderRadius: '8px',
          padding: '10px',
          fontSize: '12px',
          fontWeight: 'bold',
          width: '120px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s ease',
        },
      }))

      const flowEdges = data.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        animated: selectedNode === edge.source || selectedNode === edge.target,
        style: {
          stroke: selectedNode === edge.source || selectedNode === edge.target ? '#000' : '#ccc',
          strokeWidth: selectedNode === edge.source || selectedNode === edge.target ? 2 : 1,
        },
      }))

      setNodes(flowNodes)
      setEdges(flowEdges)
    }
  }, [data, selectedNode, setNodes, setEdges])

  const handleNodeClick = useCallback(
    (event, node) => {
      onNodeSelect(node.id)
    },
    [onNodeSelect]
  )

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  )
}

// Calculate circular layout for nodes
function calculatePosition(id, totalNodes, radius = 200) {
  const nodeIndex = ['customers', 'orders', 'order_items', 'products', 'deliveries', 'invoices', 'payments'].indexOf(
    id
  )
  const angle = (nodeIndex / totalNodes) * 2 * Math.PI
  return {
    x: radius * Math.cos(angle),
    y: radius * Math.sin(angle),
  }
}
