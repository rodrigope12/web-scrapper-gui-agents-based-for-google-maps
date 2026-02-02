/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            fontFamily: {
                sans: ['SF Pro Display', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica', 'Arial', 'sans-serif'],
            },
            colors: {
                // Apple-like System Colors (Dark Mode)
                'apple-gray': {
                    50: '#f9faqb',
                    100: '#f2f2f7',
                    200: '#e5e5ea',
                    300: '#d1d1d6',
                    400: '#c7c7cc',
                    500: '#aeaeb2',
                    600: '#8e8e93',
                    700: '#636366',
                    800: '#48484a',
                    900: '#3a3a3c',
                    950: '#1c1c1e', // System Background
                },
                'apple-blue': '#0A84FF',
                'apple-indigo': '#5E5CE6',
                'apple-purple': '#BF5AF2',
                'apple-pink': '#FF375F',
                'apple-red': '#FF453A',
                'apple-orange': '#FF9F0A',
                'apple-yellow': '#FFD60A',
                'apple-green': '#32D74B',
                'apple-teal': '#64D2FF',
                'sidebar-bg': 'rgba(44, 44, 46, 0.6)',
            },
            boxShadow: {
                'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
                'glow': '0 0 20px rgba(10, 132, 255, 0.3)',
            }
        },
    },
    plugins: [],
}
