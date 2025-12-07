"""
Flask API Module for Dashboard Integration
Provides REST endpoints for the React Dashboard
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
from pathlib import Path

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Configure Flask App
def create_app(config_path: str = 'config/settings.json') -> Flask:
    """Create and configure Flask application with CORS and error handling"""
    
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Load configuration
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)
            app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024  # 5GB
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Server Error', 'message': str(error)}), 500
    
    return app


def create_dashboard_routes(app: Flask, upload_manager, config: Dict[str, Any]):
    """
    Register dashboard API routes
    
    Args:
        app: Flask application instance
        upload_manager: Upload manager instance
        config: Configuration dictionary
    """
    
    # Mock data storage (in production, use database)
    upload_queue: List[Dict[str, Any]] = []
    analytics_data = {
        'totalUploads': 142,
        'successfulUploads': 138,
        'failedUploads': 4,
        'totalViews': 385000,
        'totalEngagement': 18500,
    }
    
    platforms_config = [
        {'name': 'YouTube', 'connected': True, 'icon': '▶️'},
        {'name': 'TikTok', 'connected': False, 'icon': '🎵'},
        {'name': 'Instagram', 'connected': True, 'icon': '📸'},
        {'name': 'Twitter', 'connected': False, 'icon': '𝕏'},
    ]
    
    # ============== STATS ENDPOINTS ==============
    
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get dashboard statistics"""
        return jsonify({
            'totalUploads': analytics_data['totalUploads'],
            'successfulUploads': analytics_data['successfulUploads'],
            'failedUploads': analytics_data['failedUploads'],
            'totalViews': analytics_data['totalViews'],
            'totalEngagement': analytics_data['totalEngagement'],
            'lastUpdated': datetime.now().isoformat(),
        }), 200
    
    # ============== UPLOAD QUEUE ENDPOINTS ==============
    
    @app.route('/api/queue', methods=['GET'])
    def get_upload_queue():
        """Get current upload queue"""
        return jsonify({
            'jobs': upload_queue,
            'count': len(upload_queue),
            'lastUpdated': datetime.now().isoformat(),
        }), 200
    
    @app.route('/api/upload', methods=['POST'])
    def upload_video():
        """Handle video upload"""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file provided'}), 400
            
            file = request.files['file']
            title = request.form.get('title', 'Untitled')
            description = request.form.get('description', '')
            platforms = request.form.get('platforms', '[]')
            
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            # Parse platforms
            try:
                platform_list = json.loads(platforms)
            except json.JSONDecodeError:
                platform_list = ['youtube']
            
            # Secure filename
            filename = secure_filename(file.filename)
            
            # Create upload job
            job_id = f"job_{datetime.now().timestamp()}"
            upload_job = {
                'id': job_id,
                'title': title,
                'description': description,
                'platforms': platform_list,
                'filename': filename,
                'size': len(file.read()),
                'status': 'queued',
                'progress': 0,
                'createdAt': datetime.now().isoformat(),
                'updatedAt': datetime.now().isoformat(),
            }
            
            # Reset file pointer
            file.seek(0)
            
            # Save file to temp directory
            upload_dir = Path('uploads/temp')
            upload_dir.mkdir(parents=True, exist_ok=True)
            file.save(upload_dir / filename)
            
            # Add to queue
            upload_queue.append(upload_job)
            
            # Update analytics
            analytics_data['totalUploads'] += 1
            
            return jsonify(upload_job), 201
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/upload/<job_id>', methods=['GET'])
    def get_upload_status(job_id: str):
        """Get upload job status"""
        job = next((j for j in upload_queue if j['id'] == job_id), None)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        return jsonify(job), 200
    
    @app.route('/api/upload/<job_id>', methods=['DELETE'])
    def cancel_upload(job_id: str):
        """Cancel upload job"""
        global upload_queue
        job = next((j for j in upload_queue if j['id'] == job_id), None)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        if job['status'] in ['completed', 'failed']:
            return jsonify({'error': 'Cannot cancel completed/failed job'}), 400
        
        job['status'] = 'cancelled'
        job['updatedAt'] = datetime.now().isoformat()
        
        return jsonify({'message': 'Upload cancelled', 'job': job}), 200
    
    # ============== PLATFORM ENDPOINTS ==============
    
    @app.route('/api/platforms', methods=['GET'])
    def get_platforms():
        """Get platform status"""
        return jsonify({
            'platforms': platforms_config,
            'count': len(platforms_config),
        }), 200
    
    @app.route('/api/platforms/<platform>/connect', methods=['POST'])
    def connect_platform(platform: str):
        """Connect to platform (auth flow)"""
        data = request.get_json() or {}
        
        platform_obj = next(
            (p for p in platforms_config if p['name'].lower() == platform.lower()),
            None
        )
        
        if not platform_obj:
            return jsonify({'error': 'Platform not found'}), 404
        
        # In real implementation, handle OAuth flow here
        platform_obj['connected'] = True
        
        return jsonify({
            'message': f'Successfully connected to {platform}',
            'platform': platform_obj,
        }), 200
    
    @app.route('/api/platforms/<platform>/disconnect', methods=['POST'])
    def disconnect_platform(platform: str):
        """Disconnect from platform"""
        platform_obj = next(
            (p for p in platforms_config if p['name'].lower() == platform.lower()),
            None
        )
        
        if not platform_obj:
            return jsonify({'error': 'Platform not found'}), 404
        
        platform_obj['connected'] = False
        
        return jsonify({
            'message': f'Successfully disconnected from {platform}',
            'platform': platform_obj,
        }), 200
    
    # ============== ANALYTICS ENDPOINTS ==============
    
    @app.route('/api/analytics', methods=['GET'])
    def get_analytics():
        """Get detailed analytics"""
        time_range = request.args.get('range', 'month')
        
        # Generate sample data based on time range
        if time_range == 'week':
            days = 7
        elif time_range == 'year':
            days = 365
        else:
            days = 30
        
        chart_data = [
            {
                'date': (datetime.now() - timedelta(days=i)).strftime('%a'),
                'views': 2400 + (i * 100),
                'engagement': 240 + (i * 10),
                'likes': 120 + (i * 5),
            }
            for i in range(days)
        ]
        
        platform_stats = [
            {'platform': 'YouTube', 'views': 125000, 'engagement': 8.5},
            {'platform': 'TikTok', 'views': 89000, 'engagement': 12.3},
            {'platform': 'Instagram', 'views': 45000, 'engagement': 9.8},
            {'platform': 'Twitter', 'views': 23000, 'engagement': 5.2},
        ]
        
        return jsonify({
            'timeRange': time_range,
            'chartData': chart_data,
            'platformStats': platform_stats,
            'summary': {
                'totalViews': sum(p['views'] for p in platform_stats),
                'avgEngagement': sum(p['engagement'] for p in platform_stats) / len(platform_stats),
                'topPlatform': max(platform_stats, key=lambda p: p['views'])['platform'],
            },
        }), 200
    
    # ============== SETTINGS ENDPOINTS ==============
    
    @app.route('/api/settings', methods=['GET'])
    def get_settings():
        """Get app settings"""
        settings = {
            'theme': 'dark',
            'notifications': True,
            'autoUpload': False,
            'maxRetries': 3,
            'uploadQuality': 'high',
        }
        return jsonify(settings), 200
    
    @app.route('/api/settings', methods=['POST'])
    def save_settings():
        """Save app settings"""
        try:
            data = request.get_json()
            
            # Validate settings
            valid_keys = {'theme', 'notifications', 'autoUpload', 'maxRetries', 'uploadQuality'}
            settings = {k: v for k, v in data.items() if k in valid_keys}
            
            # In real implementation, save to database
            return jsonify({
                'message': 'Settings saved',
                'settings': settings,
            }), 200
        
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    
    # ============== HEALTH CHECK ==============
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'queue_size': len(upload_queue),
        }), 200


if __name__ == '__main__':
    # Example usage
    app = create_app()
    config = {
        'UPLOAD_FOLDER': 'uploads',
        'MAX_CONTENT_LENGTH': 5 * 1024 * 1024 * 1024,  # 5GB
    }
    create_dashboard_routes(app, None, config)
    app.run(debug=True, host='0.0.0.0', port=5000)
