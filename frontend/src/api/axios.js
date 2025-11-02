// Базовий URL API - використовує проксі в режимі розробки
import axios from 'axios'

const api = axios.create({ 
  baseURL: import.meta.env.DEV ? '/api' : 'http://localhost:8000'
})

export { api }
export default api
