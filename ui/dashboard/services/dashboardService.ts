/**
 * Dashboard API Service
 * Kommuniziert mit dem Backend Flask-Server
 */

import {
  DashboardStats,
  UploadJob,
  Platform,
  UploadQueueResponse,
  AnalyticsData,
  APISettings,
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

/**
 * Statistiken abrufen
 */
export async function getStats(): Promise<DashboardStats> {
  const response = await fetch(`${API_BASE_URL}/stats`);
  if (!response.ok) throw new Error('Failed to fetch stats');
  return response.json();
}

/**
 * Upload-Queue abrufen
 */
export async function getUploadQueue(): Promise<UploadQueueResponse> {
  const response = await fetch(`${API_BASE_URL}/queue`);
  if (!response.ok) throw new Error('Failed to fetch queue');
  return response.json();
}

/**
 * Datei hochladen
 */
export async function uploadFile(
  file: File,
  title: string,
  description: string,
  platforms: string[]
): Promise<UploadJob> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', title);
  formData.append('description', description);
  formData.append('platforms', JSON.stringify(platforms));

  const response = await fetch(`${API_BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) throw new Error('Upload failed');
  return response.json();
}

/**
 * Upload abbrechen
 */
export async function cancelUpload(jobId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/queue/${jobId}`, {
    method: 'DELETE',
  });

  if (!response.ok) throw new Error('Failed to cancel upload');
}

/**
 * Platform-Status abrufen
 */
export async function getPlatforms(): Promise<Platform[]> {
  const response = await fetch(`${API_BASE_URL}/platforms`);
  if (!response.ok) throw new Error('Failed to fetch platforms');
  return response.json();
}

/**
 * Platform verbinden
 */
export async function connectPlatform(
  platformId: Platform['id'],
  credentials: Record<string, string>
): Promise<Platform> {
  const response = await fetch(`${API_BASE_URL}/platforms/${platformId}/connect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) throw new Error('Failed to connect platform');
  return response.json();
}

/**
 * Analytics-Daten abrufen
 */
export async function getAnalytics(
  days: number = 30
): Promise<AnalyticsData[]> {
  const response = await fetch(`${API_BASE_URL}/analytics?days=${days}`);
  if (!response.ok) throw new Error('Failed to fetch analytics');
  return response.json();
}

/**
 * Einstellungen abrufen
 */
export async function getSettings(): Promise<APISettings> {
  const response = await fetch(`${API_BASE_URL}/settings`);
  if (!response.ok) throw new Error('Failed to fetch settings');
  return response.json();
}

/**
 * Einstellungen speichern
 */
export async function saveSettings(settings: Partial<APISettings>): Promise<APISettings> {
  const response = await fetch(`${API_BASE_URL}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings),
  });

  if (!response.ok) throw new Error('Failed to save settings');
  return response.json();
}

/**
 * WebSocket für Live-Updates
 */
export function connectWebSocket(
  onMessage: (data: any) => void,
  onError?: (error: Event) => void
): WebSocket {
  const wsUrl = (API_BASE_URL.replace('http', 'ws')) + '/ws';
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    if (onError) onError(error);
  };

  return ws;
}
