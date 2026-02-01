import time
import threading
from automation.locators.Locators import Locators
from automation.login.login_utils import LoginUtils

class BackgroundWatcher:
    def __init__(self, driver):
        self.driver = driver
        self.loc = Locators()
        self.utils = LoginUtils(driver)
        self._stop_event = threading.Event()
        self.premium_detected = False

    def watch_for_premium_alert(self, duration=60):
        """
        Starts a background thread that watches for the PREMIUM button for specific duration.
        """
        self._stop_event.clear()
        self.premium_detected = False
        
        watcher_thread = threading.Thread(target=self._monitor_loop, args=(duration,))
        watcher_thread.daemon = True
        watcher_thread.start()
        return watcher_thread

    def _monitor_loop(self, duration):
        start_time = time.time()
        print(f"👀 Background Watcher Started (Duration: {duration}s)...")
        
        while time.time() - start_time < duration:
            if self._stop_event.is_set():
                break
            
            try:
                # Check for PREMIUM BUTTON
                # Using a very short timeout to minimize blocking the driver
                if self.utils.safe_find_any(self.loc.get_locators("PREMIUM_BUTTON"), timeout=1):
                    print("💰 Premium required — sender exhausted (Detected in Background)")
                    self.premium_detected = True
                    break # Stop watching if found
            except Exception as e:
                # Ignore errors as main thread might be navigating
                pass
            
            time.sleep(2) # Check every 2 seconds
            
        print("👀 Background Watcher Stopped.")

    def stop(self):
        self._stop_event.set()

    def is_premium_required(self):
        return self.premium_detected