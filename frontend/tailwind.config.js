/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        surface: '#F4F1EA',
        'surface-1': '#EBE8E0',
        'surface-2': '#F1EEE7',
        primary: '#0F1E33',
        muted: '#44474D',
        accent: '#10B981',
        'accent-hover': '#0E9E6E',
      },
      fontFamily: {
        hero: ['"Getai Grotesk"', '"Bricolage Grotesque"', 'sans-serif'],
        heading: ['"Bricolage Grotesque"', 'sans-serif'],
        body: ['Pretendard', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'level-2': '0 10px 20px rgba(15, 30, 51, 0.08)',
      },
    },
  },
  plugins: [],
}
