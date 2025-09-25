<template>
	<div class="flex flex-column" style="height:80vh;width:100%;justify-items: stretch;align-items: stretch;">
	<Toolbar class="p-0">
		<template #start>
			<div style="font-size:150%">Scheduler</div>
		</template>
	</Toolbar>
	<AlCalendar style="width:100%" class="calendar" :dateRange="dateRange" :timeRange="timeRange" :eventList="eventList">
		<template #dayheader="{ day }">
			<div class="day-header" :style="{'grid-column': day.column, 'grid-row': day.row }">
				<div>
					<span class="day-header-day">{{ day.date.getDate() }}</span>
					<span class="day-header-dow">{{ new Intl.DateTimeFormat("en-US", {weekday:'short'}).format(day.date) }}</span>
				</div>
			</div>
		</template>
		<template #timeheader="{ time }">
			<div class="time-header" :style="{'grid-row':time.row,'grid-column':time.column}">
				<div>
					<span class="time-header-hour">{{ new Intl.DateTimeFormat("en-US", {timeZone:"GMT",hour12: false, hour:'2-digit'}).format(time.date) }}</span>
					<span class="time-header-minute">{{ new Intl.DateTimeFormat("en-US", {hour12: false, minute:'2-digit'}).format(time.date).padStart(2, '0') }}</span>
				</div>
			</div>
		</template>
	</AlCalendar>
	</div>
</template>
<script setup lang="ts">
import Toolbar from "primevue/toolbar"
import AlCalendar from "../components/AlCalendar.vue"
import { DateBuilder } from "../components/DateUtils"
import type { DateRange, TimeRange, EventInfo } from "../components/AlCalendar.vue"
import {ref} from "vue"

function eraseTime(dx:Date):Date {
	let start = new Date(dx.getTime());
	start.setHours(0);
	start.setMinutes(0);
	start.setSeconds(0);
	start.setMilliseconds(0);
	return start;
}
function addDays(date: Date, days: number): Date {
	let ts = days * MS_PER_DAY;
	let start = new Date(date.getTime() + ts);
	return start;
}
function addHours(date: Date, hours:number):Date {
	const dx = eraseTime(date);
	return new Date(dx.getTime() + hours * 60 * 1000)
}
const MS_PER_DAY = 86400000;
const now = new Date()
const dateRange = ref<DateRange>({ start:new Date(), end:new Date(now.getTime() + 6*MS_PER_DAY) })
const timeRange = ref<TimeRange>({start: 0, end: 1440, interval:30 })
const eventList = ref<EventInfo[]>([
	{
		start: new DateBuilder(new Date()).midnight().date(),
		duration: 120,
		title: "my test event",
	} satisfies EventInfo,
	{
		start: new DateBuilder(new Date()).midnight().days(1).hours(2).date(),
		duration: 60,
		title: "my other test event",
	} satisfies EventInfo,
	{
		start: new DateBuilder(new Date()).midnight().days(2).hours(2).date(),
		duration: 60,
		title: "my other other test event",
	} satisfies EventInfo,
	{
		start: new DateBuilder(new Date()).midnight().days(3).hours(3).date(),
		duration: 180,
		title: "my other other other test event",
	} satisfies EventInfo,
	{
		start: new DateBuilder(new Date()).midnight().days(4).hours(21).date(),
		duration: 180,
		title: "my late night test event",
	} satisfies EventInfo
])
</script>
<style scoped>
.calendar {
	height: calc(var(--calendar-height));
}
.day-header {
	display: flex;
	align-items: center;
	justify-content: center;
	font-weight: bold;
	background-color: #e9e9e9;
	border-bottom: 1px solid #ccc;
	height: fit-content;
}
.day-header-day {
	font-size: 2rem;
	vertical-align: baseline;
}
.day-header-dow {
	font-size: 1.2rem;
	margin-left:.15rem;
	vertical-align: baseline;
}
.time-header {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	padding-right: .1rem;
	font-size: 0.8rem;
	color: #555;
	border-top: 1px dashed #eee;
	height:fit-content;
}
.time-header:first-child {
	border-bottom: none; /* No dashed line above the first label */
}
.time-header-hour {
	font-size: 1rem;
	font-weight: bold;
	vertical-align: baseline;
}
.time-header-minute {
	font-size: .75rem;
	margin-left:.1rem;
	vertical-align: text-top;
}
</style>
<style>
:root {
	--calendar-height: 800px;
}
</style>