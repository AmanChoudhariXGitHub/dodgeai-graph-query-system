import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const queryAPI = {
  // Submit a natural language query
  query: async (query) => {
    try {
      const response = await api.post('/api/query', { query })
      return response.data
    } catch (error) {
      throw error.response?.data || error.message
    }
  },

  // Trace an entity through the flow
  trace: async (entityId, entityType = 'orders') => {
    try {
      const response = await api.post('/api/trace', {
        entity_id: entityId,
        entity_type: entityType,
      })
      return response.data
    } catch (error) {
      throw error.response?.data || error.message
    }
  },

  // Get graph structure
  getGraph: async () => {
    try {
      const response = await api.get('/api/graph')
      return response.data
    } catch (error) {
      throw error.response?.data || error.message
    }
  },

  // Get neighbors of an entity
  getNeighbors: async (entityType) => {
    try {
      const response = await api.get(`/api/graph/neighbors/${entityType}`)
      return response.data
    } catch (error) {
      throw error.response?.data || error.message
    }
  },

  // Get database schema
  getSchema: async () => {
    try {
      const response = await api.get('/api/schema')
      return response.data
    } catch (error) {
      throw error.response?.data || error.message
    }
  },

  // Initialize sample data
  initData: async () => {
    try {
      const response = await api.post('/api/init-data')
      return response.data
    } catch (error) {
      throw error.response?.data || error.message
    }
  },

  // Health check
  health: async () => {
    try {
      const response = await api.get('/health')
      return response.data
    } catch (error) {
      throw error.response?.data || error.message
    }
  },
}

export default api
