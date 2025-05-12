import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import axios from 'axios'
import 'nprogress/nprogress.css'
import NProgress from 'nprogress'

// Configure Axios global settings
axios.defaults.baseURL = '/api'
axios.interceptors.request.use((config) => {
  NProgress.start()
  return config
})
axios.interceptors.response.use(
  (response) => {
    NProgress.done()
    return response
  },
  (error) => {
    NProgress.done()
    console.error('Request failed:', error)
    return Promise.reject(error)
  },
)

// Initialize Pinia with persisted state plugin
const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// Create and mount the Vue app
const app = createApp(App)

app.use(router)
app.use(pinia)
app.use(ElementPlus)

app.mount('#app')

console.log('Main application initialized')
