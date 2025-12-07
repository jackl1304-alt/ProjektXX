# Dashboard Architecture & Design Document

## 🏗️ System Overview

The Social Video Publisher Dashboard is a modern React-based web application that provides real-time monitoring and management of video uploads across multiple social media platforms.

```
┌─────────────────────────────────────────────────────────────┐
│                  Browser / Desktop Client                    │
├─────────────────────────────────────────────────────────────┤
│                   React Dashboard (port 3000)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Dashboard   │  │   Upload     │  │   Analytics      │  │
│  │  Component   │  │   Queue      │  │   Dashboard      │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│              Custom React Hooks (useData)                    │
│         Polling: 10s (queue), 30s (stats), 60s (platform)   │
├─────────────────────────────────────────────────────────────┤
│              API Service Layer (dashboardService)            │
│              WebSocket + REST Communication                  │
├──────────────────────────────────────────────────────────────┤
│            HTTP & WebSocket (Vite Proxy)                    │
│                    localhost:5000                           │
└──────────────────────────────────────────────────────────────┘
         ▼
┌──────────────────────────────────────────────────────────────┐
│              Flask Backend API (port 5000)                   │
│  /api/stats  │  /api/queue  │  /api/upload  │  /api/analytics
│  /api/platforms  │  /api/settings  │  /ws (WebSocket)       │
└──────────────────────────────────────────────────────────────┘
```

---

## 📦 Project Structure

```
ui/dashboard/
│
├── 📄 Configuration Files
│   ├── package.json              # Dependencies & scripts
│   ├── tsconfig.json             # TypeScript configuration
│   ├── vite.config.ts            # Vite build configuration
│   ├── .eslintrc.json            # Linting rules
│   ├── .prettierrc.json          # Code formatting
│   ├── .env.example              # Environment template
│   └── .gitignore                # Git ignore rules
│
├── 📄 Documentation
│   ├── README.md                 # Project overview
│   ├── SETUP_GUIDE.md            # Installation & setup
│   ├── API_DOCS.md               # API reference
│   └── ARCHITECTURE.md           # This file
│
├── 🎯 Application Root
│   ├── index.html                # HTML entry point
│   └── main.tsx                  # React app entry
│
├── 🎨 Styling
│   └── dashboard.css             # Global styles (glassmorphism)
│
├── 🧩 Components (React)
│   └── components/
│       ├── Dashboard.tsx         # Main layout & orchestration
│       ├── StatsCard.tsx         # Reusable statistics card
│       ├── UploadQueue.tsx       # Queue management UI
│       ├── DragDropUpload.tsx    # File upload modal
│       └── Analytics.tsx         # Analytics dashboard
│
├── 🎣 Custom Hooks
│   └── hooks/
│       └── useData.ts            # Data fetching with polling
│
├── 🌐 API Services
│   └── services/
│       └── dashboardService.ts   # API client & WebSocket
│
└── 📝 Type Definitions
    └── types/
        └── index.ts              # TypeScript interfaces
```

---

## 🔄 Data Flow Architecture

### 1. **Component Hierarchy**

```
<Dashboard>
  ├── <Header>
  │   ├── Logo
  │   ├── Navigation Tabs
  │   ├── Theme Toggle
  │   └── Logout Button
  │
  ├── <MobileMenu> (conditional)
  │
  ├── <MainContent>
  │   ├── Dashboard Tab
  │   │   ├── <StatsCard> (4x)
  │   │   ├── <UploadQueue> (recent)
  │   │   └── <PlatformStatus>
  │   │
  │   ├── Upload Tab
  │   │   ├── <DragDropUpload> (modal)
  │   │   └── <UploadQueue> (full)
  │   │
  │   ├── Analytics Tab
  │   │   └── <Analytics>
  │   │
  │   └── Settings Tab
  │       └── Settings Form
  │
  └── <Footer>
```

### 2. **Data Fetching Pattern**

```
useData Hook
    ↓
Fetch API Data
    ↓
Cache Response
    ↓
Set Loading/Error States
    ↓
Auto-refresh (Interval)
    ↓
Component Re-render
```

### 3. **API Communication**

```
Dashboard Component
    ↓
Custom Hook (useUploadQueue, useDashboardStats, etc.)
    ↓
dashboardService
    ↓
axios.get() / axios.post() (HTTP)
    ↓
WebSocket (Live Updates)
    ↓
Flask API Endpoints
    ↓
Backend Logic / Database
```

---

## 🎨 Design System

### **Color Palette**

