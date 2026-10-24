<script setup lang="ts">
import { onMounted, ref } from "vue";
import { router } from "@inertiajs/vue3";
import { CalendarDays, FileText } from "@lucide/vue";
import AppShell from "../layouts/AppShell.vue";
import { apiGet, hasSession } from "../shared/api";
import type { Report } from "../features/dashboard/types";

defineOptions({ layout: AppShell });

const reports = ref<Report[]>([]);
const error = ref("");
const isLoading = ref(true);

onMounted(async () => {
  if (!hasSession()) {
    router.visit("/login", { replace: true });
    return;
  }
  try {
    const result = await apiGet<{ items: Report[] }>("/bi/reports");
    reports.value = result.items;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "دریافت گزارش‌ها ناموفق بود";
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
      <p class="text-xs font-semibold text-forest">تحلیل و گزارش</p>
      <h1 class="mt-2 text-2xl font-bold">گزارش‌های مزرعه</h1>
      <p class="mt-2 text-xs text-slate-500">گزارش‌های تولیدشده از داده‌های ثبت‌شده در مزرعه</p>
    </div>
    <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-xs text-red-700">{{ error }}</p>
    <div v-if="reports.length" class="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      <article v-for="report in reports" :key="report.id" class="rounded-2xl border border-line bg-white p-5 shadow-card">
        <span class="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-forest"><FileText :size="18" /></span>
        <h2 class="mt-4 text-sm font-bold">{{ report.title }}</h2>
        <p class="mt-2 flex items-center gap-1.5 text-[11px] text-slate-400"><CalendarDays :size="14" /> {{ formatDate(report.generated_at) }}</p>
        <p class="mt-4 border-t border-line pt-3 text-[10px] text-slate-500">تهیه‌شده توسط {{ report.generated_by || "مدیر مزرعه" }}</p>
      </article>
    </div>
    <div v-else class="rounded-2xl border border-dashed border-line bg-white px-6 py-16 text-center">
      <span class="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-emerald-50 text-forest"><FileText :size="22" /></span>
      <p class="mt-4 text-sm font-semibold">{{ isLoading ? "در حال بارگذاری گزارش‌ها..." : "هنوز گزارشی ثبت نشده است" }}</p>
      <p v-if="!isLoading" class="mt-2 text-xs text-slate-400">پس از ایجاد گزارش، نتیجه در این صفحه نمایش داده می‌شود.</p>
    </div>
  </section>
</template>
