import React, { useState, useRef } from 'react';
import { Upload, X, Check } from 'lucide-react';
import { dashboardService } from '../services/dashboardService';

interface DragDropUploadProps {
  onClose: () => void;
  onSuccess?: () => void;
}

const DragDropUpload: React.FC<DragDropUploadProps> = ({ onClose, onSuccess }) => {
  const [dragActive, setDragActive] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [platforms, setPlatforms] = useState<string[]>(['youtube']);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const availablePlatforms = ['youtube', 'tiktok', 'instagram', 'twitter'];

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const droppedFiles = Array.from(e.dataTransfer.files);
    const videoFiles = droppedFiles.filter(
      (file) =>
        file.type.startsWith('video/') ||
        file.name.match(/\.(mp4|mov|avi|mkv|webm)$/i)
    );

    if (videoFiles.length === 0) {
      setError('Please drop valid video files');
      return;
    }

    setFiles(videoFiles);
    setError(null);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || []);
    const videoFiles = selectedFiles.filter(
      (file) =>
        file.type.startsWith('video/') ||
        file.name.match(/\.(mp4|mov|avi|mkv|webm)$/i)
    );

    if (videoFiles.length === 0) {
      setError('Please select valid video files');
      return;
    }

    setFiles(videoFiles);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!files.length) {
      setError('Please select a video file');
      return;
    }

    if (!title.trim()) {
      setError('Please enter a title');
      return;
    }

    if (platforms.length === 0) {
      setError('Please select at least one platform');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Upload each file to selected platforms
      for (const file of files) {
        await dashboardService.uploadFile(
          file,
          title,
          description,
          platforms
        );
      }

      setUploadSuccess(true);
      setTimeout(() => {
        onSuccess?.();
        onClose();
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setUploading(false);
    }
  };

  const togglePlatform = (platform: string) => {
    setPlatforms((prev) =>
      prev.includes(platform)
        ? prev.filter((p) => p !== platform)
        : [...prev, platform]
    );
  };

  if (uploadSuccess) {
    return (
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
        <div className="glass-card max-w-md w-full animate-scale-in">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-br from-success to-primary rounded-full flex items-center justify-center mx-auto mb-4 animate-scale-in">
              <Check size={32} className="text-white" />
            </div>
            <h3 className="text-2xl font-bold text-text-primary mb-2">
              Upload Successful!
            </h3>
            <p className="text-text-secondary">
              Your video has been queued for processing
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in">
      <div className="glass-card max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-scale-in">
        {/* Header */}
        <div className="flex justify-between items-center mb-6 pb-4 border-b border-border-light">
          <h2 className="text-2xl font-bold gradient-text">Upload Video</h2>
          <button
            onClick={onClose}
            className="glass-button secondary p-2"
            disabled={uploading}
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Drag & Drop Area */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer ${
              dragActive
                ? 'border-primary bg-primary/10'
                : 'border-border-light hover:border-primary/50'
            }`}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              multiple
              accept="video/*"
              onChange={handleInputChange}
              className="hidden"
              disabled={uploading}
            />

            {files.length === 0 ? (
              <>
                <Upload
                  size={48}
                  className="mx-auto mb-4 text-primary opacity-50"
                />
                <p className="text-lg font-semibold text-text-primary mb-2">
                  Drag & drop your video here
                </p>
                <p className="text-sm text-text-secondary mb-4">
                  or click to browse (MP4, MOV, AVI, MKV, WebM)
                </p>
                <p className="text-xs text-text-tertiary">
                  Max 5GB per file
                </p>
              </>
            ) : (
              <div className="space-y-3">
                {files.map((file) => (
                  <div
                    key={file.name}
                    className="flex items-center justify-between p-3 bg-glass-light rounded-lg"
                  >
                    <div className="flex items-center gap-2 text-left flex-1">
                      <span className="text-2xl">📹</span>
                      <div className="flex-1">
                        <p className="font-medium text-text-primary truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-text-tertiary">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setFiles((prev) =>
                          prev.filter((f) => f.name !== file.name)
                        );
                      }}
                      className="p-2 hover:bg-error/10 rounded-lg transition-colors"
                    >
                      <X size={18} className="text-error" />
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    inputRef.current?.click();
                  }}
                  className="w-full py-2 text-sm text-primary hover:text-secondary transition-colors"
                >
                  + Add more files
                </button>
              </div>
            )}
          </div>

          {/* Title Input */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Title *
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter video title"
              className="w-full px-4 py-2 bg-glass-light border border-border-light rounded-lg text-text-primary placeholder-text-tertiary focus:outline-none focus:border-primary transition-colors"
              disabled={uploading}
            />
          </div>

          {/* Description Input */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add video description (optional)"
              rows={4}
              className="w-full px-4 py-2 bg-glass-light border border-border-light rounded-lg text-text-primary placeholder-text-tertiary focus:outline-none focus:border-primary transition-colors resize-none"
              disabled={uploading}
            />
          </div>

          {/* Platform Selection */}
          <div>
            <label className="block text-sm font-medium text-text-primary mb-3">
              Upload to Platforms
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {availablePlatforms.map((platform) => (
                <button
                  key={platform}
                  type="button"
                  onClick={() => togglePlatform(platform)}
                  disabled={uploading}
                  className={`p-3 rounded-lg border-2 transition-all capitalize font-medium ${
                    platforms.includes(platform)
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border-light text-text-secondary hover:border-primary/50'
                  }`}
                >
                  {platform === 'youtube' && '▶️ YouTube'}
                  {platform === 'tiktok' && '🎵 TikTok'}
                  {platform === 'instagram' && '📸 Instagram'}
                  {platform === 'twitter' && '𝕏 Twitter'}
                </button>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="glass-card bg-error/10 border-error/30">
              <div className="flex items-center gap-3">
                <span className="text-xl">⚠️</span>
                <p className="text-error text-sm">{error}</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-border-light">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 glass-button secondary"
              disabled={uploading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 glass-button"
              disabled={uploading || files.length === 0 || !title.trim()}
            >
              {uploading ? (
                <>
                  <span className="loader mr-2" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload size={18} style={{ marginRight: '8px' }} />
                  Upload
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default DragDropUpload;
