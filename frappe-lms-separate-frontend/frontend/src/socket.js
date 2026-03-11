import { io } from 'socket.io-client'
import { getConfig } from './config'

// Null socket that silently ignores all calls — used when socket.io is disabled.
const nullSocket = {
	on() {},
	off() {},
	emit() {},
	connect() {},
	disconnect() {},
	connected: false,
}

export function initSocket() {
	const config = getConfig()

	// Gateway/standalone mode: socketio_url from runtime config
	if (config.socketio_url) {
		// socket.io-client needs the server origin as the first arg and the
		// path (where the socket.io server listens) as an option.  When
		// socketio_url is a relative path like "/services/lms/socket.io",
		// connect to the current origin with that path.
		let origin
		let socketPath
		try {
			const parsed = new URL(config.socketio_url, window.location.origin)
			origin = parsed.origin
			socketPath = parsed.pathname
		} catch {
			origin = window.location.origin
			socketPath = config.socketio_url
		}
		// socket.io expects the path to end with /
		if (!socketPath.endsWith('/')) socketPath += '/'

		return io(origin, {
			path: socketPath,
			withCredentials: true,
			reconnectionDelay: 2000,
			reconnectionDelayMax: 10000,
		})
	}

	// socketio_url not configured — disable socket
	return nullSocket
}
