<template>
	<div style="width:100%">
		<BasicForm :form="form" :baseUrl="API_URL" class="form">
			<template #header>
				<Toolbar style="width:100%" class="p-1 mt-2">
					<template #start>
						<div style="font-weight: bold;font-size:150%">System Settings</div>
					</template>
					<template #end>
						<InputGroup>
							<Button size="small" icon="pi pi-check" severity="success" />
							<Button size="small" icon="pi pi-times" severity="danger" />
						</InputGroup>
					</template>
				</Toolbar>
			</template>
		</BasicForm>
	</div>
</template>
<script setup lang="ts">
import BasicForm from "../components/BasicForm.vue"
import type {FormDef} from "../components/BasicForm.vue"
import { ref, onMounted } from "vue"
import { InputGroup, InputGroupAddon, Button, Message, Toolbar, Select } from 'primevue';
const form = ref<FormDef>()
const API_URL = import.meta.env.VITE_API_URL
onMounted(() => {
	const schemaUrl = `${API_URL}/api/schemas/system`
	const settingsUrl = `${API_URL}/api/settings/system`
	const px0 = fetch(schemaUrl).then(rx => rx.json())
	const px1 = fetch(settingsUrl).then(rx => rx.json())
	Promise.all([px0,px1])
	.then(pxs => {
		console.log("schema,settings", pxs[0], pxs[1])
		form.value = pxs[0]
	})
	.catch(ex => {
		console.error("fetch.unhandled", ex)
	})
})
</script>
<style scoped>
.form {
	width: 50%;
	margin: auto;
}
</style>