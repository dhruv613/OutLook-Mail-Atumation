from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

class LoginUtils:
    def __init__(self, driver):
        self.driver = driver

    def wait_for_loading_screen(self, timeout=10):
        """Wait for any loading screen to disappear."""
        try:
            # Wait for loadingScreen to become invisible
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.ID, "loadingScreen"))
            )
        except:
            pass  # No loading screen or already gone
        
        # Small extra wait for stability
        time.sleep(0.1)

    def wait_and_click(self, locator_tuple, timeout=10):
        """
        Robust Click: Wait -> Scroll -> JS Click -> Discard.
        Args:
            locator_tuple: (By.ID, "id") or (By.XPATH, "//...")
            timeout: seconds to wait
        """
        try:
            self.wait_for_loading_screen(2)
            
            # 1. Wait for presence
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located(locator_tuple))
            
            # 2. Scroll into view (handled by JS usually, but good to ensure)
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # 3. JS Click (Most reliable - bypasses overlays)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except Exception:
            return False

    def wait_and_send_keys(self, locator_tuple, text, timeout=10):
        """Robust Send Keys: Wait -> Clear -> Type"""
        try:
            self.wait_for_loading_screen(2)
            
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located(locator_tuple))
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            
            # Use JS to focus
            self.driver.execute_script("arguments[0].focus();", element)
            element.clear()
            element.send_keys(text)
            return True
        except Exception:
            return False

    def safe_find(self, by, value, timeout=10):
        """Safely find an element with a timeout."""
        try:
            self.wait_for_loading_screen(2)
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            return None

    def safe_click(self, by, value, timeout=10):
        """Safely click using JS click first (bypasses overlays)."""
        import threading
        t_name = threading.current_thread().name
        
        try:
            self.wait_for_loading_screen(3) # Re-enabled to prevent loadingScreen interception
            
            # Wait for element presence
            # print(f"[{t_name}] Waiting for click: ({by}, {value}) T={timeout}s")
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.1)
            
            # Use JS click directly (bypasses overlays like dialogs, loading screens)
            self.driver.execute_script("arguments[0].click();", element)
            # print(f"[{t_name}] JS Click executed on ({by}, {value})")
            return True
            
        except TimeoutException:
            # print(f"[{t_name}] Timeout waiting for ({by}, {value})")
            return False
        except Exception as e:
            # Fallback: try regular click
            try:
                print(f"[{t_name}] JS Click failed ({e}), trying standard click...")
                element = self.driver.find_element(by, value)
                element.click()
                return True
            except Exception as ex:
                print(f"[{t_name}] Standard click also failed: {ex}")
                return False

    def safe_click_any(self, locators, timeout=10):
        """Try to click using a list of locator tuples until one works."""
        import threading
        t_name = threading.current_thread().name
        # print(f"[{t_name}] DEBUG: safe_click_any searching among {len(locators)} locators...")

        for i, (by, value) in enumerate(locators):
            # print(f"[{t_name}]   Checking locator {i+1}: ({by}, {value})")
            if self.safe_click(by, value, timeout=timeout):
                # print(f"[{t_name}]   ✅ Loc {i+1} Clicked: ({by}, {value})")
                return True
        
        # print(f"[{t_name}] ❌ safe_click_any failed to click any.")
        return False

    def safe_find_any(self, locators, timeout=10):
        """Try to find an element using a list of locator tuples until one is found."""
        for by, value in locators:
            element = self.safe_find(by, value, timeout=timeout)
            if element:
                return element
        return None

    def js_click_element(self, element):
        """Click an element using JavaScript (bypasses overlays)."""
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            self.driver.execute_script("arguments[0].click();", element)
            return True
        except:
            return False
