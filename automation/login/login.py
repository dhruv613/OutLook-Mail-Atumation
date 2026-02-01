import time
import os
import datetime
from pyautogui import hotkey  # type: ignore
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from automation.locators import Locators
from automation.login.login_utils import LoginUtils

class Login:
    def __init__(self, driver):
        self.driver = driver
        self.loc = Locators()
        self.utils = LoginUtils(driver)
        self.account_blocked = False

    def outlook_login(self, email, password):
        """Perform Outlook Login Process"""
        # print(f"🔐 Logging in with: {email}")

        try:
            self.driver.get("https://outlook.live.com")

            steps = [
                lambda: self._click_sign_in(),
                lambda: self._enter_email(email),
                lambda: self._click_next(),
                lambda: self._handle_password_selection() or True,  # if this returns, None
                lambda: self._enter_password(password),
                lambda: self._submit_password()    
            ]

            step_names = [
                "Sign In click",
                "Email entry",
                "Next click",
                "Password selection",
                "Password entry",
                "Password submit"
            ]

            for step, name in zip(steps, step_names):
                if not step():
                    print(f"❌ Failed at step: {name}")
                    
                    # --- DEBUGGING FAILURE ---
                    try:
                        timestamp = datetime.datetime.now().strftime("%H_%M_%S")
                        print(f"DEBUG: Failure URL: {self.driver.current_url}")
                        print(f"DEBUG: Failure Title: {self.driver.title}")
                        
                        screenshot_dir = "d:/Mail_AutoMation/logs/screenshots"
                        if not os.path.exists(screenshot_dir):
                            os.makedirs(screenshot_dir)
                            
                        file_name = f"{email}_{name.replace(' ', '_')}_{timestamp}.png"
                        save_path = os.path.join(screenshot_dir, file_name)
                        self.driver.save_screenshot(save_path)
                        print(f"📸 Screenshot saved to: {save_path}")
                        
                        # Save page source for deeper analysis
                        with open(save_path.replace(".png", ".html"), "w", encoding="utf-8") as f:
                            f.write(self.driver.page_source)
                            
                    except Exception as e:
                        print(f"⚠️ Failed to save debug info: {e}")
                    # -------------------------
                    
                    return False

            # Unified Post-Login Handler (Replaces Check Blocked -> Skip -> Yes -> Detect Home)
            if self._handle_post_login(email, password):
                return True
            
            print("❌ Login failed: Home not detected after post-login checks")
            return False

        except Exception as e:
            print("❌ Login Exception:", e)
            return False

    def _click_sign_in(self):
        """Step 1: Click Sign In"""
        try:
            # Optimization: Try direct Link Text first as it's fastest and most common
            # Reducde timeout to 2s for fast check (was 5)
            if self.utils.safe_click(By.LINK_TEXT, "Sign in", timeout=5):
                # print("✅ Clicked 'Sign in' via Link Text")
                return True
            
            locators = self.loc.get_locators("SIGN_IN")
            # print(f"DEBUG: SIGN_IN Locators: {locators}")
            if self.utils.safe_click_any(locators, timeout=10): # Increased per user request
                return True
            # print("⚠️ SIGN_IN via JSON failed.")
            return False
        except Exception as e:
            print(f"⚠️ Error clicking Sign In: {e}")
            return False

    def _enter_email(self, email):
        """Step 2: Enter Email"""
        try:
             # DEBUG: Check if we are actually on a login page
            current_url = self.driver.current_url
            if "live.com" not in current_url and "microsoft.com" not in current_url:
                print(f"⚠️ Warning: _enter_email called on unexpected URL: {current_url}")

            # Try primary locator (using safe_find as before)
            email_field = self.utils.safe_find(By.NAME, "loginfmt") 
            if not email_field:
                 # Try from JSON
                locators = self.loc.get_locators("EMAIL_FIELD")
                for by, val in locators:
                    email_field = self.utils.safe_find(by, val)
                    if email_field: break
            
            if not email_field:
                # Try fallback
                locators = self.loc.get_locators("EMAIL_FIELD_FALLBACK")
                for by, val in locators:
                    email_field = self.utils.safe_find(by, val)
                    if email_field: 
                        break

            if email_field:
                email_field.clear()
                email_field.send_keys(email)
                return True
            return False
        except Exception as e:
            print(f"⚠️ Error entering email: {e}")
            return False

    def _click_next(self):
        """Click Next button"""
        try:
            if self.utils.safe_click_any(self.loc.get_locators("NEXT_BUTTON")):
                return True
            # print("⚠️ NEXT_BUTTON via JSON failed. Using fallback...")
            if self.utils.safe_click_any(self.loc.get_locators("NEXT_BUTTON_FALLBACK")):
                return True
            return False
        except Exception:
            return False

    def _handle_password_selection(self):
        """Step 3: Handle Passkey bypass and 'Use your password' if present"""
        try:
            # 0. Check for Passkey Error / Back Button (User reported issue)
            # The system modal might be blocking, so we try sending ESC first if we suspect it's there?
            # Or just check for the Back button which appears under the modal.
            
            # Check for "Back" button (idBtn_Back) which appears on the passkey error screen
            if self.utils.safe_click_any(self.loc.get_locators("BACK_BUTTON"), timeout=2):
                print("⚠️ Passkey Error screen detected - Clicked 'Back'")
                time.sleep(1)
                
            # Also check for "Sign in another way" link if Back didn't resolve it or wasn't there
            if self.utils.safe_click(By.ID, "idA_PWD_SwitchToCredPicker", timeout=1):
                 print("⚠️ Clicked 'Sign in another way'")
                 time.sleep(1)

            # 1. FIRST: Try to bypass Passkey prompt (Microsoft may show passkey as default)
            if self.utils.safe_click_any(self.loc.get_locators("PASSKEY_BYPASS"), timeout=3):
                # print("Clicked Passkey bypass (Other ways to sign in / Use password)")
                time.sleep(0.2)  # Wait for transition
            
            # 2. Try PRE-Use Password button (The tile/button that leads to password entry)
            if self.utils.safe_click_any(self.loc.get_locators("PRE_USE_PASSWORD"), timeout=3):
                # print("Found PRE-Use Password button - clicking...")
                time.sleep(0.2)  # Wait for animation

            # 3. Try actual 'Use your password' button
            if self.utils.safe_click_any(self.loc.get_locators("USE_PASSWORD"), timeout=3):
                # print("Clicked 'Use your password'")
                return
            
            # 4. Try PASSKEY_BYPASS again (in case it appears after other clicks)
            if self.utils.safe_click_any(self.loc.get_locators("PASSKEY_BYPASS"), timeout=2):
                # print("Clicked Passkey bypass (second attempt)")
                time.sleep(1)
            
            print("No password selection UI present - continuing...")
        except Exception:
            pass

    def _enter_password(self, password, retry=True):
        """Step 4: Enter Password"""
        try:
            # 1. Try to find password field
            locators = self.loc.get_locators("PASSWORD_FIELD")
            for by, val in locators:
                # Use a slightly shorter timeout for the first attempt if we plan to retry
                pw_field = self.utils.safe_find(by, val, timeout=5 if retry else 10)
                if pw_field:
                    pw_field.send_keys(password)
                    return True
            
            # 2. If not found and retry is allowed, check for "Use Password" button
            if retry:
                print("⚠️ Password field not found. Checking for 'Use your password' button...")
                
                # Check for "Use your password" button (e.g. if we are stuck on the choice screen)
                if self.utils.safe_click_any(self.loc.get_locators("USE_PASSWORD"), timeout=2) or \
                   self.utils.safe_click_any(self.loc.get_locators("PRE_USE_PASSWORD"), timeout=2):
                    
                    print("🔄 Clicked 'Use your password' button. Waiting for field...")
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.NAME, "passwd"))
                        )
                    except:
                        print("⚠️ Waited for password field but it didn't appear.")
                    
                    return self._enter_password(password, retry=False)

            return False
        except Exception as e:
            print(f"⚠️ Error entering password: {e}")
            return False

    def _submit_password(self):
        """Step 5: Submit Password"""
        try:
            # print("Password submitted: Using Enter key (user enforced)...")
            # time.sleep(2) # REMOVED for speed
            
            # 1. Re-locate password field to ensure focus and send Enter
            locators = self.loc.get_locators("PASSWORD_FIELD")
            for by, val in locators:
                pw_field = self.utils.safe_find(by, val)
                if pw_field:
                    pw_field.send_keys(Keys.RETURN)
                    return True
            
            # 2. Fallback if field not found
            print("⚠️ Password field not found for Enter. Using hotkey...")
            hotkey('enter')
            return True
        except Exception as e:
            print(f"⚠️ Password submit failed: {e}")
            return False

    # -------------------------------------------------------------------------
    # IMPROVED LOGIN LOGIC (User Requested)
    # -------------------------------------------------------------------------
    def _check_account_blocked(self):
        """Check for EXPLICIT block messages."""
        return self._check_any_locator("BLOCKED_INDICATORS")

    def _login_success(self):
        """Check for explicit success indicators."""
        return self._check_any_locator("LOGIN_SUCCESS_INDICATORS")

    def _handle_post_login(self, email, password, retry_count=0):
        print(f"🔄 Post-Login Check (Retry: {retry_count})...")
        
        # We need to wait for the page to settle.
        # Check iteratively for X seconds.
        end_time = time.time() + 60  # Increased to 60s
        
        while time.time() < end_time:
            # 1. Check for Block FIRST
            if self._check_account_blocked():
                print("❌ Account is EXPLICITLY BLOCKED!")
                self.account_blocked = True
                return False

            # 2. Check for Success
            if self._login_success():
                print("✅ Login Success (Indicator found)")
                return True
            
            # 3. Check for specific interactions (Skip/Yes/Password)
            # Use Password Button - Click it and retry
            if self.utils.safe_click_any(self.loc.get_locators("USE_PASSWORD"), timeout=0.1):
                 # print("⚠️ 'Use your password' detected & Clicked.")
                 if retry_count < 5:  # Increased to 5 retries
                     time.sleep(0.5)
                     self._enter_password(password)
                     self._submit_password()
                     return self._handle_post_login(email, password, retry_count=retry_count + 1)
                 return False

            # Yes / Skip buttons
            if self.utils.safe_click_any(self.loc.get_locators("YES_BUTTON"), timeout=0.1): return True
            if self.utils.safe_click_any(self.loc.get_locators("SKIP_FOR_NOW"), timeout=0.1): return True
            if self.utils.safe_click_any(self.loc.get_locators("SKIP_GENERIC"), timeout=0.1): return True
            
            time.sleep(0.5)

        print("⚠️ Login Timeout: No Block text found, but no Success indicator either.")
        # DO NOT Mark blocked. Just return False (will be treated as NOT_LOGINED/PENDING by handler)
        return False

    def _check_any_locator(self, key, timeout=1):
        """Helper to check if any locator for a key is present."""
        locators = self.loc.get_locators(key)
        for by, val in locators:
            if self.utils.safe_find(by, val, timeout=timeout):
                return True
        return False
