import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { reveal } from './directives/reveal'
import { initLocale } from './i18n'
import { registerSW } from 'virtual:pwa-register'
import './assets/main.css'
import './assets/additions.css'
import './assets/admin.css'

initLocale()

// Service worker PWA : app shell en cache + mise à jour automatique
registerSW({ immediate: true })

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.directive('reveal', reveal)
app.mount('#app')
