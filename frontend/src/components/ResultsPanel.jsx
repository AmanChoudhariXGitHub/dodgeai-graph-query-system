import { useState } from 'react'
import FlowVisualization from './FlowVisualization'

export default function ResultsPanel({ result }) {
  const [expandedRow, setExpandedRow] = useState(null)

  if (!result.success) {
    return (
      <div className="space-y-3">
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800 text-sm font-medium">Query Failed</p>
          <p className="text-red-700 text-sm mt-1">{result.error}</p>
        </div>

        {result.steps && result.steps.length > 0 && (
          <div className="border rounded-lg p-3 bg-gray-50">
            <p className="text-xs font-medium text-gray-700 mb-2">Pipeline Steps:</p>
            <div className="space-y-1">
              {result.steps.map((step, i) => (
                <div key={i} className="text-xs text-gray-600 flex gap-2">
                  <span className={step.passed ? '✓' : '✗'}></span>
                  <span>{step.step}</span>
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
          <p className="text-green-800 text-sm font-medium">✓ Flow Trace Complete</p>
        </div>

        <FlowVisualization result={result.result} flowPath={result.flow_path} />

        {result.execution_time_ms && (
          <p className="text-xs text-gray-500">Executed in {result.execution_time_ms}ms</p>
        )}
      </div>
    )
  }

  // Show regular results table
  const rows = result.result?.rows || []
  const rowCount = result.result?.count || 0

  return (
    <div className="space-y-3">
      <div className="p-2 bg-green-50 border border-green-200 rounded-lg">
        <p className="text-green-800 text-sm font-medium">✓ {rowCount} rows returned</p>
      </div>

      {result.intent && (
        <div className="text-xs text-gray-600 p-2 bg-gray-50 rounded border border-gray-200">
          <span className="font-medium">Intent:</span> {result.intent}
        </div>
      )}

      {result.sql && (
        <details className="text-xs">
          <summary className="cursor-pointer font-medium text-gray-700 p-2 hover:bg-gray-50 rounded">
            Generated SQL
          </summary>
          <pre className="bg-gray-900 text-green-400 p-2 rounded mt-1 overflow-x-auto text-xs">
            {result.sql}
          </pre>
        </details>
      )}

      {/* Results Table */}
      {rows.length > 0 && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="bg-gray-100 border-b">
                <tr>
                  {Object.keys(rows[0]).map((key) => (
                    <th key={key} className="px-2 py-2 text-left text-gray-700 font-medium">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr
                    key={i}
                    className="border-b hover:bg-gray-50 cursor-pointer"
                    onClick={() => setExpandedRow(expandedRow === i ? null : i)}
                  >
                    {Object.entries(row).map(([key, value]) => (
                      <td key={key} className="px-2 py-2 text-gray-700">
                        <span className="truncate block max-w-[80px]">
                          {value === null ? <em className="text-gray-400">null</em> : String(value).substring(0, 20)}
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
        <div className="p-3 bg-gray-100 rounded text-center text-gray-600">
          <p className="text-sm">No results</p>
        </div>
      )}

      {result.execution_time_ms && (
        <p className="text-xs text-gray-500">Executed in {result.execution_time_ms}ms</p>
      )}
    </div>
  )
}
