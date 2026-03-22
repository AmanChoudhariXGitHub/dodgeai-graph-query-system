import { useState, useRef } from 'react'

export default function QueryInterface({ onQuery, loading, lastResponse }) {
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

  // Smart quick queries based on common patterns
  const quickQueries = [
    'Trace order #1 through delivery to invoice',
    'Find all incomplete orders',
    'Top 5 products by sales',
    'Payments made in last 30 days',
    'Orders without delivery',
  ]

  // Intent badge styling
  const getIntentBadgeStyle = (intent) => {
    const styles = {
      FLOW: 'bg-blue-100 text-blue-800',
      AGGREGATION: 'bg-green-100 text-green-800',
      GENERAL: 'bg-gray-100 text-gray-800',
    }
    return styles[intent] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="space-y-3">
      {/* Query Input Form */}
      <form onSubmit={handleSubmit} className="space-y-2">
        <textarea
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask questions like: 'Trace order #1', 'Find incomplete orders', 'Total revenue by customer'..."
          className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none text-sm"
          rows="3"
          disabled={loading}
        />
        
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition"
        >
          {loading ? (
            <span className="inline-flex items-center gap-2">
              <span className="animate-spin">⌛</span>
              Analyzing query...
            </span>
          ) : 'Execute Query'}
        </button>
      </form>

      {/* Last Query Intent Badge */}
      {lastResponse && lastResponse.intent && (
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-600">Last query type:</span>
          <span className={`px-2 py-1 rounded-full font-medium ${getIntentBadgeStyle(lastResponse.intent)}`}>
            {lastResponse.intent}
          </span>
        </div>
      )}

      {/* Quick Queries */}
      <div className="border-t pt-3">
        <p className="text-xs text-gray-600 font-medium mb-2">Smart queries:</p>
        <div className="space-y-1">
          {quickQueries.map((q, i) => (
            <button
              key={i}
              onClick={() => handleQuickQuery(q)}
              disabled={loading}
              className="w-full text-left text-xs p-2 hover:bg-blue-50 rounded border border-gray-200 transition disabled:opacity-50 text-gray-700"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Dataset Overview */}
      <div className="border-t pt-3 bg-gray-50 p-2 rounded text-xs text-gray-600">
        <p className="font-medium mb-1">Dataset coverage:</p>
        <div className="grid grid-cols-2 gap-2 text-gray-500">
          <div>• Orders & Items</div>
          <div>• Deliveries</div>
          <div>• Invoices</div>
          <div>• Payments</div>
        </div>
      </div>
    </div>
  )
}
