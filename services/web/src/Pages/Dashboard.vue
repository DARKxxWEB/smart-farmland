<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { Link, router } from "@inertiajs/vue3";
import { ArrowDownLeft, ArrowUpLeft, Droplets, Leaf, RefreshCw, Sprout, Thermometer, TriangleAlert } from "@lucide/vue";
import AppShell from "../layouts/AppShell.vue";
import { apiGet, hasSession } from "../shared/api";
import type { DashboardSummary, FarmAlert, TrendResponse } from "../features/dashboard/types";

defineOptions({ layout: AppShell });

const summary = ref<DashboardSummary | null>(null);
const trends = ref<TrendResponse | null>(null);
const alerts = ref<FarmAlert[]>([]);
const errors = ref<string[]>([]);
const isLoading = ref(true);

const chartValues = computed(() => {
  const points = trends.value?.series.flatMap((series) => series.points) ?? [];
  if (points.length < 2) return "";
  const values = points.map((point) => point.avg);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  return values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * 100;
      const y = 90 - ((value - min) / range) * 74;
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");
});

function formatNumber(value: number | undefined): string {
  return value === undefined ? "—" : new Intl.NumberFormat("fa-IR").format(value);
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("fa-IR", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

async function loadDashboard(): Promise<void> {
  if (!hasSession()) {
    router.visit("/login", { replace: true });
    return;
  }
  isLoading.value = true;
  errors.value = [];
  const [summaryResult, trendsResult, alertsResult] = await Promise.allSettled([
    apiGet<DashboardSummary>("/bi/summary"),
    apiGet<TrendResponse>("/bi/trends?interval=hour"),
    apiGet<{ items: FarmAlert[] }>("/bi/alerts"),
  ]);
  if (summaryResult.status === "fulfilled") summary.value = summaryResult.value;
  else errors.value.push("دریافت خلاصه مزرعه ناموفق بود.");
  if (trendsResult.status === "fulfilled") trends.value = trendsResult.value;
  else errors.value.push("دریافت روند داده‌ها ناموفق بود.");
  if (alertsResult.status === "fulfilled") alerts.value = alertsResult.value.items;
  else errors.value.push("دریافت هشدارها ناموفق بود.");
  isLoading.value = false;
}

onMounted(loadDashboard);
</script>

<template>
  <div class="space-y-6 sm:space-y-7">
    <section class="relative overflow-hidden rounded-[26px] bg-forest px-5 py-7 text-white shadow-card sm:px-8 sm:py-8 lg:px-10">
      <div class="absolute -left-10 -top-20 h-64 w-64 rounded-full border border-white/10" />
      <div class="absolute -left-5 -top-14 h-48 w-48 rounded-full border border-white/10" />
      <div class="relative flex flex-col justify-between gap-6 sm:flex-row sm:items-center">
        <div>
          <span class="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-[11px] text-emerald-50">
            <span class="h-1.5 w-1.5 rounded-full bg-[#b9d6a4]" /> نمای زنده مزرعه
          </span>
          <h1 class="mt-4 text-2xl font-bold sm:text-[28px]">سلام، مزرعه‌ات چه خبر؟</h1>
          <p class="mt-2 text-xs leading-6 text-white/65 sm:text-sm">وضعیت امروز را یک‌جا ببین و با خیال راحت برای رشد بهتر برنامه‌ریزی کن.</p>
        </div>
        <button
          class="inline-flex h-10 items-center justify-center gap-2 self-start rounded-xl border border-white/15 bg-white/10 px-4 text-xs font-medium transition hover:bg-white/15 sm:self-auto"
          :disabled="isLoading"
          @click="loadDashboard"
        >
          <RefreshCw :size="15" :class="isLoading ? 'animate-spin' : ''" />
          به‌روزرسانی
        </button>
      </div>
    </section>

    <div v-if="errors.length" role="alert" class="space-y-1 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-6 text-amber-900">
      <p v-for="error in errors" :key="error">{{ error }} ارتباط سرویس را بررسی کنید.</p>
    </div>

    <section class="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
      <article class="rounded-2xl border border-line bg-white p-4 shadow-card sm:p-5">
        <div class="flex items-center justify-between">
          <span class="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-forest"><Sprout :size="19" /></span>
          <span class="text-[10px] text-slate-400">در کل مزرعه</span>
        </div>
        <p class="mt-4 text-2xl font-bold">{{ formatNumber(summary?.sensor_count) }}</p>
        <p class="mt-1 text-[11px] text-slate-500">حسگر فعال</p>
      </article>
      <article class="rounded-2xl border border-line bg-white p-4 shadow-card sm:p-5">
        <div class="flex items-center justify-between">
          <span class="grid h-10 w-10 place-items-center rounded-xl bg-sky-50 text-sky-700"><Droplets :size="19" /></span>
          <span class="text-[10px] text-slate-400">از ابتدای ثبت</span>
        </div>
        <p class="mt-4 text-2xl font-bold">{{ formatNumber(summary?.reading_count) }}</p>
        <p class="mt-1 text-[11px] text-slate-500">داده ثبت‌شده</p>
      </article>
      <article class="rounded-2xl border border-line bg-white p-4 shadow-card sm:p-5">
        <div class="flex items-center justify-between">
          <span class="grid h-10 w-10 place-items-center rounded-xl bg-orange-50 text-orange-600"><TriangleAlert :size="19" /></span>
          <span class="text-[10px] text-slate-400">نیازمند بررسی</span>
        </div>
        <p class="mt-4 text-2xl font-bold">{{ formatNumber(summary?.alert_count) }}</p>
        <p class="mt-1 text-[11px] text-slate-500">هشدار مزرعه</p>
      </article>
      <article class="rounded-2xl border border-line bg-white p-4 shadow-card sm:p-5">
        <div class="flex items-center justify-between">
          <span class="grid h-10 w-10 place-items-center rounded-xl bg-lime-50 text-lime-700"><Leaf :size="19" /></span>
          <span class="text-[10px] text-slate-400">آخرین داده</span>
        </div>
        <p class="mt-4 text-sm font-bold">{{ formatDate(summary?.to_time ?? null) }}</p>
        <p class="mt-1 text-[11px] text-slate-500">به‌روزرسانی مزرعه</p>
      </article>
    </section>

    <section class="grid gap-4 xl:grid-cols-[1.6fr_1fr]">
      <article class="min-w-0 rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
        <div class="flex items-start justify-between gap-3">
          <div>
            <h2 class="text-sm font-bold">روند تغییرات حسگرها</h2>
            <p class="mt-1 text-[11px] text-slate-400">میانگین اندازه‌گیری‌ها در بازه‌های زمانی</p>
          </div>
          <span class="rounded-lg bg-paper px-2.5 py-1.5 text-[10px] text-slate-500">ساعتی</span>
        </div>
        <div v-if="chartValues" class="mt-5">
          <div class="relative h-44 overflow-hidden rounded-xl bg-[#fafbf8] p-2 sm:h-52">
            <div class="absolute inset-0 flex flex-col justify-between py-4">
              <span v-for="line in 4" :key="line" class="border-t border-dashed border-slate-100" />
            </div>
            <svg class="relative h-full w-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none" aria-label="نمودار تغییرات">
              <defs>
                <linearGradient id="trend-fill" x1="0" x2="0" y1="0" y2="1">
                  <stop offset="0%" stop-color="#5b9d70" stop-opacity="0.22" />
                  <stop offset="100%" stop-color="#5b9d70" stop-opacity="0" />
                </linearGradient>
              </defs>
              <path :d="`${chartValues} L 100 100 L 0 100 Z`" fill="url(#trend-fill)" />
              <path :d="chartValues" fill="none" stroke="#2e7650" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" vector-effect="non-scaling-stroke" />
            </svg>
          </div>
          <div class="mt-3 flex items-center gap-2 text-[10px] text-slate-400">
            <span class="h-2 w-2 rounded-full bg-forest" />
            {{ trends?.series[0]?.metric ?? "اندازه‌گیری" }}
            <span v-if="trends?.series[0]?.unit">{{ trends.series[0].unit }}</span>
          </div>
        </div>
        <div v-else class="mt-5 grid h-44 place-items-center rounded-xl bg-[#fafbf8] px-6 text-center text-xs leading-6 text-slate-400 sm:h-52">
          {{ isLoading ? "در حال دریافت داده‌ها..." : "هنوز داده‌ای برای نمایش روند ثبت نشده است." }}
        </div>
      </article>

      <article class="rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
        <div class="flex items-center justify-between">
          <div>
            <h2 class="text-sm font-bold">آخرین هشدارها</h2>
            <p class="mt-1 text-[11px] text-slate-400">مواردی که نیاز به توجه دارند</p>
          </div>
          <TriangleAlert :size="19" class="text-orange-500" />
        </div>
        <div v-if="alerts.length" class="mt-4 divide-y divide-line">
          <div v-for="alert in alerts.slice(0, 4)" :key="alert.id" class="flex gap-3 py-3 first:pt-0 last:pb-0">
            <span class="mt-1 h-2 w-2 shrink-0 rounded-full" :class="alert.severity === 'high' || alert.severity === 'critical' ? 'bg-red-500' : 'bg-amber-500'" />
            <div class="min-w-0">
              <p class="text-xs font-medium leading-6">{{ alert.message }}</p>
              <p class="mt-1 text-[10px] text-slate-400">{{ alert.sensor_id }} · {{ formatDate(alert.recorded_at) }}</p>
            </div>
          </div>
        </div>
        <div v-else class="mt-5 grid min-h-36 place-items-center rounded-xl bg-[#fafbf8] px-5 text-center">
          <div>
            <span class="mx-auto grid h-10 w-10 place-items-center rounded-full bg-emerald-50 text-forest"><Leaf :size="18" /></span>
            <p class="mt-2 text-xs text-slate-500">{{ isLoading ? "در حال بررسی هشدارها..." : "هشداری برای نمایش وجود ندارد." }}</p>
          </div>
        </div>
        <Link href="/readings" class="mt-4 inline-flex items-center gap-1 text-[11px] font-semibold text-forest hover:underline">
          مشاهده داده‌های مزرعه
          <ArrowDownLeft :size="14" />
        </Link>
      </article>
    </section>

    <section class="rounded-2xl border border-line bg-white p-5 shadow-card sm:p-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-sm font-bold">وضعیت حسگرها</h2>
          <p class="mt-1 text-[11px] text-slate-400">آخرین اندازه‌گیری ثبت‌شده برای هر حسگر</p>
        </div>
        <Link href="/sensors" class="inline-flex items-center gap-1 text-[11px] font-semibold text-forest hover:underline">
          همه حسگرها <ArrowUpLeft :size="14" />
        </Link>
      </div>
      <div v-if="summary?.sensors.length" class="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <div v-for="sensor in summary.sensors.slice(0, 6)" :key="sensor.sensor_id" class="rounded-xl border border-line p-4">
          <div class="flex items-center justify-between gap-2">
            <div class="flex min-w-0 items-center gap-2">
              <span class="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-emerald-50 text-forest"><Thermometer :size="17" /></span>
              <div class="min-w-0">
                <p class="truncate text-xs font-semibold">{{ sensor.sensor_id }}</p>
                <p class="mt-1 truncate text-[10px] text-slate-400">{{ sensor.device_id }}</p>
              </div>
            </div>
            <span class="h-2 w-2 shrink-0 rounded-full bg-emerald-500" />
          </div>
          <div v-if="sensor.metrics[0]" class="mt-4 flex items-end justify-between">
            <span class="text-[10px] text-slate-500">{{ sensor.metrics[0].metric }}</span>
            <span class="text-lg font-bold">{{ formatNumber(sensor.metrics[0].last) }} <small class="text-[10px] font-normal text-slate-400">{{ sensor.metrics[0].unit }}</small></span>
          </div>
          <p class="mt-2 text-[10px] text-slate-400">{{ formatDate(sensor.last_recorded_at) }}</p>
        </div>
      </div>
      <div v-else class="mt-4 rounded-xl bg-[#fafbf8] px-5 py-8 text-center text-xs text-slate-400">
        {{ isLoading ? "در حال بارگذاری حسگرها..." : "هنوز حسگری برای این مزرعه ثبت نشده است." }}
      </div>
    </section>
  </div>
</template>
