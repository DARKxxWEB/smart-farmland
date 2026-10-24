<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { Bot, ChevronDown, LoaderCircle, Send, Sparkles, Trash2 } from "@lucide/vue";
import { apiPost, hasSession } from "../shared/api";
import type { AssistantReply, AssistantTurn } from "../features/dashboard/types";

const isOpen = ref(false);
const isSending = ref(false);
const draft = ref("");
const error = ref("");
const conversation = ref<AssistantTurn[]>([]);
const thread = ref<HTMLElement | null>(null);

const canSend = computed(() => draft.value.trim().length > 0 && !isSending.value);

watch([conversation, error], async () => {
  await nextTick();
  thread.value?.scrollTo({ top: thread.value.scrollHeight, behavior: "smooth" });
}, { deep: true });

async function sendMessage(): Promise<void> {
  const message = draft.value.trim();
  if (!message || isSending.value) return;
  if (!hasSession()) {
    error.value = "برای گفت‌وگو ابتدا وارد حساب شوید.";
    return;
  }

  error.value = "";
  draft.value = "";
  conversation.value.push({ role: "user", content: message });
  isSending.value = true;

  try {
    const history = conversation.value.slice(0, -1).slice(-8).map(({ role, content }) => ({ role, content }));
    const reply = await apiPost<AssistantReply>("/bi/assistant/chat", { message, history });
    conversation.value.push({
      role: "assistant",
      content: reply.answer,
      sources: reply.sources,
    });
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "پاسخی دریافت نشد. دوباره تلاش کنید.";
  } finally {
    isSending.value = false;
  }
}
</script>

<template>
  <div class="fixed bottom-4 left-4 z-40 sm:bottom-6 sm:left-6">
    <section
      v-if="isOpen"
      class="mb-3 flex h-[min(620px,78dvh)] w-[min(390px,calc(100vw-2rem))] flex-col overflow-hidden rounded-2xl border border-line bg-white shadow-2xl shadow-ink/15"
      aria-label="گفت‌وگو با دستیار مزرعه"
    >
      <header class="flex items-center gap-3 bg-forest px-4 py-3.5 text-white">
        <span class="grid h-10 w-10 place-items-center rounded-xl bg-white/10"><Bot :size="20" /></span>
        <div class="min-w-0 flex-1">
          <h2 class="text-xs font-bold">دستیار هوشمند مزرعه</h2>
          <p class="mt-1 text-[10px] text-white/65">پاسخ بر پایه داده و راهنمای سامانه</p>
        </div>
        <button
          v-if="conversation.length"
          class="grid h-8 w-8 place-items-center rounded-lg text-white/70 hover:bg-white/10 hover:text-white"
          aria-label="پاک‌کردن گفت‌وگو"
          title="پاک‌کردن گفت‌وگو"
          @click="conversation = []; error = ''"
        >
          <Trash2 :size="16" />
        </button>
        <button class="grid h-8 w-8 place-items-center rounded-lg text-white/70 hover:bg-white/10 hover:text-white" aria-label="بستن دستیار" @click="isOpen = false">
          <ChevronDown :size="20" />
        </button>
      </header>

      <div ref="thread" class="min-h-0 flex-1 space-y-4 overflow-y-auto bg-[#fafbf8] px-4 py-4">
        <div v-if="!conversation.length" class="flex min-h-full flex-col justify-center">
          <span class="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-emerald-50 text-forest"><Sparkles :size="22" /></span>
          <p class="mt-3 text-center text-xs font-semibold">چه چیزی درباره مزرعه می‌خواهید بدانید؟</p>
          <div class="mt-5 grid gap-2">
            <button
              v-for="question in ['وضعیت کلی حسگرهای مزرعه چطور است؟', 'هشدارهای فعلی چه معنایی دارند؟', 'روند رطوبت خاک را توضیح بده']"
              :key="question"
              class="rounded-xl border border-line bg-white px-3 py-2.5 text-right text-[11px] leading-5 text-slate-600 transition hover:border-forest/30 hover:text-forest"
              @click="draft = question; sendMessage()"
            >
              {{ question }}
            </button>
          </div>
        </div>

        <article
          v-for="(turn, index) in conversation"
          :key="`${turn.role}-${index}`"
          class="max-w-[92%] rounded-2xl px-3.5 py-3 text-xs leading-6"
          :class="turn.role === 'user' ? 'mr-auto rounded-tr-sm bg-forest text-white' : 'ml-auto rounded-tl-sm border border-line bg-white text-ink'"
        >
          <p class="whitespace-pre-wrap break-words">{{ turn.content }}</p>
          <ul v-if="turn.sources?.length" class="mt-2 space-y-1 border-t border-line pt-2 text-[10px] leading-5 text-slate-400">
            <li v-for="source in turn.sources" :key="source">منبع: {{ source }}</li>
          </ul>
        </article>
        <div v-if="isSending" class="ml-auto flex max-w-[92%] items-center gap-2 rounded-2xl rounded-tl-sm border border-line bg-white px-3.5 py-3 text-[11px] text-slate-500">
          <LoaderCircle :size="15" class="animate-spin text-forest" />
          در حال بررسی داده‌ها و آماده‌سازی پاسخ...
        </div>
        <p v-if="error" role="alert" class="rounded-xl bg-red-50 px-3 py-2.5 text-[11px] leading-5 text-red-700">{{ error }}</p>
      </div>

      <form class="border-t border-line bg-white p-3" @submit.prevent="sendMessage">
        <div class="flex items-end gap-2 rounded-xl border border-line bg-[#fafbf8] p-2 focus-within:border-forest/50">
          <textarea
            v-model="draft"
            rows="1"
            maxlength="1200"
            class="max-h-24 min-h-9 flex-1 resize-y bg-transparent px-1 py-2 text-xs leading-5 outline-none placeholder:text-slate-400"
            placeholder="درباره وضعیت مزرعه بپرسید..."
            aria-label="پیام شما"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <button
            type="submit"
            aria-label="ارسال پیام"
            class="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-forest text-white transition hover:bg-[#174b36] disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="!canSend"
          >
            <Send :size="16" />
          </button>
        </div>
        <p class="mt-2 text-center text-[9px] leading-4 text-slate-400">پاسخ هوش مصنوعی ممکن است خطا داشته باشد؛ برای تصمیم تخصصی با کارشناس مشورت کنید.</p>
      </form>
    </section>

    <button
      class="flex h-12 items-center gap-2 rounded-full bg-forest px-4 text-xs font-semibold text-white shadow-lg shadow-forest/25 transition hover:-translate-y-0.5 hover:bg-[#174b36]"
      :aria-expanded="isOpen"
      aria-label="گفت‌وگو با دستیار هوشمند"
      @click="isOpen = !isOpen"
    >
      <Sparkles :size="17" />
      <span class="hidden sm:inline">دستیار مزرعه</span>
      <span class="sm:hidden">دستیار</span>
    </button>
  </div>
</template>
