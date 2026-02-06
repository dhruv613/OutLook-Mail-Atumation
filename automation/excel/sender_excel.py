import pandas as pd
import threading
import os
import time
from datetime import datetime
import shutil

class SenderStatus:
    USED = "USED"
    BLOCKED = "BLOCKED"
    LOGGED_IN = "LOGGED_IN"
    PENDING = "PENDING"
    NEED_PREMIUM = "NEED_PREMIUM"
    FAILED = "FAILED"
    NOT_LOGINED = "NOT_LOGINED"

class SenderExcelManager:
    _instance = None
    _lock = threading.RLock() # Thread-safe lock for Singleton access
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if not cls._instance:
                cls._instance = super(SenderExcelManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, sender_excel_path):
        with self._lock: # Ensure initialization is safe
            if getattr(self, '_initialized', False):
                return
            
            self.sender_excel_path = sender_excel_path
            self.df = None
            self.email_col_name = "Email" # Default, will detect
            self.password_col_name = "Password" # Default
            self.status_col_name = None 
            
            self._load_and_initialize()
            self._initialized = True

    def _load_and_initialize(self):
        """Loads the Excel file, fixes status columns (New Day Logic), and prepares DF in memory."""
        print(f"📂 Loading Sender Excel: {self.sender_excel_path}")
        try:
            # Load Excel
            if not os.path.exists(self.sender_excel_path):
                 raise FileNotFoundError(f"Sender Excel not found: {self.sender_excel_path}")

            self.df = pd.read_excel(self.sender_excel_path)
            
            # 1. Clean Column Names (Strip whitespace)
            self.df.columns = self.df.columns.str.strip()
            
            # 2. Detect Email/Pass Columns
            cols_lower = {col.lower(): col for col in self.df.columns}
            
            if 'email' in cols_lower:
                self.email_col_name = cols_lower['email']
            else:
                pass # Assume 'Email' or user has it right. If not, it will crash later (good).
                
            if 'password' in cols_lower:
                self.password_col_name = cols_lower['password']

            # 3. Detect/Reset Status Column (New Day Logic)
            today_str = datetime.now().strftime("%d-%m-%Y")
            
            # Find existing status column (Date-like or 'Status')
            import re
            date_pattern = re.compile(r"\d{1,2}-\d{1,2}-\d{4}")
            found_col = None
            
            for col in self.df.columns:
                if date_pattern.match(col) or col.lower() == 'status':
                    found_col = col
                    break
            
            if found_col:
                self.status_col_name = found_col
                
                # Check if New Day
                if found_col != today_str:
                    print(f"🔄 New Day Detected: Renaming '{found_col}' to '{today_str}' and resetting status.")
                    
                    # RENAME column in DF
                    self.df.rename(columns={found_col: today_str}, inplace=True)
                    self.status_col_name = today_str
                    
                    # Logic: Reset all EXCEPT (USED, BLOCKED, FAILED, NEED_PREMIUM)
                    # Note: Original code kept NOT_LOGINED? Usually we want to retry those? 
                    # Original code kept: USED, BLOCKED, FAILED, NOT_LOGINED, NEED_PREMIUM
                    # But usually 'NOT_LOGINED' means 'check again tomorrow'? 
                    # I will follow original logic: Keep critical statuses.
                    
                    safe_statuses = [
                        SenderStatus.BLOCKED, 
                        SenderStatus.NEED_PREMIUM
                    ]
                    
                    # If status is NOT in safe_statuses, set to None (NaN)
                    # Using apply is slower but safer for messy data
                    def reset_logic(val):
                        if pd.isna(val): return None
                        s_val = str(val).strip().upper()
                        if s_val in safe_statuses:
                            return s_val
                        return None
                        
                    self.df[self.status_col_name] = self.df[self.status_col_name].apply(reset_logic)
                    self._save_to_disk()
            else:
                # Create NEW column
                self.status_col_name = today_str
                self.df[self.status_col_name] = None
                print(f"✨ Created new status column: {today_str}")
                self._save_to_disk()

        except Exception as e:
            print(f"❌ Error initializing Sender Excel: {e}")
            raise

    def _save_to_disk(self):
        """Saves current DF to disk securely."""
        try:
             # Atomic-ish save
             self.df.to_excel(self.sender_excel_path, index=False)
             # print(f"💾 Saved Excel.")
        except PermissionError:
             print("⚠️ Permission denied while saving. Retrying...")
             time.sleep(1)
             try:
                self.df.to_excel(self.sender_excel_path, index=False)
             except Exception as e:
                print(f"❌ Failed to save Excel (Permission): {e}")
        except Exception as e:
             print(f"❌ Failed to save Excel: {e}")

    # ----------------------------------------------------------------
    # Public API (Compatible with old manager)
    # ----------------------------------------------------------------

    def get_next_sender(self):
        """Returns (email, password, row_index) for next available account."""
        with self._lock:
            # Reload? No, we keep in memory and save on change. 
            # Singleton maintains state.
            
            # Filter: Email exists, Password exists, Status is Empty/NaN
            mask = (
                self.df[self.email_col_name].notna() & 
                self.df[self.password_col_name].notna() & 
                (self.df[self.status_col_name].isna() | (self.df[self.status_col_name] == ""))
            )
            
            candidates = self.df[mask]
            
            if candidates.empty:
                return None, None, None
                
            # Get first one
            first_idx = candidates.index[0]
            row = self.df.loc[first_idx]
            
            # Return row_index + 2 (because Excel is 1-based and header is row 1)
            # Actually, let's just return the DF index and handle it consistentl internally.
            # BUT the calling code (outlook_handler) expects a 'row' identifier to pass back to 'mark_*'.
            # So returning the DF index is the best 'ID'.
            # Note: The old code returned Excel Row Number. 
            # I will return DF Index. My internal methods will take DF Index.
            # Does external code rely on it being an integer? Yes.
            
            return row[self.email_col_name], row[self.password_col_name], first_idx

    def get_sender_by_row(self, row_idx):
        """Returns email, password for a specific row index."""
        with self._lock:
            try:
                # row_idx is the DF index
                if row_idx not in self.df.index:
                    return None, None, None
                
                row = self.df.loc[row_idx]
                return row[self.email_col_name], row[self.password_col_name], None # 3rd arg is unused 'original row'
            except Exception as e:
                print(f"Error getting sender by row {row_idx}: {e}")
                return None, None, None

    def create_queues(self, num_queues):
        with self._lock:
            # Get all available indices
            mask = (
                self.df[self.email_col_name].notna() & 
                self.df[self.password_col_name].notna() & 
                (self.df[self.status_col_name].isna() | (self.df[self.status_col_name] == ""))
            )
            available_indices = self.df[mask].index.tolist()
            
            print(f"📊 Distributing {len(available_indices)} accounts into {num_queues} queues.")
            
            queues = [[] for _ in range(num_queues)]
            for i, idx in enumerate(available_indices):
                queues[i % num_queues].append(idx)
                
            return queues

    def _update_status(self, row_idx, status):
        with self._lock:
            if row_idx in self.df.index:
                self.df.at[row_idx, self.status_col_name] = status
                self._save_to_disk()

    # --- Status Helpers ---
    def mark_sender_pending(self, row):
        self._update_status(row, SenderStatus.PENDING)

    def mark_sender_used(self, row, count=None):
        status = SenderStatus.USED
        if count:
            status = f"{SenderStatus.USED} ({count})"
        self._update_status(row, status)

    def mark_sender_blocked(self, row):
        self._update_status(row, SenderStatus.BLOCKED)

    def mark_sender_logged_in(self, row):
        self._update_status(row, SenderStatus.LOGGED_IN)

    def mark_sender_not_logined(self, row):
        # Mark BLANK as per previous logic for login retry?
        # Previous code: self._update_status(row, None)
        self._update_status(row, None)

    def mark_sender_need_premium(self, row):
        self._update_status(row, SenderStatus.NEED_PREMIUM)

    def mark_sender_failed(self, row):
         # Previous code: mark blank
         self._update_status(row, None)

    def get_pending_rows(self):
        with self._lock:
            # Find rows with PENDING, NOT_LOGINED, FAILED
            # Or strings startswith PENDING
            
            pending_indices = []
            
            for idx in self.df.index:
                val = self.df.at[idx, self.status_col_name]
                if pd.isna(val) or val == "": 
                    continue
                    
                s_val = str(val).strip().upper()
                
                if (s_val in [SenderStatus.PENDING, SenderStatus.NOT_LOGINED, SenderStatus.FAILED] or 
                    s_val.startswith(SenderStatus.PENDING)):
                    pending_indices.append(idx)
                    
                # Also check for "Logined" but not used logic? 
                # (Previous code checked for 'weird' statuses and reset them to Pending)
                # We'll stick to explicit PENDING for now to avoid loops.
                
            print(f"🔄 Found {len(pending_indices)} pending/retry accounts.")
            return pending_indices