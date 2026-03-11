import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig(async ({ mode }) => {
	const isDev = mode === 'development'
	const frappeui = await importFrappeUIPlugin(isDev)

	return {
		base: '/services/lms/frontend/',
		build: {
			rollupOptions: {
				input: path.resolve(__dirname, 'index.standalone.html'),
			},
		},
		define: {
			__VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
		},
		plugins: [
			frappeui({
				frappeProxy: false,
				lucideIcons: true,
				jinjaBootData: false,
			}),
			vue(),
			VitePWA({
				registerType: 'autoUpdate',
				devOptions: {
					enabled: false,
				},
				workbox: {
					cleanupOutdatedCaches: true,
					maximumFileSizeToCacheInBytes: 5 * 1024 * 1024,
					globDirectory: '/usr/share/nginx/html',
					globPatterns: ['**/*.{js,ts,css,html,svg}'],
					runtimeCaching: [
						{
							urlPattern: ({ request }) =>
								request.destination === 'document',
							handler: 'NetworkFirst',
							options: {
								cacheName: 'html-cache',
							},
						},
					],
				},
				manifest: false,
			}),
		],
		server: {
			host: '0.0.0.0',
			allowedHosts: true,
		},
		resolve: {
			alias: {
				'@': path.resolve(__dirname, 'src'),
			},
		},
		optimizeDeps: {
			include: [
				'feather-icons',
				'tailwind.config.js',
				'interactjs',
				'highlight.js',
				'plyr',
			],
			exclude: mode === 'production' ? [] : ['frappe-ui'],
		},
	}
})

async function importFrappeUIPlugin(isDev) {
	if (isDev) {
		try {
			const module = await import('../frappe-ui/vite')
			return module.default
		} catch (error) {
			console.warn(
				'Local frappe-ui not found, falling back to npm package:',
				error.message
			)
		}
	}
	const module = await import('frappe-ui/vite')
	return module.default
}
