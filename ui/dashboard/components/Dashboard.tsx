import React, { useState, useEffect } from 'react';
import { Moon, Sun, Menu, X, Upload, BarChart3, Settings, LogOut } from 'lucide-react';
import { useDashboardStats, useUploadQueue, usePlatformStatus } from '../hooks/useData';
import StatsCard from './StatsCard';
import UploadQueue from './UploadQueue';
import Analytics from './Analytics';
import DragDropUpload from './DragDropUpload';
import '../dashboard.css';

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: <BarChart3 size={20} /> },
  { id: 'upload', label: 'Upload', icon: <Upload size={20} /> },
  { id: 'analytics', label: 'Analytics', icon: <BarChart3 size={20} /> },
  { id: 'settings', label: 'Settings', icon: <Settings size={20} /> },
];

interface DashboardProps {
  onLogout?: () => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [darkMode, setDarkMode] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  const { stats, loading: statsLoading, error: statsError, refetch: refetchStats } = useDashboardStats();
  const { jobs, loading: jobsLoading, error: jobsError, refetch: refetchQueue } = useUploadQueue();
  const { platforms, loading: platformsLoading, error: platformsError } = usePlatformStatus();

  useEffect(() => {
    document.documentElement.style.colorScheme = darkMode ? 'dark' : 'light';
  }, [darkMode]);

  const handleRefresh = async () => {
    await Promise.all([refetchStats(), refetchQueue()]);
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'upload':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold gradient-text">Upload Video</h2>
              <button
                onClick={() => setUploadModalOpen(!uploadModalOpen)}
                className="glass-button"
              >
                <Upload size={18} style={{ marginRight: '8px' }} />
                New Upload
              </button>
            </div>
            {uploadModalOpen && <DragDropUpload onClose={() => setUploadModalOpen(false)} />}
            <UploadQueue jobs={jobs} loading={jobsLoading} error={jobsError} />
          </div>
        );
      case 'analytics':
        return (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold gradient-text">Analytics</h2>
            <Analytics />
          </div>
        );
      case 'settings':
        return (
          <div className="glass-card">
            <h2 className="text-3xl font-bold gradient-text mb-6">Settings</h2>
            <div className="space-y-4 text-text-secondary">
              <p>Platform configuration coming soon...</p>
            </div>
          </div>
        );
      default:
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center mb-8">
              <div>
                <h2 className="text-3xl font-bold text-primary mb-2">Welcome back!</h2>
                <p className="text-text-secondary">Track your video uploads and analytics</p>
              </div>
              <button
                onClick={handleRefresh}
                className="glass-button secondary"
                disabled={statsLoading || jobsLoading}
              >
                {statsLoading ? <span className="loader" /> : 'Refresh'}
              </button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatsCard
                title="Total Uploads"
                value={stats?.totalUploads || 0}
                trend={12}
                icon="📹"
                loading={statsLoading}
              />
              <StatsCard
                title="Successful"
                value={stats?.successfulUploads || 0}
                trend={8}
                icon="✅"
                loading={statsLoading}
              />
              <StatsCard
                title="In Queue"
                value={jobs?.length || 0}
                trend={-2}
                icon="⏳"
                loading={jobsLoading}
              />
              <StatsCard
                title="Total Views"
                value={stats?.totalViews || 0}
                trend={24}
                icon="👁️"
                loading={statsLoading}
              />
            </div>

            {/* Recent Uploads */}
            <div className="glass-card animate-slide-up">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-semibold text-text-primary">Recent Uploads</h3>
                <a href="#" className="text-primary hover:text-secondary transition-colors">
                  View All →
                </a>
              </div>
              <UploadQueue jobs={jobs?.slice(0, 5) || []} loading={jobsLoading} error={jobsError} />
            </div>

            {/* Platforms Overview */}
            <div className="glass-card animate-slide-up">
              <h3 className="text-xl font-semibold text-text-primary mb-6">Platform Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {platformsLoading ? (
                  <div className="col-span-full flex justify-center">
                    <div className="loader" />
                  </div>
                ) : platforms?.length ? (
                  platforms.map((platform) => (
                    <div key={platform.name} className="flex items-center justify-between p-4 bg-glass-lighter rounded-lg border border-border-light">
                      <div>
                        <p className="font-medium text-text-primary">{platform.name}</p>
                        <p className="text-sm text-text-tertiary">
                          {platform.connected ? 'Connected' : 'Not Connected'}
                        </p>
                      </div>
                      <div className={`status-indicator ${platform.connected ? 'success' : 'error'}`} />
                    </div>
                  ))
                ) : (
                  <p className="col-span-full text-text-secondary">No platforms configured</p>
                )}
              </div>
            </div>
          </div>
        );
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${darkMode ? 'bg-dark-bg' : 'bg-white'}`}>
      {/* Header */}
      <header className="glass-card sticky top-0 z-50 rounded-none md:rounded-xl m-0 md:m-4 flex justify-between items-center">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 bg-gradient-to-br from-primary to-secondary rounded-lg flex items-center justify-center">
            <span className="font-bold text-white">PX</span>
          </div>
          <h1 className="text-2xl font-bold gradient-text hidden sm:block">
            Social Video Publisher
          </h1>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden lg:flex gap-2">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-300 ${
                activeTab === item.id
                  ? 'bg-gradient-to-r from-primary to-secondary text-white'
                  : 'text-text-secondary hover:text-text-primary hover:bg-glass-light'
              }`}
            >
              {item.icon}
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Right Controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="glass-button secondary p-2 !px-3"
            title={darkMode ? 'Light Mode' : 'Dark Mode'}
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            onClick={onLogout}
            className="glass-button secondary p-2 !px-3 hidden sm:flex items-center gap-2"
            title="Logout"
          >
            <LogOut size={18} />
          </button>
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="glass-button secondary p-2 !px-3 lg:hidden"
          >
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="lg:hidden glass-card rounded-none m-0 border-t border-border-light animate-slide-down">
          <nav className="flex flex-col gap-2">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  activeTab === item.id
                    ? 'bg-gradient-to-r from-primary to-secondary text-white'
                    : 'text-text-secondary hover:text-text-primary hover:bg-glass-light'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
        </div>
      )}

      {/* Main Content */}
      <main className="p-4 md:p-8 max-w-7xl mx-auto">
        {statsError && (
          <div className="glass-card bg-error/10 border-error/30 mb-6 animate-slide-down">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚠️</span>
              <div>
                <p className="font-semibold text-error">Error loading data</p>
                <p className="text-sm text-text-secondary">{statsError}</p>
              </div>
            </div>
          </div>
        )}
        {renderContent()}
      </main>

      {/* Footer */}
      <footer className="border-t border-border-light mt-12 py-8 text-center text-text-tertiary">
        <p>© 2024 Social Video Publisher. Built with ❤️ for content creators.</p>
      </footer>
    </div>
  );
};

export default Dashboard;
