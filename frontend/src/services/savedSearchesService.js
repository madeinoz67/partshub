import { api } from '../boot/axios'

/**
 * Saved Searches API Service
 * Provides methods for managing user's saved component searches
 */

/**
 * @typedef {Object} SearchParameters
 * @property {string} [search] - Search query string
 * @property {string} [category] - Component category filter
 * @property {string} [component_type] - Component type filter
 * @property {string} [stock_status] - Stock status filter
 * @property {string[]} [tags] - Tag filters
 * @property {string} [sort_by] - Sort field
 * @property {string} [sort_order] - Sort order (asc/desc)
 */

/**
 * @typedef {Object} SavedSearch
 * @property {string} id - Unique identifier
 * @property {string} user_id - User identifier
 * @property {string} name - Search name
 * @property {string} [description] - Optional description
 * @property {SearchParameters} search_parameters - Search parameters
 * @property {string} created_at - Creation timestamp
 * @property {string} updated_at - Last update timestamp
 * @property {string} [last_used_at] - Last execution timestamp
 */

/**
 * Create a new saved search
 * @param {string} name - Search name (1-100 characters)
 * @param {SearchParameters} searchParameters - Search parameters to save
 * @param {string} [description] - Optional description (max 500 characters)
 * @returns {Promise<SavedSearch>} Created saved search
 */
export async function createSavedSearch(name, searchParameters, description = null) {
  const response = await api.post('/api/v1/saved-searches', {
    name,
    search_parameters: searchParameters,
    description
  })
  return response.data
}

/**
 * Get paginated list of user's saved searches
 * @param {Object} options - Query options
 * @param {number} [options.skip=0] - Number of records to skip
 * @param {number} [options.limit=20] - Maximum records to return
 * @param {string} [options.sort_by='created_at'] - Sort field (name, created_at, last_used_at)
 * @param {string} [options.sort_order='desc'] - Sort order (asc, desc)
 * @returns {Promise<{searches: SavedSearch[], total: number}>} List of searches and total count
 */
export async function listSavedSearches(options = {}) {
  const {
    skip = 0,
    limit = 20,
    sort_by = 'created_at',
    sort_order = 'desc'
  } = options

  const response = await api.get('/api/v1/saved-searches', {
    params: { skip, limit, sort_by, sort_order }
  })
  return response.data
}

/**
 * Get a specific saved search by ID
 * @param {string} searchId - Saved search ID
 * @returns {Promise<SavedSearch>} Saved search details
 */
export async function getSavedSearch(searchId) {
  const response = await api.get(`/api/v1/saved-searches/${searchId}`)
  return response.data
}

/**
 * Update an existing saved search
 * @param {string} searchId - Saved search ID
 * @param {Object} updates - Fields to update
 * @param {string} [updates.name] - New name
 * @param {string} [updates.description] - New description
 * @param {SearchParameters} [updates.search_parameters] - New search parameters
 * @returns {Promise<SavedSearch>} Updated saved search
 */
export async function updateSavedSearch(searchId, updates) {
  const response = await api.put(`/api/v1/saved-searches/${searchId}`, updates)
  return response.data
}

/**
 * Delete a saved search
 * @param {string} searchId - Saved search ID
 * @returns {Promise<{message: string}>} Success message
 */
export async function deleteSavedSearch(searchId) {
  const response = await api.delete(`/api/v1/saved-searches/${searchId}`)
  return response.data
}

/**
 * Execute a saved search (updates last_used_at and returns search parameters)
 * @param {string} searchId - Saved search ID
 * @returns {Promise<{search_parameters: SearchParameters}>} Search parameters to execute
 */
export async function executeSavedSearch(searchId) {
  const response = await api.post(`/api/v1/saved-searches/${searchId}/execute`)
  return response.data
}

/**
 * Duplicate a saved search
 * @param {string} searchId - Saved search ID to duplicate
 * @param {string} [newName] - Optional new name (defaults to "Copy of {original}")
 * @returns {Promise<SavedSearch>} Newly created duplicate search
 */
export async function duplicateSavedSearch(searchId, newName = null) {
  const payload = newName ? { new_name: newName } : {}
  const response = await api.post(`/api/v1/saved-searches/${searchId}/duplicate`, payload)
  return response.data
}

/**
 * Get saved searches statistics
 * @returns {Promise<{total_searches: number, total_used: number, total_unused: number, most_used: SavedSearch[]}>} Statistics
 */
export async function getSavedSearchesStats() {
  const response = await api.get('/api/v1/saved-searches/stats')
  return response.data
}

export default {
  createSavedSearch,
  listSavedSearches,
  getSavedSearch,
  updateSavedSearch,
  deleteSavedSearch,
  executeSavedSearch,
  duplicateSavedSearch,
  getSavedSearchesStats
}
