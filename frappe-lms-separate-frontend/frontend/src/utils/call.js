import { getConfig } from '../config'

function buildUrl(method, apiBase) {
	if (method.startsWith('http')) return method
	if (method.startsWith('/')) return `${apiBase}${method}`
	return `${apiBase}/method/${method}`
}

export async function call(method, args, options = {}) {
	const apiBase = getConfig().api_base_url
	const url = buildUrl(method, apiBase)

	if (!args) args = {}

	const headers = Object.assign(
		{
			Accept: 'application/json',
			'Content-Type': 'application/json; charset=utf-8',
			'X-Frappe-Site-Name': window.location.hostname,
		},
		options.headers || {},
	)
	if (window.csrf_token && window.csrf_token !== '{{ csrf_token }}') {
		headers['X-Frappe-CSRF-Token'] = window.csrf_token
	}

	const res = await fetch(url, {
		method: 'POST',
		headers,
		body: JSON.stringify(args),
	})

	if (res.ok) {
		const data = await res.json()
		if (data.docs || method === 'login') return data
		if (data.exc) {
			try {
				console.groupCollapsed(method)
				console.log(`method: ${method}`)
				console.log(`params:`, args)
				const warning = JSON.parse(data.exc)
				for (const text of warning) console.log(text)
				console.groupEnd()
			} catch (e) {
				console.warn('Error printing debug messages', e)
			}
		}
		return data.message
	}

	const responseText = await res.text()
	let error
	try {
		error = JSON.parse(responseText)
	} catch (e) {
		error = {}
	}
	const errorParts = [
		[method, error?.exc_type, error?._error_message].filter(Boolean).join(' '),
	]
	let exception = error?.exc
	if (exception) {
		try {
			exception = JSON.parse(exception)[0]
		} catch (e) {}
	}
	const e = new Error(errorParts.join('\n'))
	e.exc_type = error?.exc_type
	e.exc = exception
	e.status = res.status
	e.messages =
		error?._server_messages != null
			? JSON.parse(error._server_messages)
			: []
	e.messages = e.messages.concat(error?.message || [])
	e.messages = e.messages
		.map((m) => {
			try {
				return typeof m === 'string' ? JSON.parse(m).message : m
			} catch (err) {
				return m
			}
		})
		.filter(Boolean)
	if (!e.messages.length) {
		e.messages = error?._error_message ? [error._error_message] : ['Internal Server Error']
	}

	if (options.onError) options.onError({ response: res, status: res.status, error: e })
	throw e
}
