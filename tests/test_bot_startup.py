"""Test Bot Startup"""
import sys
import os

# Set UTF-8 encoding
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# Change to project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Testing bot imports...")
try:
    from src.config import Config
    print("✓ Config imported")
    
    from src.models import Alert
    print("✓ Models imported")
    
    from src.core.trading_engine import TradingEngine
    print("✓ TradingEngine imported")
    
    from src.main import app
    print("✓ FastAPI app imported")
    
    print("\n✓ All imports successful!")
    print("\nStarting bot server...")
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
    
except Exception as e:
    print(f"\n✗ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

