import React from 'react';
import { Trash2, Pause, Play, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { UploadJob } from '../types';

interface UploadQueueProps {
  jobs: UploadJob[];
  loading?: boolean;
  error?: string | null;
  onCancel?: (jobId: string) => void;
}

const UploadQueue: React.FC<UploadQueueProps> = ({
  jobs,
  loading = false,
  error = null,
  onCancel,
}) => {
  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'completed':
        return 'badge success';
      case 'failed':
        return 'badge error';
      case 'uploading':
        return 'badge info';
      case 'queued':
        return 'badge warning';
      default:
        return 'badge';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={18} />;
      case 'failed':
        return <AlertCircle size={18} />;
      case 'uploading':
        return <Play size={18} />;
      case 'queued':
        return <Clock size={18} />;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="glass-card">
            <div className="skeleton h-24 w-full" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card bg-error/10 border-error/30">
        <div className="flex items-center gap-3">
          <AlertCircle className="text-error" size={24} />
          <div>
            <p className="font-semibold text-error">Error Loading Queue</p>
            <p className="text-sm text-text-secondary">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="glass-card text-center py-12">
        <p className="text-5xl mb-4">📭</p>
        <p className="text-text-secondary">No uploads in queue</p>
        <p className="text-text-tertiary text-sm">Start uploading videos to see them here</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {jobs.map((job, index) => (
        <div
          key={job.id}
          className="glass-card animate-slide-up group"
          style={{ animationDelay: `${index * 0.05}s` }}
        >
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            {/* Left Section - Title & Platforms */}
            <div className="flex-1">
              <div className="flex items-start gap-3">
                <div className="text-3xl flex-shrink-0 mt-1">🎥</div>
                <div className="flex-1">
                  <h4 className="font-semibold text-text-primary mb-1 line-clamp">
                    {job.title}
                  </h4>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {job.platforms?.map((platform) => (
                      <span
                        key={platform}
                        className="text-xs bg-primary/10 text-primary px-2 py-1 rounded border border-primary/20"
                      >
                        {platform}
                      </span>
                    ))}
                  </div>
                  <p className="text-sm text-text-tertiary">
                    {new Date(job.createdAt).toLocaleDateString('de-DE', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            </div>

            {/* Progress & Status */}
            <div className="flex-shrink-0 md:text-right">
              <div className={getStatusBadgeClass(job.status)}>
                {getStatusIcon(job.status)}
                {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
              </div>

              {/* Progress Bar */}
              {job.status === 'uploading' && (
                <div className="mt-3 w-full md:w-48">
                  <div className="progress-bar">
                    <div
                      className="progress-bar-fill"
                      style={{ width: `${job.progress || 0}%` }}
                    />
                  </div>
                  <p className="text-xs text-text-tertiary mt-1">
                    {job.progress || 0}% complete
                  </p>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 md:gap-1 md:flex-col lg:flex-row">
              {job.status === 'uploading' && (
                <button
                  onClick={() => {}}
                  className="glass-button secondary p-2 flex-1 md:flex-none"
                  title="Pause upload"
                >
                  <Pause size={18} />
                </button>
              )}
              {job.status === 'queued' && (
                <button
                  onClick={() => {}}
                  className="glass-button secondary p-2 flex-1 md:flex-none"
                  title="Resume upload"
                >
                  <Play size={18} />
                </button>
              )}
              {(job.status === 'queued' || job.status === 'uploading') && (
                <button
                  onClick={() => onCancel?.(job.id)}
                  className="glass-button secondary p-2 flex-1 md:flex-none text-error hover:bg-error/10 hover:border-error/30"
                  title="Cancel upload"
                >
                  <Trash2 size={18} />
                </button>
              )}
            </div>
          </div>

          {/* Error Message */}
          {job.status === 'failed' && job.error && (
            <div className="mt-3 p-3 bg-error/10 border border-error/20 rounded-lg">
              <p className="text-xs text-error">{job.error}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default UploadQueue;
