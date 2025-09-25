import { createRouter, createWebHashHistory } from 'vue-router'
import WelcomeView from '../views/WelcomeView.vue'

const router = createRouter({
	history: createWebHashHistory(),
	routes: [
		{
			path: '/',
			name: 'home',
			component: WelcomeView
		},
		{
			path: '/system',
			name: 'system',
			// eslint-disable-next-line @typescript-eslint/explicit-function-return-type
			component: () => import('../views/SystemSettings.vue')
		},
		{
			path: '/display',
			name: 'display',
			// eslint-disable-next-line @typescript-eslint/explicit-function-return-type
			component: () => import('../views/DisplaySettings.vue')
		},
		{
			path: '/plugin',
			name: 'plugin',
			// eslint-disable-next-line @typescript-eslint/explicit-function-return-type
			component: () => import('../views/PluginSettings.vue')
		},
		{
			path: '/schedule',
			name: 'schedule',
			// eslint-disable-next-line @typescript-eslint/explicit-function-return-type
			component: () => import('../views/Scheduler.vue')
		},
		/*
		{
			path: '/setup',
			name: 'setup',
			// eslint-disable-next-line @typescript-eslint/explicit-function-return-type
			component: () => import('../views/SetupView.vue')
		},
		*/
	]
})
export default router