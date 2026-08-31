/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#0B0D12",
        cardPrimary: "#151821",
        cardSecondary: "#1A1D24",
        cardElevated: "#1f2330",
        borderDark: "#272B36",
        borderLight: "#343A4A",
        accentAmber: "#F5A623",
        accentAmberHover: "#E0951C",
        infoBlue: "#3B82F6",
        riskCritical: "#EF4444",
        riskHigh: "#F97316",
        riskMed: "#F59E0B",
        riskLow: "#10B981",
      },
      borderRadius: {
        '2xl': '16px',
        '3xl': '20px',
      },
    },
  },
  plugins: [],
}
