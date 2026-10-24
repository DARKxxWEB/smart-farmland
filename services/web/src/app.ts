import { createApp, h } from "vue";
import type { DefineComponent } from "vue";
import { createInertiaApp } from "@inertiajs/vue3";
import "./style.css";

const pages = import.meta.glob<{ default: DefineComponent }>("./Pages/**/*.vue");

void createInertiaApp({
  resolve: async (name) => {
    const loadPage = pages[`./Pages/${name}.vue`];
    if (!loadPage) throw new Error(`Inertia page "${name}" was not found`);
    const module = await loadPage();
    return module.default;
  },
  setup({ el, App, props, plugin }) {
    createApp({ render: () => h(App, props) }).use(plugin).mount(el);
  },
  progress: {
    color: "#1d5c43",
    showSpinner: false,
  },
});
