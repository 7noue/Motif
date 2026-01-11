import adapter from '@sveltejs/adapter-auto';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),

	kit: {
		adapter: adapter(),

		// This allows you to use imports like: import X from "@/components/..."
		alias: {
			"@": "./src/lib"
		}
	}
};

export default config;