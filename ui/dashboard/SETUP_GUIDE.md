# Social Video Publisher Dashboard - Setup Guide

## 🚀 Quick Start

### Prerequisites
- Node.js >= 18.0.0
- npm >= 9.0.0
- Python 3.10+ (für Backend)
- Flask (Backend-Framework)

### Installation

#### 1. **Frontend Setup**

```bash
# Navigate to dashboard directory
cd ui/dashboard

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Das Dashboard läuft dann unter `http://localhost:3000`

#### 2. **Backend API Setup**

Der Backend muss die folgenden Endpoints bereitstellen:

```bash
# From project root
python -m pip install -r requirements.txt
python main.py  # Startet Flask-Server auf Port 5000
```

### Required Backend Endpoints

```
GET    /api/stats              - Dashboard statistics
GET    /api/queue              - Upload queue status
POST   /api/upload             - New upload
DELETE /api/upload/:id         - Cancel upload
GET    /api/platforms          - Platform status
POST   /api/platforms/connect  - Connect platform
GET    /api/analytics          - Analytics data
GET    /api/settings           - App settings
POST   /api/settings           - Save settings
WS     /ws                     - WebSocket for live updates
```

---

## 📦 Project Structure

```
ui/dashboard/
├── components/              # React Komponenten
│   ├── Dashboard.tsx        # Haupt-Dashboard
│   ├── StatsCard.tsx        # Statistik-Karten
│   ├── UploadQueue.tsx      # Upload-Queue-Anzeige
│   ├── DragDropUpload.tsx   # Drag & Drop Upload
│   └── Analytics.tsx        # Analytics Dashboard
├── hooks/                   # Custom React Hooks
│   └── useData.ts           # Daten-Fetching Hooks
├── services/                # API Service Layer
│   └── dashboardService.ts  # API-Kommunikation
├── types/                   # TypeScript Interfaces
│   └── index.ts             # Type Definitions
├── dashboard.css            # Glassmorphism Styling
├── main.tsx                 # App Entry Point
├── index.html               # HTML Template
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript Config
├── vite.config.ts           # Vite Build Config
└── .env.example             # Environment Template
```

---

## 🎨 Design System

### Colors
- **Primary**: `#00d9ff` (Cyan)
- **Secondary**: `#ff006e` (Pink)
- **Accent**: `#8338ec` (Purple)
- **Success**: `#3dd68c` (Green)
- **Error**: `#ff3838` (Red)
- **Warning**: `#ff9500` (Orange)

### Features
- **Glassmorphism**: Blur effects mit transparentem Hintergrund
- **Animations**: Smooth transitions mit CSS Keyframes
- **Responsive**: Mobile-first Design (1 → 2 → 4 Spalten)
- **Dark Mode**: Native Dark Theme mit perfekter Lesbarkeit

### CSS Classes

```typescript
// Glass Cards
.glass-card          // Hauptkomponenten
.glass-button        // CTA-Buttons
.glass-button.secondary  // Sekundär-Buttons

// Status Badges
.badge.success       // ✅ Erfolg
.badge.error         // ❌ Fehler
.badge.warning       // ⚠️ Warnung
.badge.info          // ℹ️ Info

// Animations
.animate-fade-in
.animate-slide-up
.animate-slide-down
.animate-slide-left
.animate-slide-right
.animate-scale-in
.animate-pulse
.animate-glow
.animate-spin
```

---

## 🔧 Configuration

### Environment Variables

```env
# Backend API
VITE_API_BASE_URL=http://localhost:5000/api
VITE_WS_URL=ws://localhost:5000/ws

# Features
VITE_ENABLE_ANALYTICS=true
VITE_ENABLE_REAL_TIME_UPDATES=true
VITE_ENABLE_OFFLINE_MODE=false
```

---

## 📝 Development

### Available Scripts

```bash
# Start development server mit Hot Reload
npm run dev

# Build für Production
npm run build

# Preview Production Build
npm run preview

# Type Check
npm run type-check

# Linting
npm run lint

# Format Code
npm run format
```

### Development Workflow

