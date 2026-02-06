import time
import random
from automation.outlook.browser_manager import BrowserManager
from automation.outlook.outlook_handler import OutlookHandler
from utils.config import (
    SENDER_EXCEL_PATH, BROWSER_NAME, HEADLESS, DETACH, INCOGNITO,
    PARALLEL_FIREFOX_INSTANCES, STAGGER_DELAY_MIN, STAGGER_DELAY_MAX
)
from automation.data.sender_manager import SenderManager
from automation.data.sync_manager import SyncManager

    
# from utils.logger import logger

def main():
    # 1. Check Firefox is available
    start_time = time.time()

    temp_mgr = BrowserManager()
    if not temp_mgr._find_browser_path("firefox"):
        print("Firefox not found! Please install Firefox or check BROWSER_PATHS in config.py")
        return
    
    # 2. Sync Excel -> DB
    sync_mgr = SyncManager()

    sync_mgr.import_from_excel()

    # 3. Prepare Queue
    excel_mgr = SenderManager()
    
    # Create queues for 4 Firefox instances
    num_instances = PARALLEL_FIREFOX_INSTANCES
    queues = excel_mgr.create_queues(num_instances)
    
    # 3. Launch Parallel Firefox Workers (Phase 1)
    threads = []
    
    from automation.outlook.multi_browser_worker import MultiBrowserWorker
    
    for i in range(num_instances):
        if not queues[i]:
            continue
        
        # Staggered start: Wait 10-20 seconds before launching next browser
        if i > 0:
            stagger_delay = random.randint(STAGGER_DELAY_MIN, STAGGER_DELAY_MAX)
            time.sleep(stagger_delay)
        
        t = MultiBrowserWorker(browser_name="firefox", queue=queues[i], worker_id=i+1)
        t.start()
        threads.append(t)
        
    # Wait for completion
    for t in threads:
        t.join()
        
    # 4. Retry Logic (Phase 2) - Using Firefox instances again
    # Loop until no pending rows or max retries reached
    max_retry_loops = 3
    retry_loop_count = 0
    
    while retry_loop_count < max_retry_loops:
        pending_rows = excel_mgr.get_pending_rows()
        
        if not pending_rows:
            print("✅ No pending rows found. Retry loop verified clean.")
            break
            
        print(f"🔄 [Retry Execution {retry_loop_count+1}/{max_retry_loops}] Found {len(pending_rows)} pending rows.")

        # Split pending rows across Firefox instances (max 2 for retry)
        retry_instances = num_instances
        retry_queues = [[] for _ in range(retry_instances)]
        for i, row in enumerate(pending_rows):
            retry_queues[i % retry_instances].append(row)
            
        retry_threads = []
        for i in range(retry_instances):
            if not retry_queues[i]: 
                continue
            
            # Stagger retry launches too
            if i > 0:
                stagger_delay = random.randint(STAGGER_DELAY_MIN, STAGGER_DELAY_MAX)
                time.sleep(stagger_delay)
             
            t = MultiBrowserWorker(
                browser_name="firefox", 
                queue=retry_queues[i], 
                worker_id=90 + (retry_loop_count*10) + i, # Unique IDs per loop
                is_retry=True
            )
            t.start()
            retry_threads.append(t)
             
        for t in retry_threads:
            t.join()
            
        retry_loop_count += 1
        
    print(f"🏁 All retry loops completed ({retry_loop_count}).")

    # --- FINAL SUMMARY ---
    from automation.data.recipient_manager import RecipientManager
    # from utils.config import RECIPIENT_EXCEL_PATH

    import win32com.client as wincl
    
    speak = wincl.Dispatch("SAPI.SpVoice")
    speak.Speak("Automation finished.") 
    end_time = time.time()
    total_seconds = end_time - start_time
    minutes = int(total_seconds // 60)
    seconds = int(total_seconds % 60)
    
    print("\n--- Automation Summary ---")
    print(f"⏱️ Total Runtime: {minutes}m {seconds}s")

    
    # 5. Export DB -> Excel
    sync_mgr.export_to_excel()
    
    # 1. Used IDs
    used_accounts = excel_mgr.get_used_accounts()
    if used_accounts:
        print("\n✅ Used IDs:")
        for email in used_accounts:
            print(f"- {email}")
    else:
        print("\n✅ Used IDs: None")

    # 2. Failed IDs
    failed_accounts = excel_mgr.get_failed_accounts()
    if failed_accounts:
        print("\n❌ Failed IDs:")
        for email in failed_accounts:
            print(f"- {email}")
    else:
        print("\n❌ Failed IDs: None")

    # 3. Blocked IDs
    blocked_accounts = excel_mgr.get_blocked_accounts()
    if blocked_accounts:
        print("\n🚫 Blocked IDs:")
        for email in blocked_accounts:
            print(f"- {email}")
    else:
        print("\n🚫 Blocked IDs: None")

    # 4. Not Logined IDs
    not_logined_accounts = excel_mgr.get_not_logined_accounts()
    if not_logined_accounts:
        print("\n⚠️ Not Logined IDs:")
        for email in not_logined_accounts:
            print(f"- {email}")
    else:
        print("\n⚠️ Not Logined IDs: None")

    # 5. Limit Reached IDs
    limit_reached_accounts = excel_mgr.get_limit_reached_accounts()
    if limit_reached_accounts:
        print("\n🛑 Limit Reached IDs (USED-L):")
        for email in limit_reached_accounts:
            print(f"- {email}")
    else:
        print("\n🛑 Limit Reached IDs: None")

    # 6. Count of Used Recipients
    rec_mgr = RecipientManager()
    used_recipients_count = rec_mgr.get_used_count()
    print(f"\n📊 Total used recipients: {used_recipients_count}")


if __name__ == "__main__":
    main()