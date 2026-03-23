import './index.css'
import { createApp } from 'vue'
import { createLmsRouter } from './router'
import App from './App.vue'
import { createPinia } from 'pinia'
import dayjs from '@/utils/dayjs'
import { createDialog } from '@/utils/dialogs'
import translationPlugin from './translation'
import { usersStore } from './stores/user'
import { useShellStore } from './stores/shell'
import { initSocket } from './socket'
import { FrappeUI, setConfig, frappeRequest, pageMetaPlugin } from 'frappe-ui'
import { loadConfig } from './config'
import { createGatewayFetcher } from './request'

const MFE_ID = 'system-lms-frappe'

let appInstance = null
let shellStore = null

async function bootstrap(container, props) {
  const config = await loadConfig()

  // props.routePrefix takes precedence over config file (shell controls routing)
  const basePath = props.routePrefix || config.app_base_path || undefined
  const router = createLmsRouter(basePath)

  const pinia = createPinia()
  const app = createApp(App)

  setConfig('resourceFetcher', createGatewayFetcher(frappeRequest))

  app.use(FrappeUI, { socketio: false, call: false })
  app.use(pinia)
  app.use(router)
  app.use(translationPlugin)
  app.use(pageMetaPlugin)
  app.provide('$dayjs', dayjs)
  app.provide('$socket', initSocket())

  app.mount(container)

  const { userResource, allUsers } = usersStore()
  app.provide('$user', userResource)
  app.provide('$allUsers', allUsers)
  app.config.globalProperties.$user = userResource
  app.config.globalProperties.$dialog = createDialog

  appInstance = app

  // Initialise shell store and apply initial shell props
  shellStore = useShellStore()
  if (props.lang)  shellStore.setLang(props.lang)
  if (props.theme) shellStore.setTheme(props.theme)
  if (props.role)  shellStore.setRole(props.role)
}

// ── MFE contract registration ─────────────────────────────────────────────
// Register synchronously so shell polling finds the contract immediately.
// mount() is async — shell awaits it.
if (typeof window.__MCAIT_MFE__ !== 'undefined') {
  window.__MCAIT_MFE__[MFE_ID] = {
    async mount(container, props) {
      await bootstrap(container, props)
    },
    unmount(_container) {
      if (appInstance) {
        appInstance.unmount()
        appInstance = null
        shellStore = null
      }
    },
    update(props) {
      if (!shellStore) return
      if (props.lang)  shellStore.setLang(props.lang)
      if (props.theme) shellStore.setTheme(props.theme)
      if (props.role)  shellStore.setRole(props.role)
    },
  }
} else {
  // ── Standalone mode (outside shell) ──────────────────────────────────────
  // Runs exactly as before: mount directly to #app using config.json defaults.
  loadConfig().then((config) => {
    bootstrap(document.getElementById('app'), {
      routePrefix: config.app_base_path,
      initialPath: '/',
      lang: 'en',
      theme: 'light',
    })
  })
}