1. **Komponenten entwickeln**: `src/components/`
2. **Type-Safety**: TypeScript mit striktem Mode
3. **Styling**: CSS-Variablen + Tailwind-ähnliche Klassen
4. **API Integration**: Services über `dashboardService`
5. **Testing**: Unit Tests mit React Testing Library (TODO)

---

## 🌐 API Integration

### Service Functions

```typescript
import { dashboardService } from '../services/dashboardService';

// Stats abrufen
const stats = await dashboardService.getStats();

// Upload Queue
const queue = await dashboardService.getUploadQueue();

// File hochladen
const job = await dashboardService.uploadFile(file, title, description, platforms);

// Upload abbrechen
await dashboardService.cancelUpload(jobId);

// Analytics
const analytics = await dashboardService.getAnalytics();

// WebSocket Live Updates
dashboardService.connectWebSocket((data) => {
  console.log('Live update:', data);
});
```

### Custom Hooks

```typescript
import { useDashboardStats, useUploadQueue, usePlatformStatus } from '../hooks/useData';

// Dashboard Stats (30s polling)
const { stats, loading, error, refetch } = useDashboardStats();

// Upload Queue (10s polling)
const { jobs, loading, error, refetch } = useUploadQueue();

// Platform Status (60s polling)
const { platforms, loading, error } = usePlatformStatus();
```

---

## 📱 Responsive Breakpoints

```css
Desktop:  >= 1024px (4 Spalten)
Tablet:   768px - 1024px (2 Spalten)
Mobile:   < 480px (1 Spalte)
```

---

## 🚀 Production Deployment

### Build Process

```bash
npm run build
# Output: dist/ folder with optimized assets
```

### Docker Deployment

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

### Environment for Production

```env
VITE_API_BASE_URL=https://api.yourdomain.com/api
VITE_WS_URL=wss://api.yourdomain.com/ws
VITE_ENABLE_ANALYTICS=true
```

---

## 🐛 Troubleshooting

### Port 3000 bereits in Verwendung
```bash
# Mit anderem Port starten
npm run dev -- --port 3001
```

### Module nicht gefunden
```bash
# Abhängigkeiten neu installieren
rm -rf node_modules package-lock.json
npm install
```

### WebSocket-Verbindung fehlgeschlagen
- Backend muss auf Port 5000 laufen
- Proxy muss in `vite.config.ts` konfiguriert sein
- CORS-Headers im Backend überprüfen

### TypeScript-Fehler
```bash
npm run type-check
```

---

## 📚 Dependencies

### Core
- **React 18**: UI Library
- **TypeScript**: Static typing
- **Vite**: Build tool

### UI & Styling
- **lucide-react**: Icons
- **recharts**: Charts & Graphs
- **Custom CSS**: Glassmorphism Design

### State & Data
- **Zustand**: State Management (optional)
- **Axios**: HTTP Client

### Development
- **ESLint**: Code Linting
- **Prettier**: Code Formatting
- **Tailwind CSS**: Utility Classes

---

## 📞 Support & Documentation

### Component Props

#### Dashboard
```typescript
interface DashboardProps {
  onLogout?: () => void;
}
```

#### StatsCard
```typescript
interface StatsCardProps {
  title: string;
  value: number | string;
  trend?: number;
  icon?: string;
  loading?: boolean;
  onClick?: () => void;
}
```

#### DragDropUpload
```typescript
interface DragDropUploadProps {
  onClose: () => void;
  onSuccess?: () => void;
}
```

---

## 🎯 Next Steps

1. **Backend API implementieren** - Flask Endpoints
2. **WebSocket Integration** - Real-time Updates
3. **Error Handling** - Global Error Boundaries
4. **Testing** - Unit & Integration Tests
5. **State Management** - Zustand Setup
6. **Analytics** - Tracking & Monitoring
7. **Deployment** - Docker & CI/CD
8. **Documentation** - API Docs & Storybook

---

## 📄 License

© 2024 Social Video Publisher. All rights reserved.

---

**Viel Spaß beim Entwickeln! 🚀**
