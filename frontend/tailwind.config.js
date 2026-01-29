/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        secondary: '#1e40af',
        accent: '#f59e0b',
        success: '#10b981',
        danger: '#ef4444',
        warning: '#f59e0b',
        light: '#f3f4f6',
        dark: '#1f2937'
      },
      animation: {
        'pulse-ring': 'pulse-ring 2s infinite',
      },
      keyframes: {
        'pulse-ring': {
          '0%': {
            'box-shadow': '0 0 0 0 rgba(37, 99, 235, 0.7)',
          },
          '70%': {
            'box-shadow': '0 0 0 10px rgba(37, 99, 235, 0)',
          },
          '100%': {
            'box-shadow': '0 0 0 0 rgba(37, 99, 235, 0)',
          },
        },
      },
    },
  },
  plugins: [],
};
