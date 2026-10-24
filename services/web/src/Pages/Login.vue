<script setup lang="ts">
import { ref } from "vue";
import { router } from "@inertiajs/vue3";
import { Leaf, LockKeyhole, UserRound } from "@lucide/vue";
import { apiPost, saveSession, type AuthTokens } from "../shared/api";

const username = ref("");
const password = ref("");
const error = ref("");
const isSubmitting = ref(false);
const passwordChanged = new URLSearchParams(window.location.search).get("passwordChanged") === "1";
const logoutWarning = new URLSearchParams(window.location.search).get("logoutWarning") === "1";

async function submit(): Promise<void> {
  error.value = "";
  isSubmitting.value = true;
  try {
    const tokens = await apiPost<AuthTokens>("/auth/login", {
      username: username.value,
      password: password.value,
    });
    saveSession(tokens);
    router.visit("/dashboard", { replace: true });
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "ورود انجام نشد";
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <main class="relative grid min-h-screen overflow-hidden bg-paper lg:grid-cols-[1.05fr_0.95fr]">
    <div class="pointer-events-none absolute -right-20 -top-20 h-80 w-80 rounded-full bg-[#dfead9] blur-3xl" />
    <section class="relative hidden flex-col justify-between overflow-hidden bg-forest px-12 py-11 text-white lg:flex xl:px-20">
      <div class="absolute -bottom-32 -left-24 h-[440px] w-[440px] rounded-full border border-white/10" />
      <div class="absolute -bottom-16 -left-8 h-[320px] w-[320px] rounded-full border border-white/10" />
      <div class="flex items-center gap-3">
        <span class="grid h-12 w-12 place-items-center rounded-2xl bg-white/10"><Leaf :size="24" /></span>
        <span class="text-lg font-bold">هوشمند مزرعه</span>
      </div>
      <div class="relative max-w-lg">
        <span class="rounded-full bg-white/10 px-3 py-1.5 text-xs text-emerald-100">مدیریت هوشمند، رشد پایدار</span>
        <h1 class="mt-7 text-4xl font-bold leading-[1.7] xl:text-5xl">
          نبض مزرعه‌ات را
          <span class="block text-[#b9d6a4]">همیشه در دست داشته باش.</span>
        </h1>
        <p class="mt-5 max-w-md text-sm leading-8 text-white/65">
          داده‌های حسگرها، وضعیت محصولات و گزارش‌های مزرعه را در یک نگاه دنبال کن.
        </p>
      </div>
      <p class="text-xs text-white/45">پنل اختصاصی مدیریت مزرعه شما</p>
    </section>

    <section class="relative flex items-center justify-center px-5 py-12 sm:px-10">
      <div class="w-full max-w-[420px]">
        <div class="mb-10 flex items-center gap-3 lg:hidden">
          <span class="grid h-11 w-11 place-items-center rounded-2xl bg-forest text-white"><Leaf :size="22" /></span>
          <span class="text-lg font-bold">هوشمند مزرعه</span>
        </div>
        <span class="text-xs font-semibold text-forest">خوش آمدید</span>
        <h2 class="mt-2 text-3xl font-bold">ورود به پنل</h2>
        <p class="mt-3 text-sm leading-7 text-slate-500">برای مشاهده وضعیت مزرعه، اطلاعات حساب خود را وارد کنید.</p>
        <p v-if="passwordChanged" role="status" class="mt-5 rounded-xl bg-emerald-50 px-4 py-3 text-xs leading-6 text-emerald-700">
          رمز عبور با موفقیت تغییر کرد. لطفاً دوباره وارد شوید.
        </p>
        <p v-if="logoutWarning" role="alert" class="mt-5 rounded-xl bg-amber-50 px-4 py-3 text-xs leading-6 text-amber-800">
          نشست این مرورگر پاک شد، اما ارتباط با سرویس خروج ناموفق بود.
        </p>

        <form class="mt-8 space-y-5" @submit.prevent="submit">
          <label class="block">
            <span class="mb-2 block text-xs font-semibold text-slate-600">نام کاربری</span>
            <span class="flex h-12 items-center gap-3 rounded-xl border border-line bg-white px-3.5 transition focus-within:border-forest">
              <UserRound :size="18" class="text-slate-400" />
              <input
                v-model="username"
                autocomplete="username"
                class="w-full bg-transparent text-sm outline-none placeholder:text-slate-300"
                placeholder="نام کاربری خود را وارد کنید"
                required
              />
            </span>
          </label>
          <label class="block">
            <span class="mb-2 block text-xs font-semibold text-slate-600">رمز عبور</span>
            <span class="flex h-12 items-center gap-3 rounded-xl border border-line bg-white px-3.5 transition focus-within:border-forest">
              <LockKeyhole :size="18" class="text-slate-400" />
              <input
                v-model="password"
                type="password"
                autocomplete="current-password"
                class="w-full bg-transparent text-sm outline-none placeholder:text-slate-300"
                placeholder="رمز عبور"
                required
              />
            </span>
          </label>
          <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-4 py-3 text-xs leading-6 text-red-700">{{ error }}</p>
          <button
            type="submit"
            class="flex h-12 w-full items-center justify-center rounded-xl bg-forest text-sm font-semibold text-white transition hover:bg-[#174b36] disabled:cursor-wait disabled:opacity-60"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? "در حال ورود..." : "ورود به حساب" }}
          </button>
        </form>
        <p class="mt-8 text-center text-[11px] leading-6 text-slate-400">دسترسی این پنل فقط برای مدیر مزرعه فعال است.</p>
      </div>
    </section>
  </main>
</template>
