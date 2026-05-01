/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        surface: '#111111',
        border: '#1f1f1f',
        green: {
          DEFAULT: '#00d4aa',
          500: '#00d4aa',
          400: '#00e8bb',
          600: '#00b894',
        },
        red: {
          DEFAULT: '#ff4757',
          500: '#ff4757',
          400: '#ff6b78',
          600: '#e63946',
        },
        yellow: {
          DEFAULT: '#ffa502',
          500: '#ffa502',
          400: '#ffb830',
        },
        blue: {
          DEFAULT: '#1e90ff',
          500: '#1e90ff',
          400: '#4dabff',
          600: '#0070e0',
        },
        'text-primary': '#f0f0f0',
        'text-secondary': '#888888',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
};
