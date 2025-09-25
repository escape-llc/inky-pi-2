<script setup lang="ts">
import { reactive } from 'vue'

const appversion = __APP_VERSION__;
</script>

<template>
	<ul class="versions">
		<li class="app-version">MediaLab v{{ appversion }}</li>
		<!--
		<li class="electron-version">Electron v{{ versions.electron }}</li>
		<li class="chrome-version">Chromium v{{ versions.chrome }}</li>
		<li class="node-version">Node v{{ versions.node }}</li>
		-->
	</ul>
</template>
