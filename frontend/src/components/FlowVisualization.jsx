const ENTITY_COLORS = {
  orders: '#3B82F6',      // Blue
  customers: '#8B5CF6',   // Purple
  deliveries: '#F59E0B',  // Amber
  invoices: '#EC4899',    // Pink
  payments: '#10B981',    // Emerald
  products: '#6366F1',    // Indigo
  order_items: '#14B8A6', // Teal
}

const ENTITY_ICONS = {
  orders: '📦',
  customers: '👤',
  deliveries: '🚚',
  invoices: '📄',
  payments: '💳',
  products: '🏷️',
  order_items: '📋',
}

export default function FlowVisualization({ result, flowPath = [] }) {
  // Extract entity types from result
  const entities = Object.keys(result).filter((k) => result[k] !== null)

  // Order by flow path if available
  const orderedEntities = flowPath.filter((e) => entities.includes(e)).concat(entities.filter((e) => !flowPath.includes(e)))

  return (
    <div className="p-3 bg-white border border-gray-200 rounded-lg">
      <p className="text-xs font-medium text-gray-700 mb-3">Order-to-Payment Flow:</p>

      <div className="flow-visualization">
        {orderedEntities.map((entity, index) => (
          <div key={entity} className="flex items-center gap-2">
            <div
              className="flow-node"
              style={{
                borderColor: ENTITY_COLORS[entity],
                backgroundColor: ENTITY_COLORS[entity] + '15',
              }}
            >
              <span className="text-lg">{ENTITY_ICONS[entity]}</span>
              <span className="text-xs font-medium text-gray-700">{entity}</span>

              {/* Entity data preview */}
              {result[entity] && (
                <div className="text-xs text-gray-600 mt-1 space-y-1 max-w-[120px]">
                  {Object.entries(result[entity])
                    .slice(0, 3)
                    .map(([key, value]) => (
                      <div key={key} className="truncate">
                        <span className="font-medium">{key}:</span>{' '}
                        {value === null ? <em>null</em> : String(value).substring(0, 15)}
                      </div>
                    ))}
                </div>
              )}
            </div>

            {/* Arrow connector (except for last item) */}
            {index < orderedEntities.length - 1 && (
              <div className="text-gray-400 text-lg">→</div>
            )}
          </div>
        ))}
      </div>

      {/* Detailed view */}
      <div className="mt-3 space-y-2 border-t pt-3">
        {orderedEntities.map((entity) => (
          <details key={entity} className="text-xs">
            <summary
              className="cursor-pointer font-medium p-2 rounded hover:bg-gray-50"
              style={{ color: ENTITY_COLORS[entity] }}
            >
              {ENTITY_ICONS[entity]} {entity} Details
            </summary>
            <div className="bg-gray-50 p-2 rounded mt-1 space-y-1 ml-3">
              {result[entity] &&
                Object.entries(result[entity]).map(([key, value]) => (
                  <div key={key} className="flex justify-between gap-2">
                    <span className="text-gray-600">{key}:</span>
                    <span className="text-gray-800 font-mono">{value === null ? 'null' : String(value)}</span>
                  </div>
                ))}
            </div>
          </details>
        ))}
      </div>
    </div>
  )
}
