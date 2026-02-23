/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                gray: {
                    750: '#2d333f',
                    850: '#1a1f26',
                }
            }
        },
    },
    plugins: [],
}
