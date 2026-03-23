import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useShellStore = defineStore('shell', () => {
	const lang = ref('en')
	const theme = ref('light')
	const role = ref(null)

	function setLang(value) {
		lang.value = value
	}

	function setTheme(value) {
		theme.value = value
		// Sync theme class on document root so Tailwind dark mode works
		if (typeof document !== 'undefined')
			document.documentElement.classList.toggle('dark', value === 'dark')
	}

	function setRole(value) {
		role.value = value
	}

	return { lang, theme, role, setLang, setTheme, setRole }
})
