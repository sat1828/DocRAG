import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(224 71% 4%)",
        foreground: "hsl(213 31% 91%)",
        primary: {
          DEFAULT: "hsl(187 85% 54%)",
          foreground: "hsl(224 71% 4%)",
        },
        secondary: {
          DEFAULT: "hsl(271 85% 60%)",
          foreground: "hsl(213 31% 91%)",
        },
        muted: {
          DEFAULT: "hsl(223 47% 11%)",
          foreground: "hsl(215.4 16.3% 56.9%)",
        },
        accent: {
          DEFAULT: "hsl(216 34% 17%)",
          foreground: "hsl(210 40% 98%)",
        },
        card: {
          DEFAULT: "hsl(224 71% 4% / 0.5)",
          foreground: "hsl(213 31% 91%)",
        },
        border: "hsl(216 34% 17%)",
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'gradient': 'gradient 8s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': {
            backgroundPosition: '0% 50%',
          },
          '50%': {
            backgroundPosition: '100% 50%',
          },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-20px)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px hsl(187 85% 54% / 0.5)' },
          '50%': { opacity: '.5', boxShadow: '0 0 40px hsl(187 85% 54% / 0.8)' },
        },
      },
    },
  },
  plugins: [],
};

export default config;
