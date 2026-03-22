import { useState } from 'react'
import FlowVisualization from './FlowVisualization'

export default function ResultsPanel({ result, loading }) {
  const [expandedRow, setExpandedRow] = useState(null)
  const [copiedSQL, setCopiedSQL] = useState(false)

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        <div className="text-center">
          <div className="text-3xl mb-2">⏳</div>
          <p className="text-sm">Processing query...</p>
          <div className="mt-3 space-y-1 text-xs text-gray-400">
            <p>• Validating domain</p>
            <p>• Generating SQL</p>
            <p>• Executing safely</p>
          </div>
        </div>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="h-full flex items-center justify-center text-gray-400">
        <div className="text-center">
          <div className="text-3xl mb-2">📊</div>
          <p className="text-sm">Results will appear here</p>
        </div>
      </div>
    )
  }

  const copySQL = () => {
    navigator.clipboard.writeText(result.sql)
    setCopiedSQL(true)
    setTimeout(() => setCopiedSQL(false), 2000)
  }

  if (!result.success) {
    return (
      <div className="space-y-3">
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-900 text-sm font-medium flex items-center gap-2">
            <span>❌</span> Query Out of Scope
          </p>
          <p className="text-red-700 text-sm mt-2">{result.error}</p>
          <p className="text-xs text-red-600 mt-2">This system only answers questions about orders, deliveries, invoices, payments, customers, and products.</p>
        </div>

        {result.steps && result.steps.length > 0 && (
          <div className="border rounded-lg p-3 bg-gray-50">
            <p className="text-xs font-medium text-gray-700 mb-2">Pipeline Trace:</p>
            <div className="space-y-1">
              {result.steps.map((step, i) => (
                <div key={i} className="text-xs text-gray-600 flex gap-2">
                  <span className={step.passed ? '✓' : '✗'} style={{color: step.passed ? '#10b981' : '#ef4444'}}></span>
                  <span className="capitalize">{step.step.replace('_', ' ')}</span>
                  {step.error && <span className="text-red-600">({step.error})</span>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    )
  }

  // Show flow visualization if available
  if (result.flow_path && result.result) {
    return (
      <div className="space-y-3">
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-green-900 text-sm font-medium flex items-center gap-2">
            <span>✓</span> Flow Trace Complete
          </p>
        </div>

        {result.sql && (
          <div className="border border-gray-200 rounded-lg bg-gray-900 p-2">
            <div className="flex justify-between items-center mb-2">
              <p className="text-xs font-medium text-gray-300">Generated SQL</p>
              <button
                onClick={copySQL}
                className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded transition"
              >
                {copiedSQL ? '✓ Copied' : 'Copy'}
              </button>
            </div>
            <pre className="text-green-400 overflow-x-auto text-xs leading-tight">{result.sql}</pre>
          </div>
        )}

        <FlowVisualization result={result.result} flowPath={result.flow_path} highlightedNodes={result.flow_path} />

        <div className="flex justify-between text-xs text-gray-500 p-2 bg-gray-50 rounded">
          <span>⏱ {result.execution_time_ms}ms</span>
          <span>🔗 {result.flow_path.length} entities in flow</span>
        </div>
      </div>
    )
  }

  // Show regular results table
  const rows = result.result?.rows || []
  const rowCount = result.result?.count || 0

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-start">
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg flex-1">
          <p className="text-green-900 text-sm font-medium">✓ {rowCount} rows returned</p>
        </div>
        {result.execution_time_ms && (
          <div className="ml-2 p-3 bg-gray-50 border border-gray-200 rounded-lg text-right">
            <p className="text-xs text-gray-600">⏱ {result.execution_time_ms}ms</p>
          </div>
        )}
      </div>

      {result.intent && (
        <div className="inline-block text-xs px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium capitalize">
          {result.intent.toLowerCase()} query
        </div>
      )}

      {result.sql && (
        <details className="border border-gray-200 rounded-lg">
          <summary className="cursor-pointer font-medium text-gray-700 p-2 hover:bg-gray-50 flex justify-between items-center">
            <span>Generated SQL</span>
            <span className="text-xs text-gray-400">→</span>
          </summary>
          <div className="bg-gray-900 p-2 border-t">
            <div className="flex justify-end mb-1">
              <button
                onClick={copySQL}
                className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded transition"
              >
                {copiedSQL ? '✓ Copied' : 'Copy'}
              </button>
            </div>
            <pre className="text-green-400 overflow-x-auto text-xs leading-tight">{result.sql}</pre>
          </div>
        </details>
      )}

      {/* Results Table */}
      {rows.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-xs">
              <thead className="bg-gray-100 border-b sticky top-0">
                <tr>
                  {Object.keys(rows[0]).map((key) => (
                    <th key={key} className="px-3 py-2 text-left text-gray-700 font-semibold whitespace-nowrap">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i} className="border-b hover:bg-blue-50 transition">
                    {Object.entries(row).map(([key, value]) => (
                      <td key={key} className="px-3 py-2 text-gray-700">
                        <span className="block truncate max-w-xs" title={value === null ? 'null' : String(value)}>
                          {value === null ? <em className="text-gray-400">null</em> : String(value)}
                        </span>
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {rows.length === 0 && (
        <div className="p-4 bg-gray-100 rounded text-center text-gray-600">
          <p className="text-sm">No results found</p>
        </div>
      )}
    </div>
  )
}
