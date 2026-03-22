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

export default function GraphVisualization({ data, selectedNode, onNodeSelect, highlightedNodes = [] }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Convert API data to ReactFlow format
  useEffect(() => {
    if (data?.nodes && data?.edges) {
      const flowNodes = data.nodes.map((node) => {
        const isInFlowPath = highlightedNodes.includes(node.id)
        const isSelected = selectedNode === node.id
        
        return {
          id: node.id,
          data: { label: node.label, icon: node.icon },
          position: calculatePosition(node.id, data.nodes.length),
          style: {
            background: isInFlowPath ? '#dc2626' : node.color,
            color: '#fff',
            border: isSelected ? '3px solid #1f2937' : isInFlowPath ? '3px solid #991b1b' : '2px solid rgba(0,0,0,0.1)',
            borderRadius: '8px',
            padding: '10px',
            fontSize: '12px',
            fontWeight: 'bold',
            width: '120px',
            textAlign: 'center',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            boxShadow: isInFlowPath ? '0 0 12px rgba(220, 38, 38, 0.4)' : 'none',
          },
        }
      })

      const flowEdges = data.edges.map((edge) => {
        const sourceInFlow = highlightedNodes.includes(edge.source)
        const targetInFlow = highlightedNodes.includes(edge.target)
        const edgeInFlow = sourceInFlow && targetInFlow
        
        return {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          animated: isSelected || edgeInFlow,
          style: {
            stroke: edgeInFlow ? '#dc2626' : selectedNode === edge.source || selectedNode === edge.target ? '#000' : '#ccc',
            strokeWidth: edgeInFlow ? 3 : selectedNode === edge.source || selectedNode === edge.target ? 2 : 1,
          },
        }
      })

      setNodes(flowNodes)
      setEdges(flowEdges)
    }
  }, [data, selectedNode, highlightedNodes, setNodes, setEdges])

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
