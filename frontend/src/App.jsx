import { useState, useEffect } from 'react'
import './index.css'
import GraphVisualization from './components/GraphVisualization'
import QueryInterface from './components/QueryInterface'
import ResultsPanel from './components/ResultsPanel'
import { queryAPI } from './services/api'

export default function App() {
  const [graphData, setGraphData] = useState(null)
  const [queryResult, setQueryResult] = useState(null)
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
      setQueryResult(result)
    } catch (err) {
      setError(`Query failed: ${err.message}`)
      console.error(err)
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
      <header className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold">📊 Graph Query System</h1>
          <p className="text-blue-100 mt-1">Natural language queries on ERP data</p>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Graph Visualization */}
        <div className="flex-1 border-r border-gray-200 bg-white overflow-hidden">
          {graphData && (
            <GraphVisualization
              data={graphData}
              selectedNode={selectedNode}
              onNodeSelect={handleNodeSelect}
            />
          )}
          {!graphData && !loading && (
            <div className="flex items-center justify-center h-full text-gray-500">
              <div className="text-center">
                <p className="mb-2">Loading graph data...</p>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Query Interface & Results */}
        <div className="w-96 flex flex-col border-l border-gray-200 bg-white overflow-hidden">
          {/* Query Input */}
          <div className="p-4 border-b border-gray-200">
            <QueryInterface onQuery={handleQuery} loading={loading} />
          </div>

          {/* Results */}
          <div className="flex-1 overflow-y-auto p-4">
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-red-800 text-sm font-medium">Error:</p>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
            )}

            {queryResult && (
              <ResultsPanel result={queryResult} />
            )}

            {!queryResult && !error && (
              <div className="text-center text-gray-500 mt-8">
                <p className="text-sm">Enter a query to get started</p>
                <p className="text-xs mt-2 text-gray-400">Examples:</p>
                <p className="text-xs text-gray-400 mt-1">• "Trace order #1"</p>
                <p className="text-xs text-gray-400">• "Show me all orders"</p>
                <p className="text-xs text-gray-400">• "How many payments?"</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
