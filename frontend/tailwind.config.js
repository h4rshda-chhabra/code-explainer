/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0f1115',
        surface: '#1e2128',
        accent: '#5c67ff',
        textPrimary: '#f0f2f5',
        textSecondary: '#949aab'
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'sans-serif']
      }
    },
  },
  corePlugins: {
    preflight: false,
  },
  plugins: [],
}
