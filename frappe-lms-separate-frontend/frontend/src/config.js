/**
 * Runtime configuration loader.
 *
 * Loads config.json (served by nginx, injected via k8s ConfigMap).
 * The path is resolved relative to the app base so it works under any
 * sub-path (e.g. /services/lms/frontend/config.json).
 */

const defaults = {
	api_base_url: '',
	app_base_path: '/services/lms/frontend/',
	socketio_url: '',
}

let _config = null

export async function loadConfig() {
	if (_config) return _config

	let runtimeConfig = { ...defaults }

	try {
		const resp = await fetch(import.meta.env.BASE_URL + 'config.json')
		if (resp.ok) {
			const json = await resp.json()
			runtimeConfig = { ...defaults, ...json }
		}
	} catch {
		// config.json not found — use defaults
	}

	_config = runtimeConfig
	return _config
}

export function getConfig() {
	return _config || { ...defaults }
}
