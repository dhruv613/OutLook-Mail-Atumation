from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService


from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager


import shutil
import os
import platform


import sys
import os

# Add root directory to sys.path to allow imports when running directly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.config import BROWSER_PATHS, LOGS_DIR

# =============================================
# CACHED DRIVER PATHS - Avoid GitHub rate limits
# =============================================
# Set this to your local geckodriver path to avoid GitHub API calls
# Download from: https://github.com/mozilla/geckodriver/releases
GECKO_DRIVER_PATH = os.path.join(project_root, "drivers", "geckodriver.exe")

def get_geckodriver_path():
    """Get geckodriver path, using local cache if available to avoid GitHub rate limits"""
    if os.path.exists(GECKO_DRIVER_PATH):
        # print(f"✅ Using cached geckodriver: {GECKO_DRIVER_PATH}")
        return GECKO_DRIVER_PATH
    else:
        print("⚠️ No local geckodriver found, downloading via webdriver-manager...")
        try:
            path = GeckoDriverManager().install()
            # Cache it for future use
            os.makedirs(os.path.dirname(GECKO_DRIVER_PATH), exist_ok=True)
            shutil.copy(path, GECKO_DRIVER_PATH)
            print(f"✅ Cached geckodriver to: {GECKO_DRIVER_PATH}")
            return path
        except Exception as e:
            print(f"❌ Failed to download geckodriver: {e}")
            raise

class BrowserManager:
    def __init__(self, browser_name="firefox", headless=False, detach=False, incognito=False, instance_id=0):
        """
        Initialize the browser manager
        :param browser_name: Name of the browser (chrome, firefox, edge, etc.)
        :param headless: Run in headless mode (no UI)
        :param detach: Keep browser open after script ends (Chrome/Edge only)
        :param incognito: Run in incognito/private mode
        """
        self.browser_name = browser_name.lower()
        self.headless = headless
        self.detach = detach
        self.incognito = incognito
        self.instance_id = instance_id
        self.driver = None

    # ======================
    # Browser Option Setups
    # ======================


    def _find_browser_path(self, browser_key):
        """Helper to find first existing path for a browser from config"""
        paths = BROWSER_PATHS.get(browser_key, [])
        for path in paths:
            if os.path.exists(path):
                return path
        return None

    def _get_firefox_options(self, unique_profile=True):
        instance_id = self.instance_id
        options = FirefoxOptions()
        # Find path from config
        binary_path = self._find_browser_path("firefox")
        if binary_path:
             options.binary_location = binary_path
        
        # Create unique temp profile to avoid conflicts with multiple instances
        if unique_profile:
            import tempfile
            temp_profile = tempfile.mkdtemp(prefix=f"firefox_profile_{instance_id}_")
            options.add_argument("-profile")
            options.add_argument(temp_profile)
            # print(f"Created temp Firefox profile: {temp_profile}")
        
        # Disable notifications and other popups
        options.set_preference("dom.webnotifications.enabled", False)
        options.set_preference("dom.push.enabled", False)
        options.set_preference("geo.enabled", False)
        
        # WebRTC Leak Prevention (IMPORTANT for proxy usage)
        options.set_preference("media.peerconnection.enabled", False)
        options.set_preference("media.navigator.enabled", False)
        
        # Memory optimization for multiple instances
        options.set_preference("browser.cache.disk.enable", False)
        options.set_preference("browser.cache.memory.enable", True)
        options.set_preference("browser.sessionhistory.max_entries", 5)
        
        # Proxy support (loaded from proxy_config.py)
        try:
            from utils.proxy_config import get_proxy_for_instance, USE_PROXIES
            if USE_PROXIES:
                proxy = get_proxy_for_instance(instance_id)
                if proxy:
                    if isinstance(proxy, str):
                        # Simple proxy format: "ip:port"
                        options.set_preference("network.proxy.type", 1)
                        ip, port = proxy.split(":")
                        options.set_preference("network.proxy.http", ip)
                        options.set_preference("network.proxy.http_port", int(port))
                        options.set_preference("network.proxy.ssl", ip)
                        options.set_preference("network.proxy.ssl_port", int(port))
                        # print(f"Proxy configured for instance {instance_id}: {proxy}")
                    elif isinstance(proxy, dict):
                        # Authenticated proxy - will be handled by selenium-wire
                        # print(f"Authenticated proxy configured for instance {instance_id}")
                        pass
        except ImportError:
            pass  # proxy_config not found, continue without proxy

        if self.detach:
            options.add_experimental_option("detach", True)
            
        return options

    # ======================
    # Browser Configurations
    # ======================
    def _get_browser_config(self):
        return {

            "firefox": {
                "driver": webdriver.Firefox,
                "service": lambda: FirefoxService(
                    executable_path=get_geckodriver_path(),
                    log_output=os.path.join(LOGS_DIR, f"geckodriver_{self.instance_id}.log")
                ),
                "options": self._get_firefox_options()
            }

        }

    # ======================
    # Public Methods
    # ======================
    def detect_available_browsers(self):
        """
        Detect which browsers are installed on the system (Chrome, Firefox, Brave, etc.).
        Returns a list of available browser names.
        """
        available = []
        
        # Generic check using config paths
        for browser_key in ["chrome", "firefox", "brave", "vivaldi"]:
            if self._find_browser_path(browser_key):
                available.append(browser_key)
                
        # print(f"🌍 Detected Browsers: {available}")
        return available

    def launch_browser(self):
        """Launch the browser and return driver instance"""
        config_map = self._get_browser_config()

        if self.browser_name not in config_map:
            raise ValueError(f"Unsupported browser: {self.browser_name}")

        config = config_map[self.browser_name]

        try:
            service = config["service"]()
            self.driver = config["driver"](service=service, options=config["options"])
            if self.browser_name == "firefox":
                self.driver.maximize_window()
            
            # Anti-Detection: Hide navigator.webdriver for Chromium browsers
            if self.browser_name in ["chrome", "brave", "vivaldi"]:
                try:
                    self.driver.execute_cdp_cmd(
                        "Page.addScriptToEvaluateOnNewDocument",
                        {
                            "source": """
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            });
                            """
                        },
                    )
                    # print(f"🕵️ Automation detection hidden for {self.browser_name}.")
                except Exception as cdp_error:
                    print(f"⚠️ Failed to hide automation detection: {cdp_error}")

            # print(f"✅ {self.browser_name.capitalize()} launched successfully.")
            return self.driver
        except Exception as e:
            print(f"❌ Failed to launch {self.browser_name}: {str(e)}")
            return None

    def close_browser(self):
        """Close the active browser"""
        if self.driver:
            try:
                self.driver.quit()
                # print(f"🧹 {self.browser_name.capitalize()} closed successfully.")
            except:
                pass


# ======================
# Example Usage (only for testing)
# ======================
if __name__ == "__main__":
    manager = BrowserManager("chrome")
    driver = manager.launch_browser()
    if driver:
        driver.get("https://www.google.com")
        input("Press Enter to close browser...")
        manager.close_browser()
