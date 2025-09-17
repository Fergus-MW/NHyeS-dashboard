# NHyeS - Capacity Management Dashboard

A Next.js dashboard application for NHS capacity management and attendance prediction, built following NHS design guidelines.

## Features

- **Date Navigator**: Interactive calendar for selecting dates with available data
- **Capacity Visualization**: Animated stacked bar charts showing:
  - Booking Strategy (Projected Attendance, Strategic Overbooking, Safety Margin)  
  - Actual Outcome (Actual Attendance, Wasted Capacity)
- **Safety Margin Slider**: Real-time adjustment of safety margins with instant chart updates
- **NHS Brand Compliance**: Full adherence to NHS color palette, typography, and accessibility guidelines
- **Accessibility**: WCAG 2.1 AA compliant with proper focus states and keyboard navigation

## Design Philosophy

- **Clean & Minimalist**: Data-forward design with generous white space
- **Accessibility First**: Built with screen readers, keyboard navigation, and proper contrast ratios
- **NHS Branding**: Uses official NHS colors and typography guidelines
- **Responsive**: Built with Tailwind CSS and responsive design principles

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm, yarn, pnpm, or bun

### Installation

1. Navigate to the project directory:
   ```bash
   cd frontend/nhyes-dashboard
   ```

2. Install dependencies:
   ```bash
   npm install
   # or
   yarn install
   # or  
   pnpm install
   # or
   bun install
   ```

3. Run the development server:
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   # or
   bun dev
   ```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Technologies Used

- **Next.js 15**: React framework with App Router
- **React 18**: Component library
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first CSS framework
- **Shadcn/ui**: Accessible component library built on Radix UI
- **Framer Motion**: Animation library for smooth transitions
- **Lucide React**: Icon library

## Project Structure

```
src/
├── app/                 # Next.js App Router
│   ├── page.tsx        # Main dashboard page
│   ├── layout.tsx      # Root layout
│   └── globals.css     # Global styles with NHS brand colors
├── components/         
│   ├── ui/             # Reusable UI components (Button, Slider, Card)
│   ├── date-navigator.tsx    # Calendar component
│   └── capacity-visualization.tsx  # Charts and slider component
└── lib/
    └── utils.ts        # Utility functions

```

## NHS Brand Compliance

The application follows the NHS Digital Service Manual guidelines:

- **Colors**: Official NHS blue (#005EB8), system colors for success/error states
- **Typography**: Inter font family with proper hierarchy
- **Accessibility**: WCAG 2.1 AA compliance with proper focus states
- **Layout**: Clean, minimal design with generous whitespace

## Data Visualization

The dashboard displays capacity management data through:

- **Left Pane (35%)**: Date selection calendar with availability indicators
- **Right Pane (65%)**: Two animated stacked bar charts comparing booking strategy vs actual outcomes
- **Interactive Controls**: Safety margin slider that updates charts in real-time

## Accessibility Features

- Keyboard navigation support
- Screen reader compatibility
- High contrast ratios (4.5:1 for text, 3:1 for UI elements)
- Minimum 44px touch targets
- Proper ARIA labels and descriptions
- Focus indicators with NHS amber color

## License

Built for NHS hackathon project.