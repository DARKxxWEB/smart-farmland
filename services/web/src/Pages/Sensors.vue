<script setup lang="ts">
import { onMounted, ref } from "vue";
import { router } from "@inertiajs/vue3";
import { Radio, RefreshCw, Sprout } from "@lucide/vue";
import AppShell from "../layouts/AppShell.vue";
import { apiGet, hasSession } from "../shared/api";
import type { Sensor } from "../features/dashboard/types";

defineOptions({ layout: AppShell });

const sensors = ref<Sensor[]>([]);
const error = ref("");
const isLoading = ref(true);

async function loadSensors(): Promise<void> {
  if (!hasSession()) {
    router.visit("/login", { replace: true });
    return;
  }
  isLoading.value = true;
  error.value = "";
  try {
    const result = await apiGet<{ items: Sensor[] }>("/telemetry/sensors");
    sensors.value = result.items;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "دریافت حسگرها ناموفق بود";
  } finally {
    isLoading.value = false;
  }
}

onMounted(loadSensors);
</script>

<template>
  <section class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="text-xs font-semibold text-forest">تجهیزات مزرعه</p>
        <h1 class="mt-2 text-2xl font-bold">حسگرهای شما</h1>
        <p class="mt-2 text-xs text-slate-500">وضعیت حسگرهای ثبت‌شده و آخرین مقادیر اندازه‌گیری‌شده</p>
      </div>
      <button class="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-white px-4 text-xs font-semibold text-slate-600" :disabled="isLoading" @click="loadSensors">
        <RefreshCw :size="15" :class="isLoading ? 'animate-spin' : ''" /> به‌روزرسانی
      </button>
    </div>
    <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-xs text-red-700">{{ error }}</p>
    <div v-if="sensors.length" class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      <article v-for="sensor in sensors" :key="`${sensor.device_id}-${sensor.sensor_id}`" class="rounded-2xl border border-line bg-white p-5 shadow-card">
        <div class="flex items-start justify-between">
          <span class="grid h-11 w-11 place-items-center rounded-xl bg-emerald-50 text-forest"><Radio :size="20" /></span>
          <span class="flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] text-emerald-700"><span class="h-1.5 w-1.5 rounded-full bg-emerald-500" /> متصل</span>
        </div>
        <h2 class="mt-4 text-sm font-bold">{{ sensor.sensor_id }}</h2>
        <p class="mt-1 text-[11px] text-slate-400">دستگاه {{ sensor.device_id }} · {{ sensor.kind }}</p>
        <div class="mt-4 space-y-2 border-t border-line pt-3">
          <div v-for="measurement in sensor.last_measurements" :key="measurement.metric" class="flex items-center justify-between text-xs">
            <span class="text-slate-500">{{ measurement.metric }}</span>
            <span class="font-semibold">{{ measurement.value }} {{ measurement.unit }}</span>
          </div>
          <p v-if="!sensor.last_measurements.length" class="text-[11px] text-slate-400">هنوز اندازه‌گیری‌ای ثبت نشده است.</p>
        </div>
        <p class="mt-4 flex items-center gap-1.5 text-[10px] text-slate-400"><Sprout :size="13" /> آخرین دریافت: {{ sensor.last_recorded_at ? new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(sensor.last_recorded_at)) : "بدون داده" }}</p>
      </article>
    </div>
    <div v-else-if="!isLoading && !error" class="rounded-2xl border border-dashed border-line bg-white px-6 py-16 text-center">
      <span class="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-emerald-50 text-forest"><Sprout :size="22" /></span>
      <p class="mt-4 text-sm font-semibold">هنوز حسگری ثبت نشده است</p>
      <p class="mt-2 text-xs text-slate-400">با دریافت اولین داده از دستگاه، حسگر در این صفحه نمایش داده می‌شود.</p>
    </div>
    <div v-else-if="isLoading" class="rounded-2xl bg-white py-16 text-center text-xs text-slate-400">در حال دریافت فهرست حسگرها...</div>
  </section>
</template>
