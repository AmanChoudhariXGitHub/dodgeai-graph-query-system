import { useState, useRef } from 'react'

export default function QueryInterface({ onQuery, loading }) {
  const [query, setQuery] = useState('')
  const inputRef = useRef(null)

  const handleSubmit = (e) => {
    e.preventDefault()
    if (query.trim() && !loading) {
      onQuery(query.trim())
      setQuery('')
    }
  }

  const handleQuickQuery = (quickQuery) => {
    onQuery(quickQuery)
  }

  const quickQueries = [
    'Trace order #1',
    'Show all orders',
    'List customers',
    'Count payments',
  ]

  return (
    <div className="space-y-3">
      {/* Query Input Form */}
      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question about orders, invoices, deliveries, or payments..."
          className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          rows="3"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition"
        >
          {loading ? 'Loading...' : 'Query'}
        </button>
      </form>

      {/* Quick Queries */}
      <div className="border-t pt-3">
        <p className="text-xs text-gray-600 font-medium mb-2">Quick queries:</p>
        <div className="space-y-1">
          {quickQueries.map((q, i) => (
            <button
              key={i}
              onClick={() => handleQuickQuery(q)}
              disabled={loading}
              className="w-full text-left text-xs p-2 hover:bg-gray-100 rounded border border-gray-200 transition disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Help Info */}
      <div className="border-t pt-3 text-xs text-gray-600">
        <p className="font-medium mb-1">Query tips:</p>
        <ul className="list-disc list-inside space-y-1 text-gray-500">
          <li>Use entity IDs (order #1, invoice #5)</li>
          <li>Ask about aggregates (count, total)</li>
          <li>Trace flows through the system</li>
        </ul>
      </div>
    </div>
  )
}
