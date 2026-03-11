import { getConfig } from './config'

export function createGatewayFetcher(frappeRequest) {
	return function gatewayFetcher(options) {
		const apiBase = getConfig().api_base_url

		if (options.url && !options.url.startsWith('http')) {
			let url = options.url
			if (!url.startsWith('/')) {
				url = `/method/${url}`
			}
			options = { ...options, url: `${apiBase}${url}` }
		}

		return frappeRequest(options)
	}
}
