import { createConfig } from '@davidteju/dev-config/eslint';
import svelteConfig from './svelte.config.js';

export default [
	...(await createConfig({ framework: 'svelte', svelteConfig })),
	{ ignores: ['build/', '.svelte-kit/', 'node_modules/'] }
];
