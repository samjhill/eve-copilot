#!/usr/bin/env python3
"""
EVE Copilot Startup Script - Safe process management
"""

import sys
import argparse
import subprocess
from process_lock import ProcessLock


def main():
    """Main startup function."""
    parser = argparse.ArgumentParser(description="EVE Copilot Startup Script")
    parser.add_argument("--force", action="store_true", 
                       help="Force kill existing processes and start")
    parser.add_argument("--monitor", choices=["realtime", "simple"], 
                       default="realtime",
                       help="Choose monitor type (default: realtime)")
    parser.add_argument("--background", action="store_true",
                       help="Run in background (nohup)")
    args = parser.parse_args()
    
    print("🚀 EVE Copilot Startup Manager")
    print("=" * 40)
    
    # Check for existing processes
    lock = ProcessLock()
    if lock.lock_file.exists():
        try:
            with open(lock.lock_file, 'r') as f:
                old_pid = int(f.read().strip())
            
            if lock._is_process_running(old_pid):
                if args.force:
                    print(f"🔪 Force mode: Killing existing process (PID: {old_pid})")
                    lock.kill_existing_processes()
                else:
                    print(f"❌ EVE Copilot is already running (PID: {old_pid})")
                    print("   Use --force to kill existing processes")
                    return 1
            else:
                print(f"🧹 Cleaning up stale lock file (old PID: {old_pid})")
                lock.lock_file.unlink()
        except (ValueError, FileNotFoundError):
            lock.lock_file.unlink()
    
    # Choose the monitor script
    if args.monitor == "realtime":
        script = "realtime_monitor.py"
    else:
        script = "simple_monitor.py"
    
    # Build command
    cmd = [sys.executable, script]
    if args.force:
        cmd.append("--force")
    
    print(f"🎮 Starting {script}...")
    print(f"📝 Command: {' '.join(cmd)}")
    
    if args.background:
        print("🔄 Running in background...")
        cmd = ["nohup"] + cmd + [">", "eve_copilot.log", "2>&1", "&"]
        subprocess.run(" ".join(cmd), shell=True)
        print("✅ Started in background. Check eve_copilot.log for output.")
    else:
        print("🎯 Starting in foreground (Ctrl+C to stop)...")
        try:
            subprocess.run(cmd)
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
