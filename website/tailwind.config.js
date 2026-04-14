/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // User's color scheme
        bg: '#2e2e2e',
        comment: '#797979',
        white: '#d6d6d6',
        yellow: '#e5b567',
        green: '#b4d273',
        orange: '#e87d3e',
        purple: '#9e86c8',
        pink: '#b05279',
        blue: '#6c99bb',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
