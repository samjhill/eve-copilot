#!/usr/bin/env python3
"""
Process Lock Manager - Prevents multiple instances of EVE Copilot from running
"""

import os
import sys
import time
import signal
import atexit
from pathlib import Path
import psutil


class ProcessLock:
    """Manages process locking to prevent multiple instances."""
    
    def __init__(self, lock_file_path="eve_copilot.lock"):
        self.lock_file = Path(lock_file_path)
        self.pid = os.getpid()
        self.locked = False
        
        # Register cleanup function
        atexit.register(self.cleanup)
        
        # Handle signals for graceful cleanup
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle termination signals."""
        print(f"\n🛑 Received signal {signum}, cleaning up...")
        self.cleanup()
        sys.exit(0)
    
    def acquire(self):
        """Acquire the process lock."""
        if self.locked:
            return True
            
        # Check if lock file exists
        if self.lock_file.exists():
            try:
                # Read the PID from lock file
                with open(self.lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Check if the process is still running
                if self._is_process_running(old_pid):
                    print(f"❌ EVE Copilot is already running (PID: {old_pid})")
                    print("   Please stop the existing process first or wait for it to finish.")
                    return False
                else:
                    # Process is dead, remove stale lock file
                    print(f"🧹 Removing stale lock file (old PID: {old_pid})")
                    self.lock_file.unlink()
            except (ValueError, FileNotFoundError):
                # Invalid lock file, remove it
                self.lock_file.unlink()
        
        # Create new lock file
        try:
            with open(self.lock_file, 'w') as f:
                f.write(str(self.pid))
            self.locked = True
            print(f"🔒 Process lock acquired (PID: {self.pid})")
            return True
        except Exception as e:
            print(f"❌ Failed to acquire lock: {e}")
            return False
    
    def _is_process_running(self, pid):
        """Check if a process with given PID is running."""
        try:
            return psutil.pid_exists(pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def release(self):
        """Release the process lock."""
        if self.locked and self.lock_file.exists():
            try:
                # Verify we own the lock file
                with open(self.lock_file, 'r') as f:
                    lock_pid = int(f.read().strip())
                
                if lock_pid == self.pid:
                    self.lock_file.unlink()
                    print(f"🔓 Process lock released (PID: {self.pid})")
                else:
                    print(f"⚠️  Lock file owned by different process (PID: {lock_pid})")
            except (ValueError, FileNotFoundError):
                pass
            finally:
                self.locked = False
    
    def cleanup(self):
        """Clean up the lock file on exit."""
        self.release()
    
    def kill_existing_processes(self):
        """Kill any existing EVE Copilot processes."""
        killed_count = 0
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if ('realtime_monitor.py' in cmdline or 
                    'simple_monitor.py' in cmdline or
                    'app.py' in cmdline):
                    print(f"🔪 Killing existing process: PID {proc.info['pid']} - {cmdline}")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        if killed_count > 0:
            print(f"✅ Killed {killed_count} existing EVE Copilot process(es)")
            time.sleep(2)  # Give processes time to die
        else:
            print("✅ No existing EVE Copilot processes found")
        
        return killed_count


def ensure_single_instance(force_kill=False):
    """Ensure only one instance of EVE Copilot is running."""
    lock = ProcessLock()
    
    if force_kill:
        print("🔄 Force mode: Killing existing processes...")
        lock.kill_existing_processes()
    
    if not lock.acquire():
        if not force_kill:
            print("\n💡 To force start (kill existing processes), run with --force flag")
        return None
    
    return lock


if __name__ == "__main__":
    # Test the lock system
    import argparse
    
    parser = argparse.ArgumentParser(description="EVE Copilot Process Lock Test")
    parser.add_argument("--force", action="store_true", help="Force kill existing processes")
    args = parser.parse_args()
    
    lock = ensure_single_instance(force_kill=args.force)
    if lock:
        print("✅ Lock acquired successfully!")
        print("Press Ctrl+C to test cleanup...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Interrupted, testing cleanup...")
    else:
        print("❌ Failed to acquire lock")
        sys.exit(1)
