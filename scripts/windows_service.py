import win32serviceutil
import win32service
import win32event
import subprocess
import os

class TradingBotService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ZepixTradingBot"
    _svc_display_name_ = "Zepix Trading Bot Service"
    _svc_description_ = "Automated trading bot with MT5 integration"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        os.chdir("E:\\ZepixTrandingbot-New")
        subprocess.call(["venv\\Scripts\\python.exe", "src/main.py", "--host", "0.0.0.0", "--port", "80"])