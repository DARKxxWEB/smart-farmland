<script setup lang="ts">
import { ref } from "vue";
import { Link, router } from "@inertiajs/vue3";
import {
  Bell,
  ChevronLeft,
  CircleHelp,
  Leaf,
  LayoutDashboard,
  LogOut,
  Menu,
  Settings,
  Sprout,
  Thermometer,
  X,
} from "@lucide/vue";
import { endSession } from "../shared/api";
import FarmAssistant from "../components/FarmAssistant.vue";

const isMenuOpen = ref(false);
const isLoggingOut = ref(false);

const navigation = [
  { label: "نمای کلی", href: "/dashboard", icon: LayoutDashboard },
  { label: "حسگرها", href: "/sensors", icon: Sprout },
  { label: "داده‌های مزرعه", href: "/readings", icon: Thermometer },
  { label: "گزارش‌ها", href: "/reports", icon: Bell },
  { label: "تنظیمات", href: "/settings", icon: Settings },
];

function isCurrent(href: string): boolean {
  const path = window.location.pathname;
  return href === "/dashboard" ? path === "/" || path === href : path.startsWith(href);
}

async function logout(): Promise<void> {
  isLoggingOut.value = true;
  let logoutWarning = false;
  try {
    await endSession();
  } catch {
    logoutWarning = true;
  }
  router.visit(logoutWarning ? "/login?logoutWarning=1" : "/login", { replace: true });
}
</script>

<template>
  <div class="min-h-screen bg-paper text-ink lg:flex">
    <div
      v-if="isMenuOpen"
      class="fixed inset-0 z-40 bg-ink/40 backdrop-blur-sm lg:hidden"
      @click="isMenuOpen = false"
    />

    <aside
      class="fixed inset-y-0 right-0 z-50 flex w-[280px] flex-col border-l border-line bg-white px-5 py-6 transition-transform duration-200 lg:static lg:z-auto lg:min-h-screen lg:translate-x-0"
      :class="isMenuOpen ? 'translate-x-0' : 'translate-x-full lg:translate-x-0'"
    >
      <div class="flex items-center justify-between px-1">
        <Link href="/dashboard" class="flex items-center gap-3" @click="isMenuOpen = false">
          <span class="grid h-11 w-11 place-items-center rounded-2xl bg-forest text-white shadow-lg shadow-forest/15">
            <Leaf :size="22" />
          </span>
          <span>
            <span class="block text-base font-bold">هوشمند مزرعه</span>
            <span class="mt-0.5 block text-[11px] text-slate-400">مدیریت یکپارچه مزرعه</span>
          </span>
        </Link>
        <button
          class="grid h-9 w-9 place-items-center rounded-xl text-slate-400 hover:bg-paper lg:hidden"
          aria-label="بستن منو"
          @click="isMenuOpen = false"
        >
          <X :size="19" />
        </button>
      </div>

      <div class="mt-10 px-3 text-[11px] font-semibold tracking-wide text-slate-400">مدیریت مزرعه</div>
      <nav class="mt-3 space-y-1.5">
        <Link
          v-for="item in navigation"
          :key="item.href"
          :href="item.href"
          class="group flex items-center gap-3 rounded-xl px-3.5 py-3 text-[13px] font-medium transition"
          :class="isCurrent(item.href) ? 'bg-forest text-white shadow-md shadow-forest/15' : 'text-slate-500 hover:bg-paper hover:text-ink'"
          @click="isMenuOpen = false"
        >
          <component :is="item.icon" :size="18" :stroke-width="1.8" />
          <span>{{ item.label }}</span>
          <ChevronLeft v-if="isCurrent(item.href)" class="mr-auto" :size="15" />
        </Link>
      </nav>

      <div class="mt-auto">
        <div class="rounded-2xl bg-paper p-4">
          <div class="flex items-center gap-2 text-forest">
            <CircleHelp :size="17" />
            <span class="text-xs font-semibold">همیشه در دسترس شما</span>
          </div>
          <p class="mt-2 text-[11px] leading-6 text-slate-500">
            وضعیت مزرعه را از همین پنل دنبال کنید و تصمیم‌های بهتر بگیرید.
          </p>
        </div>
        <button
          class="mt-4 flex w-full items-center gap-3 rounded-xl px-3.5 py-3 text-[13px] text-slate-500 transition hover:bg-red-50 hover:text-red-600"
          :disabled="isLoggingOut"
          @click="logout"
        >
          <LogOut :size="18" />
          {{ isLoggingOut ? "در حال خروج..." : "خروج از حساب" }}
        </button>
      </div>
    </aside>

    <main class="min-w-0 flex-1">
      <header class="sticky top-0 z-30 flex h-[76px] items-center justify-between border-b border-line/80 bg-paper/90 px-4 backdrop-blur-md sm:px-7 lg:px-10">
        <div class="flex items-center gap-3">
          <button
            class="grid h-10 w-10 place-items-center rounded-xl border border-line bg-white text-ink lg:hidden"
            aria-label="بازکردن منو"
            @click="isMenuOpen = true"
          >
            <Menu :size="20" />
          </button>
          <div class="hidden items-center gap-2 text-xs text-slate-400 sm:flex">
            <span>پنل مدیریت</span>
            <span>/</span>
            <span class="font-medium text-ink">{{ navigation.find((item) => isCurrent(item.href))?.label ?? "مزرعه" }}</span>
          </div>
          <span class="font-semibold sm:hidden">هوشمند مزرعه</span>
        </div>
        <div class="flex items-center gap-2.5 sm:gap-4">
          <div class="hidden items-center gap-2 rounded-full border border-line bg-white px-3 py-2 text-[11px] text-slate-500 sm:flex">
            <span class="h-2 w-2 rounded-full bg-emerald-500" />
            پنل فعال است
          </div>
          <div class="grid h-10 w-10 place-items-center rounded-full bg-[#e8efe4] text-forest">
            <Sprout :size="19" />
          </div>
        </div>
      </header>
      <div class="mx-auto w-full max-w-[1500px] px-4 py-6 sm:px-7 sm:py-8 lg:px-10">
        <slot />
      </div>
    </main>
    <FarmAssistant />
  </div>
</template>
