import { useState, useEffect } from 'react'
import './index.css'
import GraphVisualization from './components/GraphVisualization'
import QueryInterface from './components/QueryInterface'
import ResultsPanel from './components/ResultsPanel'
import { queryAPI } from './services/api'

export default function App() {
  const [graphData, setGraphData] = useState(null)
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)

  useEffect(() => {
    // Load graph data on mount
    loadGraphData()
  }, [])

  const loadGraphData = async () => {
    try {
      setLoading(true)
      const data = await queryAPI.getGraph()
      setGraphData(data)
    } catch (err) {
      setError(`Failed to load graph: ${err.message}`)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleQuery = async (query) => {
    try {
      setLoading(true)
      setError(null)
      const result = await queryAPI.query(query)
      setResponse(result)
    } catch (err) {
      setError(`Query failed: ${err.message}`)
      console.error(err)
      setResponse(null)
    } finally {
      setLoading(false)
    }
  }

  const handleNodeSelect = (nodeId) => {
    setSelectedNode(nodeId)
  }

  return (
    <div className="w-full h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">ERP Graph Query System</h1>
            <p className="text-sm text-gray-600 mt-1">Natural language queries for order-to-cash flows</p>
          </div>
          <div className="flex items-center gap-4 text-sm">
            {graphData && (
              <>
                <span className="text-gray-600"><span className="font-semibold text-gray-900">{graphData.nodes.length}</span> entities</span>
                {response?.success && <span className="text-green-600 font-medium">✓ Query successful</span>}
              </>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Center - Graph Visualization */}
        <div className="flex-1 bg-white overflow-hidden border-r border-gray-200">
          {graphData ? (
            <GraphVisualization
              data={graphData}
              selectedNode={selectedNode}
              onNodeSelect={handleNodeSelect}
              highlightedNodes={response?.flow_path || []}
            />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <div className="text-3xl mb-2">⏳</div>
                <p>Loading graph structure...</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Query Interface & Results */}
        <div className="w-96 flex flex-col bg-white border-l border-gray-200 overflow-hidden">
          {/* Query Input */}
          <div className="p-4 border-b border-gray-200 overflow-y-auto max-h-64">
            <div className="mb-3 text-xs p-2 bg-blue-50 border border-blue-200 rounded">
              <span className="font-semibold">💡 Tip:</span> Ask "Trace order #1" or "Top products by revenue"
            </div>
            <QueryInterface onQuery={handleQuery} loading={loading} lastResponse={response} />
          </div>

          {/* Results */}
          <div className="flex-1 overflow-y-auto p-4">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 text-sm font-medium">❌ Error</p>
                <p className="text-red-700 text-xs mt-1">{error}</p>
              </div>
            )}

            <ResultsPanel result={response} loading={loading} />
          </div>
        </div>
      </div>
    </div>
  )
}
