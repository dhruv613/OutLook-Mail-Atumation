from automation.Mark_sender import SenderExcelManager
from automation.login import Login
import time


class OutlookHandler:
    def __init__(self, driver, sender_excel_path):
        self.driver = driver
        self.excel = SenderExcelManager(sender_excel_path)

    # -------------------------------------------------------------
    # Login process using Excel Manager
    # -------------------------------------------------------------

    def login_next_account(self):
        email, password, row = self.excel.get_next_sender()

        if not email:
            print("❌ No more accounts available.")
            return False

        print(f"➡ Logging in with: {email}")


        login_handler = Login(self.driver)
        time.sleep(2)

        success = login_handler.outlook_login(email, password)

        if success:
            self.excel.mark_sender_used(row)
            print(f"✔ Login Successful → Marked USED ({email})")
        else:
            print(f"❌ Login Failed → NOT marked USED ({email})")

            return success