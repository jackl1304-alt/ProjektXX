/**
 * Type Definitions für Social Video AutoPublisher Dashboard
 */

export interface UploadJob {
  id: string;
  filename: string;
  title: string;
  description: string;
  platforms: Platform[];
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  createdAt: Date;
  uploadedAt?: Date;
  errorMessage?: string;
  estimatedTime?: number;
}

export interface Platform {
  id: 'youtube' | 'tiktok' | 'clapper' | 'instagram';
  name: string;
  icon: string;
  status: 'connected' | 'disconnected' | 'error';
  lastUpload?: Date;
  videoCount: number;
  isEnabled: boolean;
}

export interface DashboardStats {
  totalUploads: number;
  uploadsToday: number;
  successRate: number;
  totalViews: number;
  totalEngagement: number;
  platformStats: PlatformStat[];
  queuedVideos: number;
  currentlyUploading: number;
}

export interface PlatformStat {
  platform: Platform['id'];
  uploads: number;
  views: number;
  engagement: number;
  successRate: number;
  averageWatchTime: number;
}

export interface AnalyticsData {
  date: Date;
  views: number;
  engagement: number;
  uploads: number;
  platform: Platform['id'];
}

export interface APISettings {
  youtube_api_key: string;
  youtube_credentials_path: string;
  tiktok_api_key?: string;
  tiktok_api_secret?: string;
  clapper_email?: string;
  clapper_password?: string;
  reddit_subreddits: string[];
  reddit_limit: number;
}

export interface UploadQueueResponse {
  jobs: UploadJob[];
  total: number;
  pending: number;
  uploading: number;
}

export interface ScheduleConfig {
  platform: Platform['id'];
  time: string;
  daysOfWeek: number[];
  enabled: boolean;
}
