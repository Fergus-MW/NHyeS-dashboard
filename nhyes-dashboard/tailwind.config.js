/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  prefix: "",
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        // NHS Brand Colors
        nhs: {
          blue: "#005EB8",
          "dark-blue": "#003087", 
          white: "#FFFFFF",
          black: "#212B32",
          "light-grey": "#F0F4F5",
          "mid-grey": "#AEB7B3",
        },
        system: {
          green: "#007F3B",
          red: "#DA291C", 
          amber: "#FFB81C",
        },
        // Data Visualization Colors
        data: {
          "projected-blue": "#357ABD",
          "strategic-blue": "#7CB5EC", 
          "success-green": "#5A9C51",
          "neutral-grey": "#EAEAEA",
        },
        primary: {
          DEFAULT: "#005EB8", // NHS Blue
          foreground: "#FFFFFF",
        },
        secondary: {
          DEFAULT: "#F0F4F5", // NHS Light Grey
          foreground: "#212B32", // NHS Black
        },
        destructive: {
          DEFAULT: "#DA291C", // NHS Red
          foreground: "#FFFFFF",
        },
        muted: {
          DEFAULT: "#F0F4F5", // NHS Light Grey
          foreground: "#212B32",
        },
        accent: {
          DEFAULT: "#FFB81C", // NHS Amber
          foreground: "#212B32",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      fontFamily: {
        sans: ["Inter", "Arial", "Helvetica", "sans-serif"],
      },
      fontSize: {
        'page-title': ['32px', { lineHeight: '1.5', fontWeight: '700' }],
        'section-title': ['24px', { lineHeight: '1.5', fontWeight: '700' }], 
        'card-title': ['19px', { lineHeight: '1.5', fontWeight: '700' }],
        'body': ['16px', { lineHeight: '1.5', fontWeight: '400' }],
        'body-small': ['14px', { lineHeight: '1.5', fontWeight: '400' }],
      },
      spacing: {
        // 8-point grid system
        '1': '8px',
        '2': '16px', 
        '3': '24px',
        '4': '32px',
        '5': '40px',
        '6': '48px',
        '8': '64px',
        '10': '80px',
        '12': '96px',
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        "bar-grow": {
          from: { height: "0%" },
          to: { height: "var(--target-height)" },
        },
        "segment-adjust": {
          from: { height: "var(--start-height)" },
          to: { height: "var(--end-height)" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
        "bar-grow": "bar-grow 0.6s ease-out",
        "segment-adjust": "segment-adjust 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
