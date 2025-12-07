/**
 * Custom Hooks für Dashboard
 */

import { useState, useEffect, useCallback } from 'react';
import { DashboardStats, UploadJob, Platform } from '../types';
import * as dashboardService from '../services/dashboardService';

export const useDashboardStats = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dashboardService.getStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
};

export const useUploadQueue = () => {
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchQueue = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dashboardService.getUploadQueue();
      setJobs(data.jobs);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch queue');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQueue();
    const interval = setInterval(fetchQueue, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, [fetchQueue]);

  const uploadFile = useCallback(
    async (
      file: File,
      title: string,
      description: string,
      platforms: Platform['id'][]
    ) => {
      try {
        setError(null);
        await dashboardService.uploadFile(file, title, description, platforms);
        await fetchQueue();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed');
        throw err;
      }
    },
    [fetchQueue]
  );

  const cancelJob = useCallback(
    async (jobId: string) => {
      try {
        setError(null);
        await dashboardService.cancelUpload(jobId);
        await fetchQueue();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to cancel upload');
        throw err;
      }
    },
    [fetchQueue]
  );

  return { jobs, loading, error, uploadFile, cancelJob, refetch: fetchQueue };
};

export const usePlatformStatus = () => {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPlatforms = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await dashboardService.getPlatforms();
      setPlatforms(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch platforms');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPlatforms();
    const interval = setInterval(fetchPlatforms, 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, [fetchPlatforms]);

  return { platforms, loading, error, refetch: fetchPlatforms };
};
