import React, { useState } from 'react';
import { Calendar, TrendingUp, Users, Eye, ThumbsUp } from 'lucide-react';

interface ChartData {
  date: string;
  views: number;
  likes: number;
  shares: number;
}

interface PlatformAnalytics {
  platform: string;
  views: number;
  engagement: number;
  icon: string;
}

const Analytics: React.FC = () => {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('month');

  // Mock data - in real app, this would come from API
  const chartData: ChartData[] = [
    { date: 'Mon', views: 2400, likes: 240, shares: 120 },
    { date: 'Tue', views: 1398, likes: 221, shares: 98 },
    { date: 'Wed', views: 9800, likes: 229, shares: 200 },
    { date: 'Thu', views: 3908, likes: 200, shares: 150 },
    { date: 'Fri', views: 4800, likes: 478, shares: 210 },
    { date: 'Sat', views: 3800, likes: 320, shares: 180 },
    { date: 'Sun', views: 4300, likes: 490, shares: 220 },
  ];

  const platformStats: PlatformAnalytics[] = [
    { platform: 'YouTube', views: 125000, engagement: 8.5, icon: '▶️' },
    { platform: 'TikTok', views: 89000, engagement: 12.3, icon: '🎵' },
    { platform: 'Instagram', views: 45000, engagement: 9.8, icon: '📸' },
    { platform: 'Twitter', views: 23000, engagement: 5.2, icon: '𝕏' },
  ];

  const maxViews = Math.max(...chartData.map((d) => d.views));

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex gap-2 flex-wrap">
        {(['week', 'month', 'year'] as const).map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-lg transition-all capitalize ${
              timeRange === range
                ? 'bg-gradient-to-r from-primary to-secondary text-white'
                : 'glass-card secondary'
            }`}
          >
            {range}
          </button>
        ))}
      </div>

      {/* Main Chart - Bar Chart Representation */}
      <div className="glass-card">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-text-primary">Views Trend</h3>
          <div className="flex gap-2">
            <div className="flex items-center gap-2 text-sm">
              <div className="w-3 h-3 rounded bg-primary" />
              <span className="text-text-secondary">Views</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <div className="w-3 h-3 rounded bg-secondary" />
              <span className="text-text-secondary">Engagement</span>
            </div>
          </div>
        </div>

        {/* ASCII-style Bar Chart */}
        <div className="space-y-4">
          {chartData.map((item) => (
            <div key={item.date}>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium text-text-primary">
                  {item.date}
                </span>
                <span className="text-sm text-text-secondary">
                  {item.views.toLocaleString()} views
                </span>
              </div>
              <div className="relative h-8 bg-glass-light rounded-lg overflow-hidden">
                <div
                  className="absolute h-full bg-gradient-to-r from-primary to-secondary rounded-lg transition-all duration-300 flex items-center justify-end pr-2"
                  style={{ width: `${(item.views / maxViews) * 100}%` }}
                >
                  {(item.views / maxViews) * 100 > 10 && (
                    <span className="text-xs font-semibold text-white">
                      {((item.views / maxViews) * 100).toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Platform Performance Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {platformStats.map((platform) => (
          <div key={platform.platform} className="glass-card group">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h4 className="font-semibold text-text-primary text-lg mb-1">
                  {platform.platform}
                </h4>
                <p className="text-2xl text-text-secondary mb-2">
                  {platform.icon}
                </p>
              </div>
              <TrendingUp className="text-success opacity-50 group-hover:opacity-100 transition-opacity" />
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-xs text-text-tertiary uppercase tracking-wider mb-1">
                  Total Views
                </p>
                <p className="text-2xl font-bold text-primary">
                  {(platform.views / 1000).toFixed(0)}K
                </p>
              </div>

              <div>
                <p className="text-xs text-text-tertiary uppercase tracking-wider mb-1">
                  Engagement Rate
                </p>
                <p className="text-xl font-semibold text-secondary">
                  {platform.engagement}%
                </p>
              </div>

              <div className="pt-2 border-t border-border-light">
                <button className="w-full text-xs text-primary hover:text-secondary transition-colors py-1 font-medium">
                  View Details →
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-tertiary uppercase tracking-wider mb-2">
                Total Views
              </p>
              <p className="text-3xl font-bold text-primary">382K</p>
              <p className="text-xs text-success mt-2">+12% from last period</p>
            </div>
            <Eye className="text-primary opacity-30 flex-shrink-0" size={32} />
          </div>
        </div>

        <div className="glass-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-tertiary uppercase tracking-wider mb-2">
                Total Engagements
              </p>
              <p className="text-3xl font-bold text-secondary">18.5K</p>
              <p className="text-xs text-success mt-2">+8% from last period</p>
            </div>
            <ThumbsUp className="text-secondary opacity-30 flex-shrink-0" size={32} />
          </div>
        </div>

        <div className="glass-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-tertiary uppercase tracking-wider mb-2">
                New Followers
              </p>
              <p className="text-3xl font-bold text-accent">2.3K</p>
              <p className="text-xs text-success mt-2">+5% from last period</p>
            </div>
            <Users className="text-accent opacity-30 flex-shrink-0" size={32} />
          </div>
        </div>

        <div className="glass-card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-text-tertiary uppercase tracking-wider mb-2">
                Avg Engagement
              </p>
              <p className="text-3xl font-bold text-success">9.2%</p>
              <p className="text-xs text-warning mt-2">-2% from last period</p>
            </div>
            <TrendingUp className="text-success opacity-30 flex-shrink-0" size={32} />
          </div>
        </div>
      </div>

      {/* Top Videos */}
      <div className="glass-card">
        <h3 className="text-xl font-semibold text-text-primary mb-6">
          Top Performing Videos
        </h3>

        <div className="space-y-4">
          {[
            {
              title: 'Quick Tips for Content Creators',
              views: 45000,
              engagement: 12.5,
            },
            {
              title: 'Behind the Scenes: Making Content',
              views: 38000,
              engagement: 11.2,
            },
            {
              title: 'Tech Review: Latest Gear',
              views: 32000,
              engagement: 9.8,
            },
            {
              title: 'Daily Vlog: Production Process',
              views: 28000,
              engagement: 8.5,
            },
          ].map((video, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-4 bg-glass-light rounded-lg hover:bg-glass-lighter transition-colors"
            >
              <div className="flex items-center gap-3 flex-1">
                <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full bg-gradient-to-br from-primary to-secondary text-white font-bold text-sm">
                  {index + 1}
                </span>
                <div className="flex-1">
                  <p className="font-medium text-text-primary">{video.title}</p>
                  <p className="text-sm text-text-tertiary">
                    {video.views.toLocaleString()} views •{' '}
                    {video.engagement}% engagement
                  </p>
                </div>
              </div>
              <button className="text-primary hover:text-secondary transition-colors text-sm font-medium">
                View →
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Analytics;
