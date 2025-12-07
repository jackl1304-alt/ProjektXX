# 🎬 Social Video Publisher - React Dashboard

Modern, professional web dashboard for managing video uploads across multiple social media platforms.

![Dashboard Preview](https://via.placeholder.com/800x450?text=Dashboard+Preview)

## ✨ Features

- **Real-time Upload Queue**: Monitor video processing status in real-time
- **Multi-Platform Support**: Upload simultaneously to YouTube, TikTok, Instagram & Twitter
- **Analytics Dashboard**: Track views, engagement & performance metrics
- **Drag & Drop Upload**: Easy file upload with progress tracking
- **Glasmorphism Design**: Modern UI with blur effects & smooth animations
- **Dark Mode**: Premium dark theme optimized for long work sessions
- **Responsive Layout**: Perfect on desktop, tablet & mobile
- **WebSocket Integration**: Live updates without page refresh
- **Type-Safe**: Full TypeScript support with strict type checking

## 🚀 Quick Start

### Prerequisites
- Node.js >= 18.0.0
- npm >= 9.0.0

### Installation

```bash
# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Start development server
npm run dev
```

Dashboard runs at `http://localhost:3000`

### Backend Requirements

Ensure the Flask backend is running on `http://localhost:5000` with these endpoints:

- `GET /api/stats` - Dashboard statistics
- `GET /api/queue` - Upload queue status
- `POST /api/upload` - Create new upload
- `DELETE /api/upload/:id` - Cancel upload
- `GET /api/platforms` - Connected platforms
- `POST /api/platforms/:name/connect` - Platform authentication
- `GET /api/analytics` - Analytics data
- `GET /api/settings` - Application settings
- `POST /api/settings` - Save settings

## 📁 Project Structure

```
ui/dashboard/
├── components/              # React Components
│   ├── Dashboard.tsx        # Main dashboard container
│   ├── StatsCard.tsx        # Statistics card component
│   ├── UploadQueue.tsx      # Upload queue display
│   ├── DragDropUpload.tsx   # File upload modal
│   └── Analytics.tsx        # Analytics dashboard
├── hooks/                   # Custom React Hooks
│   └── useData.ts           # Data fetching hooks
├── services/                # API Service Layer
│   └── dashboardService.ts  # API communication
├── types/                   # TypeScript Interfaces
│   └── index.ts             # Type definitions
├── dashboard.css            # Global styles & glassmorphism
├── main.tsx                 # Application entry point
├── index.html               # HTML template
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
├── package.json             # Dependencies
└── SETUP_GUIDE.md           # Detailed setup guide
```

## 🎨 Design System

### Color Palette
```
Primary:    #00d9ff (Cyan)
Secondary:  #ff006e (Pink)
Accent:     #8338ec (Purple)
Success:    #3dd68c (Green)
Error:      #ff3838 (Red)
Warning:    #ff9500 (Orange)
Dark BG:    #0a0e27
```

### Components
- **glass-card**: Main container with blur effect
- **glass-button**: Primary call-to-action button
- **glass-button.secondary**: Secondary button variant
- **badge**: Status badges (success, error, warning, info)
- **progress-bar**: Animated progress indicator

### Animations
- `fadeIn` - Smooth entrance
- `slideInUp/Down/Left/Right` - Directional slides
- `scaleIn` - Zoom effect
- `pulse` - Pulsing effect
- `glow` - Glowing effect
- `spin` - Rotation animation

## 🔧 Development

### Available Scripts

```bash
# Start dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run type-check

# Linting
npm run lint

# Code formatting
npm run format
```

### Technology Stack

| Package | Purpose |
|---------|---------|
| React 18 | UI Framework |
| TypeScript | Type Safety |
| Vite | Build Tool & Dev Server |
| Lucide React | Icons |
| Axios | HTTP Client |
| Tailwind CSS | Utility Classes (optional) |
| Recharts | Charts & Graphs |

## 📊 API Integration

### Fetching Data

```typescript
import { useDashboardStats, useUploadQueue } from './hooks/useData';

function MyComponent() {
  // Auto-refetch every 30 seconds
  const { stats, loading, error } = useDashboardStats();
  
  // Auto-refetch every 10 seconds
  const { jobs } = useUploadQueue();
  
  return (
    <>
      <h1>{stats?.totalViews}</h1>
      <p>{jobs.length} uploads in queue</p>
    </>
  );
}
```

### Uploading Files

```typescript
import { dashboardService } from './services/dashboardService';

const job = await dashboardService.uploadFile(
  file,
  'Video Title',
  'Video Description',
  ['youtube', 'tiktok']
);
```

### WebSocket Live Updates

```typescript
dashboardService.connectWebSocket((data) => {
  console.log('Live update:', data);
  // Updates from: queue status, platform connections, analytics
});
```

## 🎯 Component Props

### Dashboard
```typescript
interface DashboardProps {
  onLogout?: () => void;  // Logout callback
}
```

### StatsCard
```typescript
interface StatsCardProps {
  title: string;           // Card title
  value: number | string;  // Displayed value
  trend?: number;          // Trend percentage
  icon?: string;           // Emoji icon
  loading?: boolean;       // Loading state
  onClick?: () => void;    // Click handler
}
```

### DragDropUpload
```typescript
interface DragDropUploadProps {
  onClose: () => void;     // Close modal callback
  onSuccess?: () => void;  // Success callback
}
```

## 📱 Responsive Design

- **Desktop** (≥1024px): 4-column grid
- **Tablet** (768-1024px): 2-column grid  
- **Mobile** (<480px): 1-column grid

All components adapt seamlessly across breakpoints.

## 🔒 Type Safety

Full TypeScript support with strict mode enabled:

```typescript
// From ui/dashboard/types/index.ts
export interface UploadJob {
  id: string;
  title: string;
  status: 'queued' | 'uploading' | 'completed' | 'failed';
  progress: number;
  platforms: string[];
  createdAt: string;
  error?: string;
}
```

## 🚀 Production Build

```bash
# Build optimized production bundle
npm run build

# Output: dist/ directory ready for deployment
# Includes:
# - Minified JavaScript
# - Optimized assets
# - Source maps (optional)
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

## 📚 Documentation

- [Detailed Setup Guide](./SETUP_GUIDE.md) - Complete installation & configuration
- [API Documentation](./API_DOCS.md) - Backend endpoint specifications
- [Component Storybook](./storybook/) - Component showcase (TODO)

## 🐛 Troubleshooting

### Port 3000 Already in Use
```bash
npm run dev -- --port 3001
```

### Module Not Found
```bash
rm -rf node_modules package-lock.json
npm install
```

### WebSocket Connection Failed
- Verify backend running on port 5000
- Check CORS configuration
- Ensure proxy in `vite.config.ts` is correct

### TypeScript Errors
```bash
npm run type-check
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

© 2024 Social Video Publisher. All rights reserved.

## 🙏 Acknowledgments

- Icons by [Lucide React](https://lucide.dev)
- Built with ❤️ for content creators
- Dashboard design inspired by modern web applications

---

**Ready to get started?** Check out [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed instructions!

For questions or support, please open an issue on GitHub.
