#!/usr/bin/env python3
"""
Lablr Startup Script

This script helps you start all the necessary services for the Lablr system:
- Redis server (if not already running)
- Celery worker
- FastAPI application

Usage:
    python start_lablr.py [--dev]
    
Options:
    --dev    Start in development mode with auto-reload
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path
from typing import List, Optional
import argparse
import psutil

class LablrLauncher:
    """Launch and manage Lablr services."""
    
    def __init__(self, development_mode: bool = False):
        self.development_mode = development_mode
        self.processes: List[subprocess.Popen] = []
        self.project_root = Path(__file__).parent
        
    def check_redis(self) -> bool:
        """Check if Redis is running."""
        try:
            # Try to connect to Redis on default port
            import redis
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            r.ping()
            return True
        except:
            return False
    
    def check_requirements(self) -> bool:
        """Check if all requirements are met."""
        print("🔍 Checking system requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return False
        print("✅ Python version OK")
        
        # Check if Redis is running
        if not self.check_redis():
            print("❌ Redis not running. Please start Redis server:")
            print("   - On Windows: Install Redis and run 'redis-server'")
            print("   - On macOS: brew install redis && redis-server")
            print("   - On Linux: sudo systemctl start redis")
            return False
        print("✅ Redis is running")
        
        # Check environment variables
        required_vars = [
            'AZURE_FORM_RECOGNIZER_ENDPOINT',
            'AZURE_FORM_RECOGNIZER_KEY'
        ]
        
        openai_vars = [
            'AZURE_OPENAI_ENDPOINT',
            'AZURE_OPENAI_KEY'
        ]
        
        # Check Azure services
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        # Check OpenAI (either new or legacy naming)
        has_openai = all(os.getenv(var) for var in openai_vars)
        has_cognitive = all(os.getenv(var) for var in ['AZURE_COGNITIVE_SERVICES_ENDPOINT', 'AZURE_COGNITIVE_SERVICES_KEY'])
        
        if not (has_openai or has_cognitive):
            missing_vars.extend(openai_vars)
        
        if missing_vars:
            print("❌ Missing environment variables:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\n💡 Copy env.template to .env and fill in your Azure credentials")
            return False
        
        print("✅ Environment variables configured")
        return True
    
    def start_celery_worker(self):
        """Start Celery worker."""
        print("🚀 Starting Celery worker...")
        
        cmd = [
            sys.executable, "-m", "celery",
            "-A", "src.workers.celery_app",
            "worker",
            "--loglevel=info"
        ]
        
        if self.development_mode:
            cmd.extend(["--reload"])
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.processes.append(process)
            print("✅ Celery worker started")
            return process
        except Exception as e:
            print(f"❌ Failed to start Celery worker: {e}")
            return None
    
    def start_api_server(self):
        """Start FastAPI server."""
        print("🚀 Starting API server...")
        
        if self.development_mode:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "src.api.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ]
        else:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "src.api.main:app",
                "--host", "0.0.0.0",
                "--port", "8000"
            ]
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self.processes.append(process)
            print("✅ API server started")
            return process
        except Exception as e:
            print(f"❌ Failed to start API server: {e}")
            return None
    
    def create_directories(self):
        """Create necessary directories."""
        directories = ['uploads', 'outputs', 'logs']
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def start_all(self):
        """Start all services."""
        print("🎯 Starting Lablr PDF Data Labeling System...")
        print("=" * 50)
        
        if not self.check_requirements():
            print("\n❌ Requirements check failed. Please fix the issues above.")
            return False
        
        # Create necessary directories
        self.create_directories()
        
        # Start Celery worker
        celery_process = self.start_celery_worker()
        if not celery_process:
            return False
        
        # Give Celery a moment to start
        time.sleep(3)
        
        # Start API server
        api_process = self.start_api_server()
        if not api_process:
            self.stop_all()
            return False
        
        # Give API server a moment to start
        time.sleep(2)
        
        print("\n🎉 Lablr is now running!")
        print("=" * 50)
        print("📍 API Server: http://localhost:8000")
        print("📋 API Documentation: http://localhost:8000/docs")
        print("📊 Health Check: http://localhost:8000/health")
        print("\n💡 Press Ctrl+C to stop all services")
        print("=" * 50)
        
        return True
    
    def stop_all(self):
        """Stop all running processes."""
        print("\n🛑 Stopping all services...")
        
        for process in self.processes:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                print(f"Error stopping process: {e}")
        
        self.processes.clear()
        print("✅ All services stopped")
    
    def monitor_processes(self):
        """Monitor running processes and handle shutdown."""
        try:
            while True:
                # Check if all processes are still running
                running_processes = [p for p in self.processes if p.poll() is None]
                
                if len(running_processes) != len(self.processes):
                    print("⚠️  Some processes have stopped unexpectedly")
                    break
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested...")
        finally:
            self.stop_all()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Start Lablr PDF Data Labeling System")
    parser.add_argument(
        "--dev", 
        action="store_true", 
        help="Start in development mode with auto-reload"
    )
    
    args = parser.parse_args()
    
    launcher = LablrLauncher(development_mode=args.dev)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 Received shutdown signal...")
        launcher.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if launcher.start_all():
        launcher.monitor_processes()
    else:
        print("❌ Failed to start Lablr system")
        sys.exit(1)

if __name__ == "__main__":
    main() 