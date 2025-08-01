import tailwindcss from "@tailwindcss/vite";

/**
 * Tailwind v4 config: colors are now managed via CSS variables in index.css using @theme and :root.
 * Use the new plugin for Vite integration.
 */
export default {
  plugins: [tailwindcss()],
  theme: {
    extend: {
      // Animations and other extensions can remain here if needed
      colors: {
        "ctan-gold": "var(--ctan-gold)",
        "ctan-amber": "var(--ctan-amber)",
        "ctan-orange": "var(--ctan-orange)",
        "ctan-warm-yellow": "var(--ctan-warm-yellow)",
        "ctan-card": "var(--ctan-card)",
      },
      text: {
        "ctan-gold": "var(--ctan-gold)",
        "ctan-amber": "var(--ctan-amber)",
        "ctan-orange": "var(--ctan-orange)",
        "ctan-warm-yellow": "var(--ctan-warm-yellow)",
        "ctan-text-secondary": "var(--ctan-text-secondary)",
        "ctan-text-muted": "var(--ctan-text-muted)",
      },
      animation: {
        "gradient-shift": "gradient-shift 4s ease infinite",
        "icon-glow": "icon-glow 3s ease-in-out infinite",
        "loading-sweep": "loading-sweep 1.5s ease-in-out infinite",
      },
    },
  },
};
