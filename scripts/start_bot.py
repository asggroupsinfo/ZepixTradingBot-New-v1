"""
Start Bot Server on Port 5000
"""
import uvicorn
import sys
import os

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

if __name__ == "__main__":
    print("=" * 60)
    print("STARTING TRADING BOT SERVER")
    print("=" * 60)
    print("Server will start on: http://localhost:5000")
    print("Webhook endpoint: http://localhost:5000/webhook")
    print("Status endpoint: http://localhost:5000/status")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
            uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=5000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {str(e)}")
        import traceback
        traceback.print_exc()

