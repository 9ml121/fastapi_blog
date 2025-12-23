import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth.store'

import './styles/main.css'
import './styles/auth.css' 

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')

// 应用启动时检查并恢复登录状态
const authStore = useAuthStore()
authStore.checkAuth()
