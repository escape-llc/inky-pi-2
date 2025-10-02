<template>
	<div style="width:100%">
		<BasicForm :form="form" :baseUrl="API_URL" class="form">
			<template #header>
				<Toolbar style="width:100%" class="p-1 mt-2">
					<template #start>
						<div style="font-weight: bold;font-size:150%">Display Settings</div>
					</template>
					<template #end>
						<InputGroup>
							<Button size="small" icon="pi pi-check" severity="success" />
							<Button size="small" icon="pi pi-times" severity="danger" />
						</InputGroup>
					</template>
				</Toolbar>
			</template>
			<template #group-header="slotProps">
				<h3 class="mb-0">{{ slotProps.label }}</h3>
			</template>
		</BasicForm>
	</div>
</template>
<script setup lang="ts">
import displayJson from "../assets/display.json"
import BasicForm from "../components/BasicForm.vue"
import type {FormDef} from "../components/BasicForm.vue"
import {ref} from "vue"
import { InputGroup, InputGroupAddon, Button, Message, Toolbar, Select } from 'primevue';
const form = ref<FormDef>(structuredClone(displayJson))
const API_URL = import.meta.env.VITE_API_URL
</script>
<style scoped>
.form {
	width: 50%;
	margin: auto;
}
</style>