# MavunoSure Web Dashboard

React TypeScript dashboard for Insurance Providers to review claims and generate reports.

## Setup

### Prerequisites
- Node.js 18+ and npm/yarn/pnpm

### Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

2. Set up environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your configuration
```

3. Start development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

The app will be available at http://localhost:5173

## Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
web/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/           # Page components
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API services
│   ├── store/           # State management (Zustand)
│   ├── types/           # TypeScript types
│   ├── utils/           # Utility functions
│   ├── App.tsx
│   └── main.tsx
├── public/
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Tech Stack

- React 18
- TypeScript
- Vite
- TanStack Query (React Query)
- Zustand (State Management)
- React Router
- shadcn/ui (UI Components)
- Tailwind CSS

## Testing

```bash
npm run test
```
