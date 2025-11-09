import os
import sys
import ctypes
import subprocess
from pathlib import Path

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def find_mt5_installation():
    possible_paths = [
        r"C:\Program Files\XM Global MT5",
        r"C:\Program Files\MetaTrader 5",
        r"C:\Program Files (x86)\XM Global MT5",
        r"C:\Program Files (x86)\MetaTrader 5",
        r"C:\Program Files\XM MT5",
        r"C:\Program Files\Exness MT5",
        r"C:\Program Files\FTMO MT5",
    ]
    
    print("SEARCH: Searching for MetaTrader 5 installation...")
    
    for path in possible_paths:
        terminal_path = os.path.join(path, "terminal64.exe")
        if os.path.exists(terminal_path):
            print(f"SUCCESS: Found MT5 at: {path}")
            return path
    
    print("ERROR: MetaTrader 5 not found in standard locations.")
    print("\nNOTE: Please install MT5 from your broker or specify custom path.")
    return None

def create_symlink(source, target):
    if os.path.exists(target):
        if os.path.islink(target):
            print(f"SUCCESS: Symlink already exists: {target}")
            return True
        else:
            print(f"WARNING: Directory exists but is not a symlink: {target}")
            return False
    
    if not is_admin():
        print("ERROR: Administrator privileges required to create symlink")
        print("   Please run the deployment script as Administrator")
        print("   OR use: windows_setup_admin.bat")
        return False
    
    try:
        os.symlink(source, target, target_is_directory=True)
        print(f"SUCCESS: Symlink created: {target} -> {source}")
        return True
    except Exception as e:
        print(f"ERROR: Failed to create symlink: {e}")
        return False

def verify_mt5_connection():
    try:
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            print("WARNING: MT5 initialize failed. Make sure MT5 terminal is installed and logged in.")
            return False
        
        account_info = mt5.account_info()
        if account_info:
            print(f"SUCCESS: MT5 Connected Successfully!")
            print(f"   Account: {account_info.login}")
            print(f"   Balance: ${account_info.balance:.2f}")
            print(f"   Server: {account_info.server}")
        
        mt5.shutdown()
        return True
    except ImportError:
        print("WARNING: MetaTrader5 package not installed. Run: pip install MetaTrader5")
        return False
    except Exception as e:
        print(f"ERROR: MT5 connection error: {e}")
        return False

def main():
    print("="*60)
    print("MT5 AUTO-CONNECTION SETUP")
    print("="*60)
    
    mt5_path = find_mt5_installation()
    
    if not mt5_path:
        print("\nERROR: Setup failed: MT5 installation not found")
        return False
    
    standard_path = r"C:\Program Files\MetaTrader 5"
    
    if mt5_path != standard_path:
        print(f"\nLINK: Creating symlink for Python MT5 package compatibility...")
        if not create_symlink(mt5_path, standard_path):
            print("\nERROR: Setup failed: Could not create symlink")
            return False
    
    print("\nSEARCH: Verifying MT5 connection...")
    if verify_mt5_connection():
        print("\nSUCCESS: MT5 AUTO-SETUP COMPLETE!")
        return True
    else:
        print("\nWARNING: MT5 installed but connection failed.")
        print("   Please make sure MT5 terminal is running and logged in.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
