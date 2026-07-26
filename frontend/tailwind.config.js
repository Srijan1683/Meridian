/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Manrope", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["Sora", "Manrope", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      colors: {
        ink: {
          950: "#08070f",
          900: "#0f0d1b",
          850: "#151225",
          800: "#1d1833",
          700: "#2b2448",
        },
        signal: {
          cyan: "var(--accent)",
          green: "var(--success)",
          amber: "var(--soft-accent)",
          rose: "var(--danger)",
        },
      },
      boxShadow: {
        glow: "0 0 34px var(--glow)",
        panel: "0 24px 80px rgba(0, 0, 0, 0.38)",
      },
    },
  },
  plugins: [],
};
