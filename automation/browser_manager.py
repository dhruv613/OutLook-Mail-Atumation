from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import shutil
import os
import platform


class BrowserManager:
    def __init__(self, browser_name="chrome"):
        """Initialize the browser manager"""
        self.browser_name = browser_name.lower()
        self.driver = None

    # ======================
    # Browser Option Setups
    # ======================
    def _get_chrome_options(self):
        options = ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        return options

    def _get_firefox_options(self):
        options = FirefoxOptions()
        options.set_preference("dom.webnotifications.enabled", False)
        return options

    def _get_edge_options(self):
        options = EdgeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        return options

    def _get_brave_options(self):
        options = ChromeOptions()
        system = platform.system()

        brave_paths = {
            "Windows": [
                r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
                r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe"
            ],
            "Darwin": ["/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"],
            "Linux": ["/usr/bin/brave-browser", "/usr/bin/brave"]
        }

        for path in brave_paths.get(system, []):
            if os.path.exists(path):
                options.binary_location = path
                break

        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        return options

    def _get_opera_options(self):
        options = ChromeOptions()
        system = platform.system()

        opera_paths = {
            "Windows": [
                rf"C:\Users\{os.getlogin()}\AppData\Local\Programs\Opera\opera.exe",
                r"C:\Program Files\Opera\opera.exe"
            ],
            "Darwin": ["/Applications/Opera.app/Contents/MacOS/Opera"],
            "Linux": ["/usr/bin/opera", "/usr/bin/opera-stable"]
        }

        for path in opera_paths.get(system, []):
            if os.path.exists(path):
                options.binary_location = path
                break

        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        return options

    # ======================
    # Browser Configurations
    # ======================
    def _get_browser_config(self):
        return {
            "chrome": {
                "driver": webdriver.Chrome,
                "service": lambda: ChromeService(shutil.which("chromedriver")),
                "options": self._get_chrome_options()
            },
            "firefox": {
                "driver": webdriver.Firefox,
                "service": lambda: FirefoxService(shutil.which("geckodriver")),
                "options": self._get_firefox_options()
            },
            "edge": {
                "driver": webdriver.Edge,
                "service": lambda: EdgeService(shutil.which("msedgedriver")),
                "options": self._get_edge_options()
            },
            "brave": {
                "driver": webdriver.Chrome,
                "service": lambda: ChromeService(shutil.which("chromedriver")),
                "options": self._get_brave_options()
            },
            "opera": {
                "driver": webdriver.Chrome,
                "service": lambda: ChromeService(shutil.which("chromedriver")),
                "options": self._get_opera_options()
            }
        }

    # ======================
    # Public Methods
    # ======================
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
            print(f"✅ {self.browser_name.capitalize()} launched successfully.")
            return self.driver
        except Exception as e:
            print(f"❌ Failed to launch {self.browser_name}: {str(e)}")
            return None

    def close_browser(self):
        """Close the active browser"""
        if self.driver:
            self.driver.quit()
            print(f"🧹 {self.browser_name.capitalize()} closed successfully.")


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