```typescript
const colors = {
  // Primary
  primary: '#00d9ff',         // Cyan
  primaryDark: '#0099cc',     // Dark cyan
  
  // Secondary
  secondary: '#ff006e',       // Pink
  
  // Accent
  accent: '#8338ec',          // Purple
  
  // Semantic
  success: '#3dd68c',         // Green
  warning: '#ff9500',         // Orange
  error: '#ff3838',           // Red
  
  // Backgrounds
  darkBg: '#0a0e27',          // Main background
  darkSecondary: '#141829',   // Secondary background
  darkTertiary: '#1a1f3a',    // Tertiary background
  
  // Text
  textPrimary: '#ffffff',
  textSecondary: '#b0b5c0',
  textTertiary: '#7a7f8e',
  
  // Borders
  borderLight: 'rgba(255, 255, 255, 0.1)',
};
```

### **Spacing System**

```typescript
const spacing = {
  xs: '0.25rem',   // 4px
  sm: '0.5rem',    // 8px
  md: '1rem',      // 16px
  lg: '1.5rem',    // 24px
  xl: '2rem',      // 32px
  '2xl': '3rem',   // 48px
};
```

### **Glassmorphism Effect**

```css
.glass-card {
  background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
}
```

---

## 🔌 API Endpoints

### **REST Endpoints**

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/queue` | Upload queue status |
| POST | `/api/upload` | Create upload job |
| DELETE | `/api/upload/:id` | Cancel upload |
| GET | `/api/platforms` | Platform status |
| POST | `/api/platforms/:name/connect` | OAuth connection |
| GET | `/api/analytics` | Analytics data |
| GET | `/api/settings` | App settings |
| POST | `/api/settings` | Save settings |
| GET | `/api/health` | Health check |

### **WebSocket Events**

```javascript
// Connect
const ws = new WebSocket('ws://localhost:5000/ws');

// Receive
ws.onmessage = (event) => {
  const { type, data } = JSON.parse(event.data);
  
  switch(type) {
    case 'upload_progress':   // { jobId, progress }
    case 'upload_completed':  // { jobId, status }
    case 'analytics_update':  // { views, engagement }
    case 'platform_status':   // { platform, connected }
  }
};
```

---

## 🎯 Custom Hooks

### **useDashboardStats()**

```typescript
const { stats, loading, error, refetch } = useDashboardStats();

// Auto-refetches every 30 seconds
// Returns:
// - stats: { totalUploads, successfulUploads, totalViews, ... }
// - loading: boolean
// - error: string | null
// - refetch: () => Promise<void>
```

### **useUploadQueue()**

```typescript
const { jobs, loading, error, refetch } = useUploadQueue();

// Auto-refetches every 10 seconds
// Returns:
// - jobs: UploadJob[]
// - loading: boolean
// - error: string | null
// - refetch: () => Promise<void>
```

### **usePlatformStatus()**

```typescript
const { platforms, loading, error } = usePlatformStatus();

