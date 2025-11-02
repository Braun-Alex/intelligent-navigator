import { createApp } from 'vue'
import { Quasar, Notify, Loading, Dialog, LoadingBar } from 'quasar'
import router from './router'
import App from './App.vue'

// Імпорт іконок та стилів Quasar
import '@quasar/extras/roboto-font/roboto-font.css'
import '@quasar/extras/material-icons/material-icons.css'
import '@quasar/extras/material-icons-outlined/material-icons-outlined.css'
import '@quasar/extras/material-icons-round/material-icons-round.css'
import '@quasar/extras/material-icons-sharp/material-icons-sharp.css'
import '@quasar/extras/mdi-v7/mdi-v7.css'
import '@quasar/extras/fontawesome-v6/fontawesome-v6.css'

// Імпорт стилів Quasar
import 'quasar/dist/quasar.css'

// Імпорт глобальних стилів
import './css/app.scss'

const app = createApp(App)

// Налаштування Quasar
app.use(Quasar, {
  plugins: {
    Notify,
    Loading,
    Dialog,
    LoadingBar
  },
  config: {
    brand: {
      primary: '#1976D2',
      secondary: '#26A69A',
      accent: '#9C27B0',
      dark: '#1d1d1d',
      positive: '#21BA45',
      negative: '#C10015',
      info: '#31CCEC',
      warning: '#F2C037'
    },
    notify: {
      position: 'top',
      timeout: 3000
    },
    loading: {
      spinnerColor: 'primary'
    }
  }
})

app.use(router)

app.mount('#q-app')
