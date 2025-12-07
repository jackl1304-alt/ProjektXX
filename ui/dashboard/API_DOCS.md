# Social Video Publisher - API Documentation

Complete REST API documentation for the Dashboard backend.

## Base URL

```
Development:  http://localhost:5000
Production:   https://api.yourdomain.com
```

## Authentication

Currently using no authentication. In production, implement JWT tokens:

```bash
Authorization: Bearer <token>
```

## Response Format

All responses are JSON:

```json
{
  "data": {...},
  "error": null,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Error Handling

```json
{
  "error": "Error message",
  "code": 400,
  "details": "Additional details"
}
```

---

## 📊 Stats Endpoints

### Get Dashboard Statistics

Get overview statistics for the dashboard.

**Request:**
```http
GET /api/stats
```

**Response (200 OK):**
```json
{
  "totalUploads": 142,
  "successfulUploads": 138,
  "failedUploads": 4,
  "totalViews": 385000,
  "totalEngagement": 18500,
  "lastUpdated": "2024-01-15T14:30:00Z"
}
```

**Example:**
```bash
curl -X GET http://localhost:5000/api/stats
```

---

## 📹 Upload Queue Endpoints

### Get Upload Queue

Retrieve all pending and active uploads.

**Request:**
```http
GET /api/queue
```

**Response (200 OK):**
```json
{
  "jobs": [
    {
      "id": "job_1705353000",
      "title": "Quick Tips for Content Creators",
      "description": "Learn top tips for creating engaging content",
      "platforms": ["youtube", "tiktok"],
      "filename": "tips_video.mp4",
      "size": 524288000,
      "status": "uploading",
      "progress": 45,
      "createdAt": "2024-01-15T14:30:00Z",
      "updatedAt": "2024-01-15T14:31:20Z",
      "error": null
    }
  ],
  "count": 3,
  "lastUpdated": "2024-01-15T14:31:30Z"
}
```

### Create Upload

Upload a new video to the queue.

**Request:**
```http
POST /api/upload
Content-Type: multipart/form-data