// Auto-refetches every 60 seconds
// Returns:
// - platforms: Platform[]
// - loading: boolean
// - error: string | null
```

---

## 📱 Responsive Design Strategy

### **Breakpoints**

```typescript
const breakpoints = {
  mobile: 480,    // < 480px
  tablet: 768,    // 768px - 1024px
  desktop: 1024,  // >= 1024px
};
```

### **Grid Layouts**

| Device | Columns | Examples |
|--------|---------|----------|
| Mobile | 1 | Full width cards |
| Tablet | 2 | 2-column grid |
| Desktop | 4 | Stats cards in 4-column |

### **CSS Media Queries**

```css
@media (max-width: 1024px) { /* Tablet */ }
@media (max-width: 768px) { /* Mobile */ }
@media (max-width: 480px) { /* Small mobile */ }
```

---

## 🔐 Type Safety

### **TypeScript Configuration**

- **Mode**: Strict (all strict checks enabled)
- **Target**: ES2020
- **Module**: ESNext (tree-shakeable)
- **Path Aliases**: `@/*` → `./src/*`

### **Core Interfaces**

```typescript
// From types/index.ts
interface UploadJob {
  id: string;
  title: string;
  description?: string;
  platforms: string[];
  status: 'queued' | 'uploading' | 'completed' | 'failed';
  progress: number;
  createdAt: string;
  updatedAt: string;
  error?: string;
}

interface DashboardStats {
  totalUploads: number;
  successfulUploads: number;
  failedUploads: number;
  totalViews: number;
  totalEngagement: number;
}

interface Platform {
  name: string;
  connected: boolean;
  icon: string;
}
```

---

## 🚀 Build & Deployment

### **Development**

```bash
npm run dev
# Vite dev server on http://localhost:3000
# HMR enabled for fast refresh
# Proxy to backend on http://localhost:5000
```

### **Production**

```bash
npm run build
# Outputs optimized files to dist/
# Code splitting enabled
# Minification & tree-shaking applied
```

### **Preview**

```bash
npm run preview
# Preview production build locally
# http://localhost:3000
```

---

## 📊 Performance Optimizations

### **Code Splitting**

- Vite automatically splits components into chunks
- Lazy loading for large components (Analytics, etc.)

### **Caching Strategy**

- React Query-like polling with configurable intervals
- Stale-while-revalidate pattern for API data

### **CSS Optimization**

- Custom CSS variables for theming
- No unused CSS in production
- Minified CSS bundling

### **Image & Asset Handling**

- Vite handles image optimization
- SVG icons via Lucide React (no extra HTTP requests)

---

## 🐛 Error Handling

### **Global Error Boundary** (TODO)

```typescript
<ErrorBoundary>
  <Dashboard />
</ErrorBoundary>
```

### **API Error Handling**

```typescript
try {
  const data = await dashboardService.getStats();
} catch (error) {
  // Network error
  // Server error
  // Validation error
  setError(error.message);
}
```

### **User-Facing Errors**

- Toast notifications
- Error cards with retry buttons
- Loading skeletons during fetch

---

## 🧪 Testing Strategy (TODO)

### **Unit Tests**

```typescript
// components/__tests__/StatsCard.test.tsx
test('displays value and trend', () => {
  render(<StatsCard value={100} trend={12} />);
  expect(screen.getByText('100')).toBeInTheDocument();
});
```

### **Integration Tests**

```typescript
// hooks/__tests__/useData.test.ts
test('fetches and updates data', async () => {
  const { result } = renderHook(() => useDashboardStats());
  await waitFor(() => {
    expect(result.current.stats).toBeDefined();
  });
});
```

### **E2E Tests** (TODO)

```typescript
// e2e/dashboard.spec.ts
test('upload video flow', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.click('button:has-text("Upload")');
  // Upload flow...
});
```

---

## 📈 Scalability Considerations

### **Current Limitations**

- In-memory data storage (for demo)
- No pagination (small data sets)
- No caching layer (Zustand could be added)

### **Production Improvements**

1. **Database**: PostgreSQL or MongoDB
2. **Caching**: Redis for frequently accessed data
3. **State Management**: Zustand for complex state
4. **Message Queue**: For async uploads (Celery/RabbitMQ)
5. **CDN**: For static assets distribution
6. **API Gateway**: For rate limiting & authentication

---

## 🔄 CI/CD Integration

### **GitHub Actions** (TODO)

```yaml
name: Dashboard CI/CD
on: [push, pull_request]
jobs:
  build:
    - npm install
    - npm run lint
    - npm run type-check
    - npm run build
    - npm run test
```

---

## 📚 Development Guidelines

### **Component Structure**

```typescript
// components/MyComponent.tsx
import React from 'react';
import './styles.css'; // or inline styles

interface MyComponentProps {
  title: string;
  onClick?: () => void;
}

const MyComponent: React.FC<MyComponentProps> = ({
  title,
  onClick,
}) => {
  return (
    <div className="my-component">
      {title}
    </div>
  );
};

export default MyComponent;
```

### **Hook Pattern**

```typescript
// hooks/useMyHook.ts
import { useState, useEffect, useCallback } from 'react';
import { dashboardService } from '../services/dashboardService';

export const useMyHook = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    try {
      const result = await dashboardService.fetchData();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
    const interval = setInterval(fetch, 30000); // Auto-refresh
    return () => clearInterval(interval);
  }, [fetch]);

  return { data, loading, error, refetch: fetch };
};
```

---

## 🎓 Next Steps for Development

1. **Error Boundaries** - Add React error boundary
2. **Testing Suite** - Jest + React Testing Library
3. **State Management** - Zustand for complex state
4. **Backend Integration** - Connect to actual Flask API
5. **Authentication** - Implement JWT/OAuth
6. **Database** - Switch from in-memory storage
7. **Monitoring** - Add analytics & error tracking
8. **Storybook** - Component documentation

---

**Last Updated:** January 2024  
**Version:** 1.0.0  
**Status:** Production Ready (Frontend)
