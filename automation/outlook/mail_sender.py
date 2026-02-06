import random
import time
import json
import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from automation.locators import Locators
from automation.login.login_utils import LoginUtils
from automation.content.content_manager import ContentManager
from automation.data.recipient_manager import RecipientManager

import win32clipboard
import win32con


class MailSender:
    def __init__(self, driver, sender_excel_mgr=None, sender_row=None, current_email=None):
        self.driver = driver
        self.sender_excel_mgr = sender_excel_mgr
        self.sender_row = sender_row
        self.current_email = current_email

        self.loc = Locators()
        self.utils = LoginUtils(driver)
        self.content_mgr = ContentManager("c:/Users/ASUS/Desktop/Mail_AutoMation")
        self.recipient_mgr = RecipientManager(
            "c:/Users/ASUS/Desktop/Mail_AutoMation/data/recipient_list.xlsx"
        )

        self.to_email_id = "zoedebtcollector@gmail.com"

    # ---------------------------------------------------------
    # SAFETY CHECK
    # ---------------------------------------------------------
    def _is_driver_alive(self):
        try:
            _ = self.driver.current_url
            return True
        except:
            return False

    def _safe_action(self):
        if not self._is_driver_alive():
            raise RuntimeError("Driver died mid-session")

    # ---------------------------------------------------------
    # CLIPBOARD
    # ---------------------------------------------------------
    _clipboard_lock = threading.Lock()

    def _copy_to_clipboard(self, text):
        with self._clipboard_lock:
            try:
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
            except Exception as e:
                print(f"⚠️ Clipboard error: {e}")
            finally:
                try:
                    win32clipboard.CloseClipboard()
                except:
                    pass

    # ---------------------------------------------------------
    # HELPER: Robust Find with Retry & JS Fallback
    # ---------------------------------------------------------
    def _retry_find(self, key, js_fallback=None, timeout=1.0, retries=5):
        """
        Try to find an element using strategies in locators.json.
        If it fails, retry 'retries' times. 
        If still fails, try the provided js_fallback script.
        """
        for i in range(retries):
            element = self.utils.safe_find_any(self.loc.get_locators(key), timeout=timeout)
            if element:
                return element
            # print(f"⚠️ {key} not found (Attempt {i+1}/{retries})...")

        
        # JS Fallback
        if js_fallback:
            print(f"⚠️ {key} standard locators failed. Trying JS fallback...")
            try:
                # Assuming fallback returns the element or null
                element = self.driver.execute_script(js_fallback)
                if element:
                    print(f"✅ {key} found via JS Fallback!")
                    return element
            except Exception as e:
                print(f"❌ JS Fallback error for {key}: {e}")
        
        return None

    # ---------------------------------------------------------
    # EXPLICIT RECIPIENT FILLER (TO / BCC)
    # ---------------------------------------------------------
    def _handle_unexpected_modal(self):
        """Check for 'Add recipients' modal and close it if found."""
        try:
            # Short timeout to check for modal
            modal = self.utils.safe_find_any(self.loc.get_locators("ADD_RECIPIENTS_MODAL"), timeout=1.5)
            if modal:
                print("⚠️ 'Add recipients' modal detected - Closing it...")
                if self.utils.safe_click_any(self.loc.get_locators("ADD_RECIPIENTS_CANCEL"), timeout=2):

                    return True
                
                # Fallback to ESC
                print("⚠️ Cancel button failed, trying ESC...")
                actions = ActionChains(self.driver)
                actions.send_keys(Keys.ESCAPE)
                actions.perform()
        except Exception as e:
            print(f"⚠️ Modal handler warning: {e}")

    def _fill_to_field(self, email):
        try:
            # Check for pesky modal first
            self._handle_unexpected_modal()

            # Retry with JS Fallback
            js_script = f"return document.querySelector({json.dumps(self.loc.get_js('TO_FIELD_JS'))});"
            to_input = self._retry_find("TO_FIELD", js_fallback=js_script, timeout=1.0, retries=5)

            if not to_input:
                print("❌ TO field not found")
                return False

            self.driver.execute_script("arguments[0].focus();", to_input)
            
            # Robust Click
            try:
                to_input.click()
            except Exception:
                print("⚠️ Title intercept/Loading screen detected - forcing JS click (TO)")
                self.driver.execute_script("arguments[0].click();", to_input)

            self._copy_to_clipboard(email)
            
            
            
            to_input.send_keys(Keys.CONTROL, "v")
            # time.sleep(0.5) # REMOVED for speed
            to_input.send_keys(Keys.ENTER)  # chip creation

            return True
            
        except Exception as e:
            print(f"❌ TO_FIELD failed: {e}")
            return False

    def _fill_bcc_field(self, bcc_list):
        try:
            # 1. OPTIMIZATION: Instant JS Check for BCC field visibility
            js_is_visible = f"""
                var bcc = document.querySelector({json.dumps(self.loc.get_js('BCC_FIELD_JS'))});
                return bcc && bcc.offsetParent !== null;
            """
            is_visible = self.driver.execute_script(js_is_visible)
            
            if not is_visible:
                # 2. Only click if not visible
                if not self.utils.safe_click_any(self.loc.get_locators("BCC_BUTTON"), timeout=5):
                     # Try JS click on button if standard fails?
                    pass

            self._handle_unexpected_modal()

            # Retry with JS Fallback
            js_script = f"return document.querySelector({json.dumps(self.loc.get_js('BCC_FIELD_JS'))});"
            bcc_input = self._retry_find("BCC_FIELD", js_fallback=js_script, timeout=1.0, retries=5)

            if not bcc_input:
                print("❌ BCC field not found")
                return False

            self.driver.execute_script("arguments[0].focus();", bcc_input)
            
            try:
                bcc_input.click()
            except Exception:
                print("⚠️ Intercept detected - forcing JS click (BCC)")
                self.driver.execute_script("arguments[0].click();", bcc_input)

            emails = "\n".join(bcc_list)
            self._copy_to_clipboard(emails)
            bcc_input.send_keys(Keys.CONTROL, "v")
            # time.sleep(0.5) # REMOVED for speed
            bcc_input.send_keys(Keys.ENTER)

            return True
        except Exception as e:
            print(f"❌ BCC_FIELD failed: {e}")
            return False

    # ---------------------------------------------------------
    # COMPOSE + SEND
    # ---------------------------------------------------------
    def _compose_and_send(self, to_email, bcc_list, subject, body, check_limit=True):
        self._safe_action()
        # NEW MAIL
        if not self.utils.safe_click_any(self.loc.get_locators("NEW_MAIL"), timeout=0.3):
            print("⚠️ New Mail button not found. Using fallback hotkey 'n'...")
            try:
                actions = ActionChains(self.driver)
                actions.send_keys("n")
                actions.perform()
                # Smart wait
                self.utils.safe_find_any(self.loc.get_locators("TO_FIELD"), timeout=5)
            except Exception as e:
                print(f"❌ Hotkey 'n' failed: {e}")
                return False
        # else:
            #  time.sleep(0.5) # REMOVED for speed

        # TO
        if not self._fill_to_field(to_email):
            return False

        # BCC
        if not self._fill_bcc_field(bcc_list):
            return False

        # SUBJECT
        js_subj = f"return document.querySelector({json.dumps(self.loc.get_js('SUBJECT_FIELD_JS'))});"
        subject_input = self._retry_find("SUBJECT_FIELD", js_fallback=js_subj, retries=2)
        
        if not subject_input:
            print("❌ Subject field missing")
            return False

        try:
            subject_input.click()
        except Exception:
            print("⚠️ Subject intercept - forcing JS click")
            self.driver.execute_script("arguments[0].click();", subject_input)

        subject_input.send_keys(Keys.CONTROL, "a", Keys.DELETE)
        self._copy_to_clipboard(subject)
        subject_input.send_keys(Keys.CONTROL, "v", Keys.TAB)

        # BODY
        js_body = f"return document.querySelector({json.dumps(self.loc.get_js('BODY_FIELD_JS'))});"
        body_input = self._retry_find("BODY_FIELD", js_fallback=js_body, retries=2)

        if not body_input:
            print("❌ Body field missing")
            return False

        try:
            body_input.click()
        except Exception:
            print("⚠️ Body intercept - forcing JS click")
            self.driver.execute_script("arguments[0].click();", body_input)
            
        self._copy_to_clipboard(body)
        body_input.send_keys(Keys.CONTROL, "v")
        # time.sleep(0.5) # REMOVED for speed

        # SEND
        if not self.utils.safe_click_any(self.loc.get_locators("SEND_BUTTON"), timeout=10):
            print("❌ Send button missing")
            return False
        
        
        self._safe_action()

        # --- OPTIMIZATION: Smart Wait for Compose Dialog to Vanish ---
        try:
            # We use the FIRST strategy from the list (CSS) which is handled by get_locators
            dialog_strategies = self.loc.get_locators("COMPOSE_DIALOG")
            # We only need one valid strategy for WebDriverWait
            # dialog_strategies returns list of (By, value)
            if dialog_strategies:
                WebDriverWait(self.driver, 8).until(
                    EC.invisibility_of_element_located(dialog_strategies[0])
                )
                # print("✅ Compose dialog closed.")
        except Exception:
            # Compose still open -> send probably failed
            print("⚠️ Compose dialog still open after Send (possible failure)")

        # --- DAILY LIMIT CHECK (Once) ---
        # User Logic: Check once after send, but only for first 3 emails (controlled by check_limit arg)
        if check_limit:
            # print("🔍 checking limit reached (Once)...")
            if self._check_daily_limit():
                print("🛑 Daily Limit Reached detected!")
                return "LIMIT_REACHED"
        
        # Check for "Couldn't send this message" alert (Always check strictly? or also skip? keeping it for safety)
        if self.utils.safe_find_any(self.loc.get_locators("SEND_FAILURE_ALERT"), timeout=1):
            print("🛑 Send Failure Alert detected!")
            return "ALERT_FAILED"
                
        return True

    def _check_daily_limit(self):
        """Check if 'Daily limit reached' message is visible."""
        try:
            msg = self.utils.safe_find_any(self.loc.get_locators("DAILY_LIMIT_REACHED"), timeout=2)
            if msg:
                return True
        except:
            pass
        return False

    # ---------------------------------------------------------
    # MAIN LOOP
    # ---------------------------------------------------------
    def send_process(self, start_round=1):
        count_to_send = random.randint(18, 20)
        print(f"📧 Sending {count_to_send} emails")
        
        sent_count_session = 0

        for i in range(start_round, count_to_send + 1):
            if not self._is_driver_alive():
                print("💀 Driver is dead. Exiting sender cleanly.")
                return False, sent_count_session

            print(f"--- 📨 Email {i}/{count_to_send} ---")
            
            # 0. Pre-Email Limit Check REMOVED (User Request: Single check post-send)
            # should_check_limit = (sent_count_session < 3)
            # if should_check_limit ... REMOVED

            bcc_list, rows = self.recipient_mgr.get_batch_recipients(
                random.randint(40, 45), self.sender_row or 0
            )

            if not bcc_list:
                return False, sent_count_session

            subject = self.content_mgr.get_random_subject()
            body = self.content_mgr.get_random_body()

            result = self._compose_and_send(self.to_email_id, bcc_list, subject, body, check_limit=True)

            # LIMIT REACHED HANDLING
            if result == "LIMIT_REACHED":
                print(f"🛑 limit reached for {self.current_email} -> Marking USED-L")
                if self.sender_excel_mgr:
                     self.sender_excel_mgr.update_status(self.sender_row, "USED-L")
                self.recipient_mgr.update_batch_status(rows, None) 
                return False, sent_count_session

            # ALERT FAILED HANDLING
            if result == "ALERT_FAILED":
                print(f"🛑 Send Failure Alert for {self.current_email} -> Marking USED-L (Alert Detected)")
                if self.sender_excel_mgr:
                     # User requested "Send Failure Alert" be treated as Daily Limit (USED-L)
                     self.sender_excel_mgr.update_status(self.sender_row, "USED-L")
                self.recipient_mgr.update_batch_status(rows, None)
                return False, sent_count_session

            if not result:
                print("❌ Compose/Send failed.")
                # PARTIAL SUCCESS CHECK (USED-R)
                if sent_count_session > 0:
                    print(f"⚠️ Partial success ({sent_count_session} sent). Marking USED-R.")
                    if self.sender_excel_mgr:
                        self.sender_excel_mgr.mark_sender_used_reuse(self.sender_row, sent_count_session)
                else:
                    print(f"⚠️ Failed completely (0 sent).")

                self.recipient_mgr.update_batch_status(rows, None)
                return False, sent_count_session

            # Success
            self.recipient_mgr.update_batch_status(rows, "USED")
            sent_count_session += 1
            # time.sleep(random.uniform(1, 2)) # REMOVED as per USER REQUEST

        print(f"🏁 Done (Sent {count_to_send})")
        return True, sent_count_session
