# Patch Priority Framework - Frontend

A React-based frontend application for the Patch Priority Framework, a game-theoretic approach to vulnerability patching prioritization.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Router DOM** for routing
- **Zustand** for state management
- **React Query** for data fetching
- **Axios** for API communication
- **Lucide React** for icons

## Prerequisites

- Node.js 18+ and npm

## Setup Instructions

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

   The application will be available at `http://localhost:5173`

3. **Ensure the backend is running:**

   The frontend expects the backend API to be running at `http://localhost:8000`. Make sure to start the FastAPI backend before using the frontend.

   ```bash
   # In the project root directory
   cd web_api
   uvicorn main:app --reload
   ```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
frontend/
├── public/          # Static assets
├── src/
│   ├── components/  # Reusable React components
│   ├── pages/       # Page components
│   ├── services/    # API client and services
│   ├── stores/      # Zustand state stores
│   ├── types/       # TypeScript type definitions
│   ├── App.tsx      # Main application component
│   ├── main.tsx     # Application entry point
│   └── index.css    # Global styles with Tailwind
├── index.html       # HTML template
├── package.json     # Dependencies and scripts
├── vite.config.ts   # Vite configuration
├── tailwind.config.js  # Tailwind CSS configuration
└── tsconfig.json    # TypeScript configuration
```

## Features

- **Authentication:** Login and registration with JWT tokens
- **Dashboard:** Overview of systems, simulations, and vulnerabilities
- **Protected Routes:** Role-based access control
- **Admin Panel:** Platform statistics and user management (admin only)
- **Responsive Design:** Mobile-friendly interface

## API Integration

The frontend communicates with the backend API through Axios. The API client is configured with:

- Base URL: `/api` (proxied to `http://localhost:8000/api` in development)
- JWT authentication via `Authorization` header
- Automatic token refresh and error handling

## Environment Variables

No environment variables are required for development. The Vite configuration handles API proxying automatically.

## Building for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

## Browser Support

Modern browsers with ES2020 support:
- Chrome/Edge 80+
- Firefox 72+
- Safari 13.1+
