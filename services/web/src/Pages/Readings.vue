<script setup lang="ts">
import { onMounted, ref } from "vue";
import { router } from "@inertiajs/vue3";
import { Activity, Clock3 } from "@lucide/vue";
import AppShell from "../layouts/AppShell.vue";
import { apiGet, hasSession } from "../shared/api";
import type { Reading } from "../features/dashboard/types";

defineOptions({ layout: AppShell });

const readings = ref<Reading[]>([]);
const error = ref("");
const isLoading = ref(true);

onMounted(async () => {
  if (!hasSession()) {
    router.visit("/login", { replace: true });
    return;
  }
  try {
    const result = await apiGet<{ items: Reading[] }>("/telemetry/readings/latest");
    readings.value = result.items;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "دریافت داده‌ها ناموفق بود";
  } finally {
    isLoading.value = false;
  }
});

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}
</script>

<template>
  <section class="space-y-5">
    <div>
      <p class="text-xs font-semibold text-forest">پایش مزرعه</p>
      <h1 class="mt-2 text-2xl font-bold">داده‌های ثبت‌شده</h1>
      <p class="mt-2 text-xs text-slate-500">آخرین اندازه‌گیری هر حسگر را مشاهده کنید.</p>
    </div>
    <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-xs text-red-700">{{ error }}</p>
    <div class="overflow-hidden rounded-2xl border border-line bg-white shadow-card">
      <div class="flex items-center gap-2 border-b border-line px-5 py-4">
        <Activity :size="17" class="text-forest" />
        <h2 class="text-xs font-bold">آخرین قرائت‌ها</h2>
        <span class="mr-auto rounded-full bg-paper px-2.5 py-1 text-[10px] text-slate-500">{{ new Intl.NumberFormat("fa-IR").format(readings.length) }} حسگر</span>
      </div>
      <div v-if="readings.length" class="divide-y divide-line">
        <article v-for="reading in readings" :key="reading.id" class="grid gap-3 px-5 py-4 sm:grid-cols-[1fr_1fr_auto] sm:items-center">
          <div class="min-w-0">
            <p class="truncate text-xs font-semibold">{{ reading.sensor_id }}</p>
            <p class="mt-1 text-[10px] text-slate-400">دستگاه {{ reading.device_id }}</p>
          </div>
          <div class="flex flex-wrap gap-2">
            <span v-for="measurement in reading.measurements" :key="measurement.metric" class="rounded-lg bg-paper px-2.5 py-1.5 text-[10px] text-slate-600">
              {{ measurement.metric }} <b class="text-ink">{{ measurement.value }} {{ measurement.unit }}</b>
            </span>
          </div>
          <p class="flex items-center gap-1.5 text-[10px] text-slate-400"><Clock3 :size="13" /> {{ formatDate(reading.recorded_at) }}</p>
        </article>
      </div>
      <div v-else class="px-5 py-14 text-center text-xs text-slate-400">
        {{ isLoading ? "در حال دریافت داده‌ها..." : "هنوز داده‌ای برای نمایش ثبت نشده است." }}
      </div>
    </div>
  </section>
</template>
