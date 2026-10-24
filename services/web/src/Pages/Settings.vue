<script setup lang="ts">
import { ref } from "vue";
import { router } from "@inertiajs/vue3";
import { KeyRound, ShieldCheck } from "@lucide/vue";
import AppShell from "../layouts/AppShell.vue";
import { apiPost, clearSession, hasSession } from "../shared/api";

defineOptions({ layout: AppShell });

const oldPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const error = ref("");
const isSaving = ref(false);

async function changePassword(): Promise<void> {
  error.value = "";
  if (newPassword.value !== confirmPassword.value) {
    error.value = "رمز عبور جدید و تکرار آن یکسان نیستند.";
    return;
  }
  if (!hasSession()) {
    router.visit("/login", { replace: true });
    return;
  }
  isSaving.value = true;
  try {
    await apiPost<{ message: string }>("/auth/change-password", {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    });
    clearSession();
    router.visit("/login?passwordChanged=1", { replace: true });
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "تغییر رمز عبور انجام نشد";
  } finally {
    isSaving.value = false;
  }
}
</script>

<template>
  <section class="space-y-5">
    <div>
      <p class="text-xs font-semibold text-forest">حساب کاربری</p>
      <h1 class="mt-2 text-2xl font-bold">تنظیمات</h1>
      <p class="mt-2 text-xs text-slate-500">امنیت حساب خود را مدیریت کنید.</p>
    </div>
    <form class="max-w-2xl rounded-2xl border border-line bg-white p-5 shadow-card sm:p-7" @submit.prevent="changePassword">
      <div class="flex items-center gap-3 border-b border-line pb-5">
        <span class="grid h-10 w-10 place-items-center rounded-xl bg-emerald-50 text-forest"><ShieldCheck :size="20" /></span>
        <div>
          <h2 class="text-sm font-bold">تغییر رمز عبور</h2>
          <p class="mt-1 text-[11px] text-slate-400">برای امنیت بیشتر، رمز عبور قوی انتخاب کنید.</p>
        </div>
      </div>
      <div class="mt-5 grid gap-4 sm:grid-cols-2">
        <label class="block sm:col-span-2">
          <span class="mb-2 block text-xs font-semibold text-slate-600">رمز عبور فعلی</span>
          <span class="flex h-11 items-center gap-2 rounded-xl border border-line px-3 transition focus-within:border-forest">
            <KeyRound :size="16" class="text-slate-400" />
            <input v-model="oldPassword" type="password" autocomplete="current-password" required class="w-full bg-transparent text-xs outline-none" />
          </span>
        </label>
        <label class="block">
          <span class="mb-2 block text-xs font-semibold text-slate-600">رمز عبور جدید</span>
          <input v-model="newPassword" type="password" autocomplete="new-password" minlength="10" pattern="(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).{10,}" required class="h-11 w-full rounded-xl border border-line px-3 text-xs outline-none transition focus:border-forest" />
        </label>
        <label class="block">
          <span class="mb-2 block text-xs font-semibold text-slate-600">تکرار رمز عبور جدید</span>
          <input v-model="confirmPassword" type="password" autocomplete="new-password" minlength="10" pattern="(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9]).{10,}" required class="h-11 w-full rounded-xl border border-line px-3 text-xs outline-none transition focus:border-forest" />
        </label>
      </div>
      <p v-if="error" role="alert" class="mt-4 rounded-xl bg-red-50 px-4 py-3 text-xs text-red-700">{{ error }}</p>
      <button type="submit" class="mt-5 h-11 rounded-xl bg-forest px-5 text-xs font-semibold text-white transition hover:bg-[#174b36] disabled:opacity-60" :disabled="isSaving">
        {{ isSaving ? "در حال ذخیره..." : "ذخیره رمز عبور" }}
      </button>
      <p class="mt-4 text-[10px] leading-6 text-slate-400">رمز جدید باید حداقل ۱۰ کاراکتر و شامل حروف بزرگ، حروف کوچک و عدد باشد. پس از تغییر، برای ادامه دوباره وارد شوید.</p>
    </form>
  </section>
</template>
