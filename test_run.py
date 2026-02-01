import time
from pathlib import Path
from automation.browser_manager import BrowserManager
from automation.outlook_handler import OutlookHandler



def main():
    # Path setup (automatic)
    project_root = Path(__file__).resolve().parent
    sender_excel_path = project_root.joinpath("data", "sender_list.xlsx")

    # Step 1: Start browser
    browser_mgr = BrowserManager()
    driver = browser_mgr.launch_browser()
    print("✅ Browser started successfully")

    # Step 2: Initialize Outlook Handler
    outlook = OutlookHandler(driver, str(sender_excel_path))
    print("✅ Outlook handler initialized")

    # Step 3: Test the account switching logic (pick 5 IDs)
    outlook.login_next_account()
    print("✅ Login test completed")

    # mark_sender_used(sender_excel_path, row=2)




if __name__ == "__main__":
    main()
