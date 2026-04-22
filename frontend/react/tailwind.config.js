/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        agri: {
          moss: "#2D6A4F",
          leaf: "#40916C",
          clay: "#B5651D",
          night: "#1B1B1B"
        }
      }
    }
  },
  plugins: []
};
