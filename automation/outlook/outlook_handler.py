import time
from automation.data.sender_manager import SenderManager
from automation.login.login import Login

class OutlookHandler:
    def __init__(self, driver, sender_excel_path):
        self.driver = driver
        self.excel = SenderManager(sender_excel_path)

    # -------------------------------------------------------------
    # Login next available account
    # -------------------------------------------------------------
    # --------------------------------------------------------------------
    # Login next available account (Legacy / Sequential)
    # --------------------------------------------------------------------
    def login_next_account(self):
        email, password, row = self.excel.get_next_sender()

        if not email:
            print("❌ No more accounts available.")
            return None
            
        return self._perform_login(email, password, row)

    # --------------------------------------------------------------------
    # [NEW] Process specific account from Queue
    # --------------------------------------------------------------------
    def process_account(self, row):
        email, password, status, _ = self.excel.get_sender_by_row(row)
        if not email:
            return False
            
        # Parse start round from status
        start_round = 1
        if status and ":" in status:
            try:
                parts = status.split(":")
                if len(parts) > 1 and parts[1].isdigit():
                    start_round = int(parts[1]) + 1 # Start from NEXT round
                    # print(f"🔄 Resuming {email} from Round {start_round}...")
            except:
                pass

        # 1. Login
        if self._perform_login(email, password, row, start_round):
            # Login successful -> Logic handled in _perform_login for status updates
            return True
        return False


    # --------------------------------------------------------------------
    # Internal Login Logic
    # --------------------------------------------------------------------
    def _perform_login(self, email, password, row, start_round=1):
        # print(f"➡ Logging in with: {email}")

        login_handler = Login(self.driver)
        
        try:
            success = login_handler.outlook_login(email, password)
            # print(f"DEBUG: login_handler.outlook_login returned {success} for {email}")

            if success:
                # 2. Mark LOGGED_IN
                self.excel.mark_sender_logged_in(row)
                print(f"logined == loginned with this id\"{email}\"")
                
                # 3. Perform Mail Sending Process
                # print(f"DEBUG: Starting _perform_email_sending for {email} starting at round {start_round}...")
                mail_result, sent_count = self._perform_email_sending(email, row, start_round)
                # print(f"DEBUG: _perform_email_sending returned {mail_result} with count {sent_count}")

                if mail_result:
                    # 4. Mark USED (Final Success)
                    self.excel.mark_sender_used(row, count=sent_count)
                    # print(f"✔ Mail Process Complete → Marked USED ({email}) with {sent_count} recipients")
                    return True
                else:
                    print(f"⚠️ Mail Process Failed/Incomplete ({email})")
                    
                    # Check current status
                    _, _, current_status, _ = self.excel.get_sender_by_row(row)
                    if current_status == "USED-L":
                        print(f"✅ Limit Reached (USED-L) - Process Considered Complete.")
                        return True # Return TRUE so worker doesn't think it failed

                    # Only mark PENDING if no mails sent (and thus likely no USED-R/USED-L status set)
                    if sent_count == 0:
                        self.excel.mark_sender_pending(row)
                    else:
                        print(f"ℹ️ Partial success ({sent_count}), preserving USED-R/USED-L status.")
                    return False

            else:
                if login_handler.account_blocked:
                    self.excel.mark_sender_blocked(row)
                    print(f"🚫 Account BLOCKED → Marked BLOCKED ({email})")
                else:
                    # Login Failed -> NOT_LOGINED
                    self.excel.mark_sender_not_logined(row)
                    print(f"⚠️ Login Failed (Generic) → Marked NOT_LOGINED ({email})")
                return False
                
        except Exception as e:
            print(f"💥 Exception in process logic: {e}")
            import traceback
            traceback.print_exc()
            self.excel.mark_sender_pending(row)
            return False

    def _perform_email_sending(self, email, row, start_round=1):
        try:
            from automation.outlook.mail_sender import MailSender
            sender = MailSender(self.driver, self.excel, row, email)
            # print("DEBUG: MailSender initialized. Calling send_process()...")
            
            # Call send_process
            result = sender.send_process(start_round=start_round)
            
            # Handle return variations (bool vs tuple)
            if isinstance(result, tuple):
                 return result
            else:
                 # Assume result is boolean success, count is unknown (0)
                 return result, 0
                 
        except Exception as e:
            print(f"❌ Error in mail sending process: {e}")
            import traceback
            traceback.print_exc()
            return False, 0
