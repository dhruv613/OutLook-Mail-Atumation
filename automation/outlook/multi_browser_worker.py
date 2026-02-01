import threading
import time
from automation.outlook.browser_manager import BrowserManager
from automation.outlook.outlook_handler import OutlookHandler
from utils.config import SENDER_EXCEL_PATH

class MultiBrowserWorker(threading.Thread):
    def __init__(self, browser_name, queue, worker_id, is_retry=False):
        super().__init__()
        self.browser_name = browser_name
        self.queue = queue # List of row numbers
        self.worker_id = worker_id
        self.is_retry = is_retry
        self.failed_rows = [] # Track what failed in this worker

    def run(self):
        prefix = f"[Worker-{self.worker_id} ({self.browser_name})]"
        # print(f"{prefix} 🚀 Starting with {len(self.queue)} accounts...")

        mgr = None
        driver = None

        # Helper to launch browser
        def launch():
            nonlocal mgr, driver
            try:
                if mgr: mgr.close_browser()
            except: pass
            
            mgr = BrowserManager(browser_name=self.browser_name, incognito=True, instance_id=self.worker_id)
            driver = mgr.launch_browser()
            return driver

        # 3. Process Queue
        for row in self.queue:
            # Always launch fresh browser to prevent session bleeding
            try:
                launch()
            except Exception as e:
                print(f"{prefix} ❌ Failed to launch browser for Row {row}. Skipping. Error: {e}")
                continue

            if not driver:
                print(f"{prefix} ❌ Driver unavailable for Row {row}. Skipping.")
                continue

            try:
                handler = OutlookHandler(driver, SENDER_EXCEL_PATH)
                success = handler.process_account(row)
                
                if not success:
                    if self.is_retry:
                            # Re-read status to check if it wasn't blocked (if blocked, it's already marked blocked)
                            handler.excel.mark_sender_failed(row)
                            print(f"{prefix} ❌ Retry failed for Row {row} → Marked FAILED.")
                
                # Small delay between accounts
                time.sleep(2)

            except Exception as e:
                print(f"{prefix} 💥 Crash on Row {row}: {e}")
                # Force restart on crash
                launch()
        
        # Cleanup at end
        if mgr:
            mgr.close_browser()
        # print(f"{prefix} 🏁 Finished Queue.")
