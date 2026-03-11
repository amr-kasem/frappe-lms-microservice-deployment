import { getConfig } from '../config'

export function getLmsBasePath() {
	// Standalone mode: use app_base_path from /config.json
	const config = getConfig()
	if (config.app_base_path) {
		return config.app_base_path.replace(/^\/|\/$/g, '')
	}
	return 'services/lms/frontend'
}

export function getLmsRoute(path = '') {
	const base = getLmsBasePath()
	if (!path) {
		return base
	}
	const normalized = path.startsWith('/') ? path.slice(1) : path
	return `/${base}/${normalized}`
}
