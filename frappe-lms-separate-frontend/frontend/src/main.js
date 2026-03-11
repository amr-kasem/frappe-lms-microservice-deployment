import './index.css'
import { createApp } from 'vue'
import { createLmsRouter } from './router'
import App from './App.vue'
import { createPinia } from 'pinia'
import dayjs from '@/utils/dayjs'
import { createDialog } from '@/utils/dialogs'
import translationPlugin from './translation'
import { usersStore } from './stores/user'
import { initSocket } from './socket'
import { FrappeUI, setConfig, frappeRequest, pageMetaPlugin } from 'frappe-ui'
import { loadConfig } from './config'
import { createGatewayFetcher } from './request'

async function bootstrap() {
	const config = await loadConfig()

	const router = createLmsRouter(config.app_base_path || undefined)

	let pinia = createPinia()
	let app = createApp(App)

	setConfig('resourceFetcher', createGatewayFetcher(frappeRequest))

	app.use(FrappeUI, { socketio: false, call: false })
	app.use(pinia)
	app.use(router)
	app.use(translationPlugin)
	app.use(pageMetaPlugin)
	app.provide('$dayjs', dayjs)
	app.provide('$socket', initSocket())
	app.mount('#app')

	const { userResource, allUsers } = usersStore()
	app.provide('$user', userResource)
	app.provide('$allUsers', allUsers)

	app.config.globalProperties.$user = userResource
	app.config.globalProperties.$dialog = createDialog
}

bootstrap()
