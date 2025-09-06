# EVE Copilot Process Management

## 🚀 **New Process Lock System**

The EVE Copilot now has a robust process management system that prevents multiple instances from running simultaneously, eliminating the duplicate voice issue.

## 📋 **Available Scripts**

### 1. **Startup Script (Recommended)**
```bash
# Start in background (recommended)
python start_eve_copilot.py --background

# Start in foreground (for debugging)
python start_eve_copilot.py

# Force kill existing processes and start
python start_eve_copilot.py --force --background

# Use simple monitor instead of realtime
python start_eve_copilot.py --monitor simple --background
```

### 2. **Direct Scripts (with process protection)**
```bash
# Real-time monitor (with process lock)
python realtime_monitor.py --force

# Simple monitor (with process lock)
python simple_monitor.py --force
```

## 🔒 **Process Lock Features**

- **Automatic Detection**: Detects if another instance is already running
- **PID Tracking**: Uses process ID to verify if the process is actually running
- **Stale Lock Cleanup**: Automatically removes lock files from dead processes
- **Force Mode**: `--force` flag kills existing processes before starting
- **Signal Handling**: Graceful cleanup on Ctrl+C or termination signals

## 🛠️ **How It Works**

1. **Lock File**: Creates `eve_copilot.lock` with the process PID
2. **Process Check**: Verifies the PID is actually running using `psutil`
3. **Stale Cleanup**: Removes lock files from dead processes
4. **Force Kill**: `--force` option kills all EVE Copilot processes before starting

## 🚨 **Troubleshooting**

### If you get "already running" error:
```bash
# Option 1: Use force mode
python start_eve_copilot.py --force --background

# Option 2: Manual cleanup
rm -f eve_copilot.lock
pkill -9 -f "realtime_monitor.py"
pkill -9 -f "simple_monitor.py"
```

### If processes are stuck:
```bash
# Kill all EVE Copilot processes
pkill -9 -f "realtime_monitor.py"
pkill -9 -f "simple_monitor.py"
pkill -9 -f "app.py"
rm -f eve_copilot.lock
```

## ✅ **Benefits**

- **No More Duplicate Voices**: Only one instance can run at a time
- **Automatic Cleanup**: Lock files are cleaned up on exit
- **Easy Management**: Simple commands to start/stop/restart
- **Force Mode**: Easy recovery from stuck processes
- **Background Support**: Run in background with `--background`

## 🎮 **Quick Start**

```bash
# Start EVE Copilot (recommended)
python start_eve_copilot.py --background

# Check if running
ps aux | grep realtime_monitor

# Stop EVE Copilot
pkill -f realtime_monitor.py
```

The system is now bulletproof against multiple instances! 🛡️
