<template>
	<div class="bg-surface-white w-full h-full">
		<div class="w-fit mx-auto mt-56 text-center p-4">
			<div class="text-3xl font-semibold text-ink-gray-5 pb-4 mb-2 border-b">
				{{ __('Not Permitted') }}
			</div>
			<div class="px-5 py-3">
				<div class="text-ink-gray-5">
					{{ __('You do not have permission to access this page.') }}
				</div>
				<router-link :to="{ name: 'Courses' }">
					<Button variant="solid" class="mt-2 w-full">
						{{ __('Checkout Courses') }}
					</Button>
				</router-link>
			</div>
		</div>
	</div>
</template>
<script setup>
import { Button, usePageMeta } from 'frappe-ui'
import { sessionStore } from '../stores/session'

const { brand } = sessionStore()

usePageMeta(() => {
	return {
		title: __('Not Permitted'),
		icon: brand.favicon,
	}
})
</script>