- file: File (required, max 5GB)
- title: string (required)
- description: string (optional)
- platforms: string[] (required, JSON array)
```

**Response (201 Created):**
```json
{
  "id": "job_1705353000",
  "title": "New Video",
  "description": "Description here",
  "platforms": ["youtube", "tiktok"],
  "filename": "video.mp4",
  "size": 524288000,
  "status": "queued",
  "progress": 0,
  "createdAt": "2024-01-15T14:30:00Z",
  "updatedAt": "2024-01-15T14:30:00Z"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@video.mp4" \
  -F "title=My Video" \
  -F "description=A great video" \
  -F 'platforms=["youtube", "tiktok"]'
```

**Errors:**
- `400 Bad Request` - Missing required field or invalid file
- `413 Payload Too Large` - File exceeds 5GB limit

### Get Upload Status

Get details of a specific upload job.

**Request:**
```http
GET /api/upload/:jobId
```

**Response (200 OK):**
```json
{
  "id": "job_1705353000",
  "title": "New Video",
  "status": "uploading",
  "progress": 45,
  "platforms": ["youtube", "tiktok"],
  ...
}
```

### Cancel Upload

Cancel a queued or uploading job.

**Request:**
```http
DELETE /api/upload/:jobId
```

**Response (200 OK):**
```json
{
  "message": "Upload cancelled",
  "job": {
    "id": "job_1705353000",
    "status": "cancelled",
    ...
  }
}
```

**Errors:**
- `404 Not Found` - Job not found
- `400 Bad Request` - Cannot cancel completed/failed job

---

## 🌐 Platform Endpoints

### Get Connected Platforms

Get list of all available platforms and their connection status.

**Request:**
```http
GET /api/platforms
```

**Response (200 OK):**
```json
{
  "platforms": [
    {
      "name": "YouTube",
      "connected": true,
      "icon": "▶️"
    },
    {
      "name": "TikTok",
      "connected": false,
      "icon": "🎵"
    },
    {
      "name": "Instagram",
      "connected": true,
      "icon": "📸"
    },
    {
      "name": "Twitter",
      "connected": false,
      "icon": "𝕏"
    }
  ],
  "count": 4
}
```

### Connect Platform

Initiate OAuth connection with a platform.

**Request:**
```http
POST /api/platforms/:platform/connect
Content-Type: application/json

{
  "redirectUrl": "http://localhost:3000/auth/callback"
}
```

**Response (200 OK):**
```json
{
  "message": "Successfully connected to YouTube",
  "platform": {
    "name": "YouTube",
    "connected": true,
    "icon": "▶️"
  },
  "authUrl": "https://accounts.google.com/o/oauth2/auth?..."
}
```

### Disconnect Platform

Disconnect from a platform.

**Request:**
```http
POST /api/platforms/:platform/disconnect
```

**Response (200 OK):**
```json
{
  "message": "Successfully disconnected from YouTube",
  "platform": {
    "name": "YouTube",
    "connected": false,
    "icon": "▶️"
  }
}
```

---

## 📊 Analytics Endpoints

### Get Analytics Data

Get detailed analytics for a time range.

**Request:**
```http
GET /api/analytics?range=month
```

**Query Parameters:**
- `range` - Time range: `week`, `month`, `year` (default: `month`)

**Response (200 OK):**
```json
{
  "timeRange": "month",
  "chartData": [
    {
      "date": "Mon",
      "views": 2500,
      "engagement": 250,
      "likes": 125
    },
    ...
  ],
  "platformStats": [
    {
      "platform": "YouTube",
      "views": 125000,
      "engagement": 8.5
    },
    ...
  ],
  "summary": {
    "totalViews": 282000,
    "avgEngagement": 8.95,
    "topPlatform": "YouTube"
  }
}
```

---

## ⚙️ Settings Endpoints

### Get Settings

Get current application settings.

**Request:**
```http
GET /api/settings
```

**Response (200 OK):**
```json
{
  "theme": "dark",
  "notifications": true,
  "autoUpload": false,
  "maxRetries": 3,
  "uploadQuality": "high"
}
```

### Save Settings

Update application settings.

**Request:**
```http
POST /api/settings
Content-Type: application/json

{
  "theme": "dark",
  "notifications": true,
  "autoUpload": false,
  "maxRetries": 3,
  "uploadQuality": "high"
}
```

**Response (200 OK):**
```json
{
  "message": "Settings saved",
  "settings": {
    "theme": "dark",
    ...
  }
}
```

---

## 🏥 Health Check

### Server Health

Check if server is running and healthy.

**Request:**
```http
GET /api/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T14:35:00Z",
  "queue_size": 3
}
```

---

## 🔌 WebSocket Endpoints

### Live Updates

Connect to WebSocket for real-time updates.

**Endpoint:**
```
ws://localhost:5000/ws
```

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:5000/ws');

ws.onopen = () => {
  console.log('Connected');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
  // Handle: queue updates, analytics, platform status
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

**Message Types:**

```json
{
  "type": "upload_progress",
  "jobId": "job_1705353000",
  "progress": 75
}
```

```json
{
  "type": "upload_completed",
  "jobId": "job_1705353000",
  "status": "completed"
}
```

```json
{
  "type": "analytics_update",
  "views": 385000,
  "engagement": 18500
}
```

---

## 📋 Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 404 | Not Found |
| 413 | Payload Too Large |
| 500 | Server Error |

---

## 🔐 Rate Limiting

Currently disabled. In production, implement:

```
Rate Limit: 100 requests per minute per IP
Headers: X-RateLimit-Limit, X-RateLimit-Remaining
```

---

## 📝 Request Examples

### JavaScript / TypeScript

```typescript
import axios from 'axios';

// Get stats
const stats = await axios.get('http://localhost:5000/api/stats');
console.log(stats.data);

// Upload video
const formData = new FormData();
formData.append('file', videoFile);
formData.append('title', 'My Video');
formData.append('platforms', JSON.stringify(['youtube', 'tiktok']));

const job = await axios.post('http://localhost:5000/api/upload', formData);
console.log(job.data);
```

### Python

```python
import requests
import json

# Get stats
response = requests.get('http://localhost:5000/api/stats')
print(response.json())

# Upload video
files = {'file': open('video.mp4', 'rb')}
data = {
    'title': 'My Video',
    'platforms': json.dumps(['youtube', 'tiktok'])
}
response = requests.post('http://localhost:5000/api/upload', files=files, data=data)
print(response.json())
```

### cURL

```bash
# Get stats
curl -X GET http://localhost:5000/api/stats

# Upload video
curl -X POST http://localhost:5000/api/upload \
  -F "file=@video.mp4" \
  -F "title=My Video" \
  -F 'platforms=["youtube","tiktok"]'
```

---

## 🚀 Deployment Considerations

1. **Enable HTTPS** - Use SSL certificates in production
2. **Add Authentication** - Implement JWT or OAuth
3. **Rate Limiting** - Prevent abuse with rate limiting
4. **CORS** - Configure allowed origins properly
5. **Logging** - Implement comprehensive logging
6. **Monitoring** - Track errors and performance
7. **Database** - Replace in-memory storage with database
8. **File Storage** - Use cloud storage (S3, GCS) for videos

---

**Last Updated:** January 2024  
**Version:** 1.0.0
