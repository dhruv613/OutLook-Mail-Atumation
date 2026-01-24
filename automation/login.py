# login.py
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from automation.locators import Locators


class Login:
    def __init__(self, driver):
        self.driver = driver
        self.loc = Locators()

    def outlook_login(self, email, password):
        """Perform Outlook Login Process"""
        try:
            print(f"🔐 Logging in with: {email}")

            # Open Outlook
            self.driver.get("https://outlook.live.com")
            time.sleep(2)

    # -------------------------------
    # STEP 1: CLICK SIGN IN
    # -------------------------------
            try:
                sign_in_btn = self.loc.find(self.driver, "SIGN_IN")
                sign_in_btn.click()
            except Exception:
                print("⚠️ SIGN_IN via JSON failed. Using LINK_TEXT fallback...")
                fallback = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, "Sign in"))
                )
                fallback.click()

            # Wait for email field
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "loginfmt"))
            )

    # -------------------------------
    # STEP 2: ENTER EMAIL
    # -------------------------------
            try:
                email_field = self.loc.find(self.driver, "EMAIL_FIELD")
                email_field.clear()
                email_field.send_keys(email)
            except Exception:
                print("⚠️ EMAIL_FIELD via JSON failed. Using fallback...")
                fallback_email_field = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.NAME, "loginfmt"))
                )
                fallback_email_field.clear()
                fallback_email_field.send_keys(email)

            time.sleep(1)

            # Click NEXT
            try:
                next_btn = self.loc.find(self.driver, "NEXT_BUTTON")
                next_btn.click()
            except Exception:
                print("⚠️ NEXT_BUTTON via JSON failed. Using fallback...")
                fallback_next = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.ID, "idSIButton9"))
                )
                fallback_next.click()
    # -------------------------------
    # STEP 3: CLICK "USE YOUR PASSWORD" (NEW + OLD)
    # -------------------------------
            try:
                # FIRST: New pre-button before showing password option
                try:
                    pre_btn = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(
                            (By.XPATH, self.loc.locators["PRE_USE_PASSWORD"]["xpath"])
                        )
                    )
                    print("🟦 Found pre-password screen button — clicking...")
                    pre_btn.click()
                    time.sleep(2)
                except TimeoutException:
                    pass  # Not present — skip

                # SECOND: Actual "Use your password"
                use_pass = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, self.loc.locators["USE_PASSWORD"]["xpath"])
                    )
                )
                use_pass.click()
                print("🟦 Clicked 'Use your password'")
                time.sleep(2)

            except Exception:
                print("ℹ️ No 'Use your password' option — continuing...")

    # -------------------------------
    # STEP 4: ENTER PASSWORD
    # -------------------------------
            password_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.NAME, "passwd"))
            )
            password_input.send_keys(password)
            time.sleep(1)

    # -------------------------------
    # STEP 5: SUBMIT PASSWORD (NEXT)
    # -------------------------------
            try:
                final_next = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, '//*[@id="idSIButton9"] | //*[@id="view"]/div/div[5]/button')
                    )
                )
                final_next.click()
            except TimeoutException:
                print("⚠️ Password submit button not found — continuing...")

    # -------------------------------
    # STEP 6: CLICK "YES" ON STAY SIGNED IN
    # -------------------------------
            try:
                final_btn = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='view']/div/div[5]/button[1]"))
                )
                final_btn.click()
                time.sleep(4)
                print(f"✅ Login successful for: {email}")
                return True

            except TimeoutException:
                print("⚠️ 'Yes' button not found — skipping...")
                print(f"✅ Login successful for: {email}")
                return True

        except (NoSuchElementException, TimeoutException, WebDriverException) as e:
            print(f"❌ Login failed for {email}: {e}")
            return False
