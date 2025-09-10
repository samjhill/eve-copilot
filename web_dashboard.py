#!/usr/bin/env python3
"""
EVE Copilot Web Dashboard
Modern web-based interface for monitoring and controlling EVE Copilot
"""

import asyncio
import json
import logging
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
import webbrowser
from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_socketio import SocketIO, emit
import psutil

from evetalk.config import Config
from evetalk.engine import RulesEngine
from evetalk.parse import LogParser
from evetalk.notify import SpeechNotifier
from evetalk.watcher import LogWatcher

logger = logging.getLogger(__name__)

class WebDashboard:
    """Web-based dashboard for EVE Copilot."""
    
    def __init__(self, config: Config, rules_engine: RulesEngine, log_watcher: LogWatcher):
        """Initialize web dashboard.
        
        Args:
            config: Application configuration
            rules_engine: Rules engine instance
            log_watcher: Log watcher instance
        """
        self.config = config
        self.rules_engine = rules_engine
        self.log_watcher = log_watcher
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'eve_copilot_dashboard_secret_key'
        self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", allow_unsafe_werkzeug=True)
        
        # Dashboard state
        self.start_time = datetime.now()
        self.last_activity = None
        self.alert_history = []
        self.performance_metrics = {
            'events_processed': 0,
            'rules_triggered': 0,
            'alerts_sent': 0,
            'avg_response_time': 0.0,
            'memory_usage': 0.0,
            'cpu_usage': 0.0
        }
        
        # Connect rules engine to dashboard alerts
        if self.rules_engine:
            self.rules_engine.alert_callback = self.add_alert
        
        # Setup routes and socket events
        self._setup_routes()
        self._setup_socket_events()
        
        # Start background monitoring
        self._start_monitoring()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            try:
                return render_template('dashboard.html')
            except Exception as e:
                logger.error(f"Error rendering dashboard: {e}")
                return f"<h1>EVE Copilot Dashboard</h1><p>Error loading dashboard: {e}</p>", 500
        
        @self.app.route('/api/status')
        def api_status():
            """Get current system status."""
            return jsonify(self._get_system_status())
        
        @self.app.route('/api/alerts')
        def api_alerts():
            """Get recent alerts."""
            limit = request.args.get('limit', 50, type=int)
            return jsonify(self.alert_history[-limit:])
        
        @self.app.route('/api/metrics')
        def api_metrics():
            """Get performance metrics."""
            return jsonify(self.performance_metrics)
        
        @self.app.route('/test')
        def test():
            """Test route to verify Flask is working."""
            return jsonify({'status': 'ok', 'message': 'Flask is working'})
        
        @self.app.route('/api/config')
        def api_config():
            """Get current configuration."""
            return jsonify(self._get_config_data())
        
        @self.app.route('/api/config', methods=['POST'])
        def api_update_config():
            """Update configuration."""
            try:
                data = request.get_json()
                self._update_config(data)
                return jsonify({'success': True, 'message': 'Configuration updated'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 400
        
        @self.app.route('/api/control', methods=['POST'])
        def api_control():
            """Control application actions."""
            try:
                data = request.get_json()
                action = data.get('action')
                
                if action == 'start_watching':
                    if self.log_watcher and hasattr(self.log_watcher, 'start'):
                        if asyncio.iscoroutinefunction(self.log_watcher.start):
                            # Run async method in new event loop
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(self.log_watcher.start())
                            loop.close()
                        else:
                            self.log_watcher.start()
                        return jsonify({'success': True, 'message': 'Started watching logs'})
                    else:
                        return jsonify({'success': False, 'message': 'Log watcher not available'}), 400
                        
                elif action == 'stop_watching':
                    if self.log_watcher and hasattr(self.log_watcher, 'stop'):
                        if asyncio.iscoroutinefunction(self.log_watcher.stop):
                            # Run async method in new event loop
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(self.log_watcher.stop())
                            loop.close()
                        else:
                            self.log_watcher.stop()
                        return jsonify({'success': True, 'message': 'Stopped watching logs'})
                    else:
                        return jsonify({'success': False, 'message': 'Log watcher not available'}), 400
                        
                elif action == 'reload_config':
                    self.config.reload()
                    if self.rules_engine and hasattr(self.rules_engine, 'reload_config'):
                        self.rules_engine.reload_config()
                    return jsonify({'success': True, 'message': 'Configuration reloaded'})
                    
                elif action == 'test_speech':
                    if self.rules_engine and hasattr(self.rules_engine, 'speech_notifier'):
                        self.rules_engine.speech_notifier.speak("EVE Copilot dashboard test", priority=2)
                        # Also add an alert to the dashboard
                        logger.info("Adding test alert to dashboard")
                        self.add_alert("test_speech", "EVE Copilot dashboard test", 2)
                        logger.info(f"Alert added. Total alerts: {len(self.alert_history)}")
                        return jsonify({'success': True, 'message': 'Speech test sent'})
                    else:
                        return jsonify({'success': False, 'message': 'Speech notifier not available'}), 400
                        
                elif action == 'force_detect_log':
                    if self.log_watcher and hasattr(self.log_watcher, 'force_detect_active_file'):
                        active_file = self.log_watcher.force_detect_active_file()
                        if active_file:
                            return jsonify({'success': True, 'message': f'Detected active log file: {active_file}'})
                        else:
                            return jsonify({'success': False, 'message': 'No active log file found'})
                    else:
                        return jsonify({'success': False, 'message': 'Log watcher not available'}), 400
                        
                else:
                    return jsonify({'success': False, 'message': 'Unknown action'}), 400
                    
            except Exception as e:
                logger.error(f"Error in control API: {e}")
                return jsonify({'success': False, 'message': str(e)}), 500
    
    def _setup_socket_events(self):
        """Setup SocketIO events for real-time updates."""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection."""
            logger.info('Client connected to dashboard')
            emit('status', self._get_system_status())
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection."""
            logger.info('Client disconnected from dashboard')
        
        @self.socketio.on('request_status')
        def handle_status_request():
            """Handle status update request."""
            emit('status', self._get_system_status())
        
        @self.socketio.on('request_alerts')
        def handle_alerts_request():
            """Handle alerts request."""
            emit('alerts', self.alert_history[-50:])
    
    def _start_monitoring(self):
        """Start background monitoring thread."""
        def monitor():
            while True:
                try:
                    # Update performance metrics
                    self._update_performance_metrics()
                    
                    # Emit real-time updates
                    self.socketio.emit('status', self._get_system_status())
                    self.socketio.emit('metrics', self.performance_metrics)
                    
                    time.sleep(1)  # Update every second
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        try:
            # Get watcher status
            watcher_status = {}
            if self.log_watcher and hasattr(self.log_watcher, 'get_status'):
                watcher_status = self.log_watcher.get_status()
            else:
                watcher_status = {
                    'watching': False,
                    'files_monitored': 0,
                    'events_processed': 0,
                    'current_file': 'Not Available (Web-only mode)'
                }
            
            # Get engine status
            engine_status = {}
            if self.rules_engine and hasattr(self.rules_engine, 'get_status'):
                engine_status = self.rules_engine.get_status()
                logger.info(f"Web dashboard: rules_engine exists, got status: {engine_status}")
            else:
                logger.info(f"Web dashboard: rules_engine is None or no get_status method. rules_engine={self.rules_engine}")
                engine_status = {
                    'active_profile': 'Not Available (Web-only mode)',
                    'rules_count': 0,
                    'rules_triggered': 0,
                    'speech_enabled': False
                }
            
            # Calculate uptime
            uptime = datetime.now() - self.start_time
            
            return {
                'status': 'running',
                'uptime': str(uptime).split('.')[0],  # Remove microseconds
                'start_time': self.start_time.isoformat(),
                'last_activity': self.last_activity.isoformat() if self.last_activity else None,
                'watcher': {
                    'watching': watcher_status.get('watching', False),
                    'files_monitored': watcher_status.get('files_monitored', 0),
                    'events_processed': watcher_status.get('events_processed', 0),
                    'current_file': watcher_status.get('current_file', 'None')
                },
                'engine': {
                    'active_profile': engine_status.get('active_profile', 'Unknown'),
                    'rules_loaded': engine_status.get('rules_count', 0),
                    'rules_triggered': engine_status.get('rules_triggered', 0),
                    'speech_enabled': engine_status.get('speech_enabled', False)
                },
                'performance': self.performance_metrics
            }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _update_performance_metrics(self):
        """Update performance metrics."""
        try:
            # Get process info
            process = psutil.Process()
            self.performance_metrics['memory_usage'] = process.memory_info().rss / 1024 / 1024  # MB
            self.performance_metrics['cpu_usage'] = process.cpu_percent()
            
            # Update other metrics from components
            if self.rules_engine and hasattr(self.rules_engine, 'get_status'):
                engine_status = self.rules_engine.get_status()
                self.performance_metrics['rules_triggered'] = engine_status.get('rules_triggered', 0)
                self.performance_metrics['alerts_sent'] = engine_status.get('alerts_sent', 0)
            
            if self.log_watcher and hasattr(self.log_watcher, 'get_status'):
                watcher_status = self.log_watcher.get_status()
                self.performance_metrics['events_processed'] = watcher_status.get('events_processed', 0)
                
        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")
    
    def _get_config_data(self) -> Dict[str, Any]:
        """Get current configuration data."""
        try:
            return {
                'eve_logs_path': self.config.eve_logs_path,
                'speech': self.config.speech,
                'profiles': self.config.profiles,
                'logging': self.config.logging,
                'performance': self.config.performance
            }
        except Exception as e:
            logger.error(f"Error getting config data: {e}")
            return {}
    
    def _update_config(self, data: Dict[str, Any]):
        """Update configuration."""
        try:
            # Update configuration values
            if 'eve_logs_path' in data:
                self.config.eve_logs_path = data['eve_logs_path']
            
            if 'speech' in data:
                self.config.speech.update(data['speech'])
            
            if 'profiles' in data:
                self.config.profiles.update(data['profiles'])
            
            if 'performance' in data:
                self.config.performance.update(data['performance'])
            
            # Save configuration
            self.config.save()
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            raise
    
    def add_alert(self, alert_type: str, message: str, priority: int = 1):
        """Add alert to history."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'message': message,
            'priority': priority
        }
        self.alert_history.append(alert)
        self.last_activity = datetime.now()
        
        # Keep only last 1000 alerts
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        # Emit real-time alert
        self.socketio.emit('new_alert', alert)
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Run the web dashboard."""
        try:
            logger.info(f"Starting web dashboard on http://{host}:{port}")
            
            # Open browser automatically
            if not debug:
                threading.Timer(1.5, lambda: webbrowser.open(f'http://{host}:{port}')).start()
            
            self.socketio.run(self.app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
            
        except Exception as e:
            logger.error(f"Failed to start web dashboard: {e}")
            raise


def create_dashboard_templates():
    """Create HTML templates for the dashboard."""
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    # Main dashboard template
    dashboard_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EVE Copilot Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }
        
        .status-card h3 {
            margin-bottom: 15px;
            color: #64b5f6;
            font-size: 1.2em;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .status-value {
            font-weight: bold;
            color: #4caf50;
        }
        
        .status-value.error {
            color: #f44336;
        }
        
        .status-value.warning {
            color: #ff9800;
        }
        
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .btn {
            background: #4caf50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .btn:hover {
            background: #45a049;
        }
        
        .btn.danger {
            background: #f44336;
        }
        
        .btn.danger:hover {
            background: #da190b;
        }
        
        .btn.warning {
            background: #ff9800;
        }
        
        .btn.warning:hover {
            background: #e68900;
        }
        
        .alerts-section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .alerts-section h3 {
            margin-bottom: 15px;
            color: #64b5f6;
        }
        
        .alert-item {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #4caf50;
        }
        
        .alert-item.priority-2 {
            border-left-color: #ff9800;
        }
        
        .alert-item.priority-3 {
            border-left-color: #f44336;
        }
        
        .alert-time {
            font-size: 0.8em;
            color: #bbb;
            margin-bottom: 5px;
        }
        
        .alert-message {
            font-weight: bold;
        }
        
        .chart-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            margin-top: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #64b5f6;
        }
        
        .error {
            color: #f44336;
            text-align: center;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 EVE Copilot Dashboard</h1>
            <p>Real-time monitoring and control for EVE Online voice assistant</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="startWatching()">Start Watching</button>
            <button class="btn danger" onclick="stopWatching()">Stop Watching</button>
            <button class="btn warning" onclick="reloadConfig()">Reload Config</button>
            <button class="btn" onclick="testSpeech()">Test Speech</button>
            <button class="btn" onclick="forceDetectLog()">Force Detect Log</button>
        </div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📊 System Status</h3>
                <div id="system-status">
                    <div class="loading">Loading...</div>
                </div>
            </div>
            
            <div class="status-card">
                <h3>📈 Performance</h3>
                <div id="performance-metrics">
                    <div class="loading">Loading...</div>
                </div>
            </div>
        </div>
        
        <div class="alerts-section">
            <h3>🔔 Recent Alerts</h3>
            <div id="alerts-list">
                <div class="loading">Loading alerts...</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📊 Performance Chart</h3>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
    </div>
    
    <script>
        // Initialize Socket.IO connection
        const socket = io();
        
        // Chart setup
        const ctx = document.getElementById('performanceChart').getContext('2d');
        const performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage %',
                    data: [],
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Memory Usage MB',
                    data: [],
                    borderColor: '#2196f3',
                    backgroundColor: 'rgba(33, 150, 243, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#fff'
                        }
                    }
                }
            }
        });
        
        // Socket event handlers
        socket.on('connect', function() {
            console.log('Connected to dashboard');
            loadStatus();
            loadAlerts();
        });
        
        socket.on('status', function(data) {
            updateSystemStatus(data);
        });
        
        socket.on('metrics', function(data) {
            updatePerformanceMetrics(data);
            updateChart(data);
        });
        
        socket.on('new_alert', function(alert) {
            addAlertToList(alert);
        });
        
        // Load initial data
        function loadStatus() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => updateSystemStatus(data))
                .catch(error => console.error('Error loading status:', error));
        }
        
        function loadAlerts() {
            fetch('/api/alerts')
                .then(response => response.json())
                .then(data => updateAlertsList(data))
                .catch(error => console.error('Error loading alerts:', error));
        }
        
        function updateSystemStatus(data) {
            const statusDiv = document.getElementById('system-status');
            if (data.status === 'error') {
                statusDiv.innerHTML = `<div class="error">Error: ${data.message}</div>`;
                return;
            }
            
            const uptime = data.uptime || 'Unknown';
            const lastActivity = data.last_activity ? new Date(data.last_activity).toLocaleTimeString() : 'None';
            
            statusDiv.innerHTML = `
                <div class="status-item">
                    <span>Status:</span>
                    <span class="status-value">${data.status}</span>
                </div>
                <div class="status-item">
                    <span>Uptime:</span>
                    <span class="status-value">${uptime}</span>
                </div>
                <div class="status-item">
                    <span>Last Activity:</span>
                    <span class="status-value">${lastActivity}</span>
                </div>
                <div class="status-item">
                    <span>Watching:</span>
                    <span class="status-value ${data.watcher.watching ? '' : 'error'}">${data.watcher.watching ? 'Yes' : 'No'}</span>
                </div>
                <div class="status-item">
                    <span>Files Monitored:</span>
                    <span class="status-value">${data.watcher.files_monitored}</span>
                </div>
                <div class="status-item">
                    <span>Events Processed:</span>
                    <span class="status-value">${data.watcher.events_processed}</span>
                </div>
                <div class="status-item">
                    <span>Current File:</span>
                    <span class="status-value">${data.watcher.current_file}</span>
                </div>
                <div class="status-item">
                    <span>Active Profile:</span>
                    <span class="status-value">${data.engine.active_profile}</span>
                </div>
                <div class="status-item">
                    <span>Rules Loaded:</span>
                    <span class="status-value">${data.engine.rules_loaded}</span>
                </div>
                <div class="status-item">
                    <span>Rules Triggered:</span>
                    <span class="status-value">${data.engine.rules_triggered}</span>
                </div>
            `;
        }
        
        function updatePerformanceMetrics(data) {
            const metricsDiv = document.getElementById('performance-metrics');
            metricsDiv.innerHTML = `
                <div class="status-item">
                    <span>CPU Usage:</span>
                    <span class="status-value ${data.cpu_usage > 80 ? 'error' : data.cpu_usage > 60 ? 'warning' : ''}">${data.cpu_usage.toFixed(1)}%</span>
                </div>
                <div class="status-item">
                    <span>Memory Usage:</span>
                    <span class="status-value ${data.memory_usage > 500 ? 'error' : data.memory_usage > 300 ? 'warning' : ''}">${data.memory_usage.toFixed(1)} MB</span>
                </div>
                <div class="status-item">
                    <span>Events Processed:</span>
                    <span class="status-value">${data.events_processed}</span>
                </div>
                <div class="status-item">
                    <span>Rules Triggered:</span>
                    <span class="status-value">${data.rules_triggered}</span>
                </div>
                <div class="status-item">
                    <span>Alerts Sent:</span>
                    <span class="status-value">${data.alerts_sent}</span>
                </div>
                <div class="status-item">
                    <span>Avg Response Time:</span>
                    <span class="status-value">${data.avg_response_time.toFixed(2)}s</span>
                </div>
            `;
        }
        
        function updateAlertsList(alerts) {
            const alertsDiv = document.getElementById('alerts-list');
            if (alerts.length === 0) {
                alertsDiv.innerHTML = '<div class="loading">No alerts yet</div>';
                return;
            }
            
            alertsDiv.innerHTML = alerts.map(alert => `
                <div class="alert-item priority-${alert.priority}">
                    <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                    <div class="alert-message">${alert.message}</div>
                </div>
            `).join('');
        }
        
        function addAlertToList(alert) {
            const alertsDiv = document.getElementById('alerts-list');
            const alertElement = document.createElement('div');
            alertElement.className = `alert-item priority-${alert.priority}`;
            alertElement.innerHTML = `
                <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                <div class="alert-message">${alert.message}</div>
            `;
            alertsDiv.insertBefore(alertElement, alertsDiv.firstChild);
            
            // Keep only last 50 alerts visible
            while (alertsDiv.children.length > 50) {
                alertsDiv.removeChild(alertsDiv.lastChild);
            }
        }
        
        function updateChart(data) {
            const now = new Date().toLocaleTimeString();
            performanceChart.data.labels.push(now);
            performanceChart.data.datasets[0].data.push(data.cpu_usage);
            performanceChart.data.datasets[1].data.push(data.memory_usage);
            
            // Keep only last 20 data points
            if (performanceChart.data.labels.length > 20) {
                performanceChart.data.labels.shift();
                performanceChart.data.datasets[0].data.shift();
                performanceChart.data.datasets[1].data.shift();
            }
            
            performanceChart.update('none');
        }
        
        // Control functions
        function startWatching() {
            fetch('/api/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'start_watching'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Started watching logs');
                    loadStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            });
        }
        
        function stopWatching() {
            fetch('/api/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'stop_watching'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Stopped watching logs');
                    loadStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            });
        }
        
        function reloadConfig() {
            fetch('/api/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'reload_config'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Configuration reloaded');
                    loadStatus();
                } else {
                    alert('Error: ' + data.message);
                }
            });
        }
        
        function testSpeech() {
            fetch('/api/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'test_speech'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Speech test sent');
                } else {
                    alert('Error: ' + data.message);
                }
            });
        }
        
        function forceDetectLog() {
            fetch('/api/control', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({action: 'force_detect_log'})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Log detection: ' + data.message);
                    // Refresh status to show new current file
                    setTimeout(updateStatus, 1000);
                } else {
                    alert('Log detection failed: ' + data.message);
                }
            });
        }
        
        // Auto-refresh every 5 seconds
        setInterval(loadStatus, 5000);
    </script>
</body>
</html>'''
    
    with open(templates_dir / 'dashboard.html', 'w') as f:
        f.write(dashboard_html)
    
    logger.info("Dashboard templates created successfully")


if __name__ == '__main__':
    # This is for testing the dashboard standalone
    import sys
    from pathlib import Path
    
    # Add the project root to Python path
    sys.path.insert(0, str(Path(__file__).parent))
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Create templates
    create_dashboard_templates()
    
    # Load configuration
    config = Config('config/app.yml')
    
    # Initialize components
    from evetalk.engine import RulesEngine
    from evetalk.watcher import LogWatcher
    from evetalk.parse import LogParser
    from evetalk.notify import SpeechNotifier
    
    # Create log parser
    log_parser = LogParser("config/patterns/core.yml")
    
    # Create speech notifier
    speech_notifier = SpeechNotifier(config)
    
    # Create rules engine
    rules_engine = RulesEngine(config, speech_notifier)
    
    # Create log watcher
    log_watcher = LogWatcher(config, rules_engine)
    
    # Create and run dashboard
    dashboard = WebDashboard(config, rules_engine, log_watcher)
    dashboard.run(debug=True)
