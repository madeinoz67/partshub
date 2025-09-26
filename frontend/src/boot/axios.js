import { boot } from 'quasar/wrappers'
import axios from 'axios'

// Create axios instance
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000
})

export default boot(({ app }) => {
  // Make axios available in components via this.$axios and this.$api
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
})

export { api }