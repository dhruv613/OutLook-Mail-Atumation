from automation.data.database_manager import DatabaseManager
import threading

class SenderStatus:
    USED = "USED"
    BLOCKED = "BLOCKED"
    LOGGED_IN = "LOGGED_IN"
    PENDING = "PENDING"
    NEED_PREMIUM = "NEED_PREMIUM"
    FAILED = "FAILED"
    NOT_LOGINED = "NOT_LOGINED"
    USED_L = "USED-L"

class SenderManager:
    # Mimic the interface of SenderExcelManager
    _lock = threading.RLock() # Not strictly needed with DB, but good for safety

    def __init__(self, sender_excel_path_ignored=None):
        # We ignore the path because we use the DB now. 
        # Kept argument for compatibility with existing instantiation calls.
        self.db = DatabaseManager()

    # --------------------------------------------------------------------
    # PUBLIC: Get next available Email
    # --------------------------------------------------------------------
    def get_next_sender(self):
        # Find one Pending or NULL status
        query = """
            SELECT email, password, original_row 
            FROM senders 
            WHERE status IS NULL OR status = '' OR status = 'PENDING'
            LIMIT 1
        """
        row = self.db.fetch_one(query)
        if row:
            return row['email'], row['password'], row['original_row']
        return None, None, None

    # --------------------------------------------------------------------
    # PUBLIC: Create Queues (Split available rows into buckets)
    # --------------------------------------------------------------------
    def create_queues(self, num_queues):
        # Fetch all available original_rows
        query = """
            SELECT original_row 
            FROM senders 
            WHERE status IS NULL OR status = '' OR status = 'PENDING' OR status LIKE 'PENDING:%'
            ORDER BY original_row ASC
        """
        rows = self.db.fetch_all(query)
        
        queues = [[] for _ in range(num_queues)]
        if not rows:
             print("⚠️ No available rows found in DB.")
             return queues

        for i, r in enumerate(rows):
            queues[i % num_queues].append(r['original_row'])
            
        print(f"📊 DB Rows Distributed: {len(rows)} accounts split into {num_queues} queues.")
        return queues

    # --------------------------------------------------------------------
    # PUBLIC: Get specific row
    # --------------------------------------------------------------------
    def get_sender_by_row(self, row_idx):
        query = "SELECT email, password, status FROM senders WHERE original_row = ?"
        res = self.db.fetch_one(query, (row_idx,))
        if res:
            return res['email'], res['password'], res['status'], row_idx
        return None, None, None, row_idx

    # --------------------------------------------------------------------
    # STATUS UPDATES
    # --------------------------------------------------------------------
    def _update_status(self, row_idx, status):
        self.db.execute("UPDATE senders SET status = ? WHERE original_row = ?", (status, row_idx))

    def update_status(self, row_idx, status):
        """Public wrapper for _update_status to match MailSender expectation."""
        self._update_status(row_idx, status)

    def mark_sender_pending(self, row):
        self._update_status(row, SenderStatus.PENDING)

    def mark_sender_used(self, row, count=None):
        status = SenderStatus.USED
        # Logic to preserve count if needed? The DB has 'rounds_completed' but status string is also used.
        if count:
            status = f"{SenderStatus.USED} ({count})"
        self._update_status(row, status)

    def mark_sender_used_reuse(self, row, count=None):
        status = "USED-R"
        if count:
            status = f"USED-R ({count})"
        self._update_status(row, status)

    def mark_sender_blocked(self, row):
        self._update_status(row, SenderStatus.BLOCKED)

    def mark_sender_limit_reached(self, row):
        self._update_status(row, SenderStatus.USED_L)

    def mark_sender_logged_in(self, row):
        self._update_status(row, SenderStatus.LOGGED_IN)

    def mark_sender_not_logined(self, row):
        self._update_status(row, SenderStatus.NOT_LOGINED)
        # self._update_status(row, None) # Reverted: User wants to track these

    def mark_sender_need_premium(self, row):
        self._update_status(row, SenderStatus.NEED_PREMIUM)

    def mark_sender_failed(self, row):
        # Check if blocked first?
        curr = self.db.fetch_one("SELECT status FROM senders WHERE original_row = ?", (row,))
        if curr and curr['status'] in [SenderStatus.BLOCKED, SenderStatus.USED_L, SenderStatus.USED]:
            # print(f"ℹ️ Skipping mark_failed for Row {row} (Status: {curr['status']})")
            return

        self._update_status(row, SenderStatus.FAILED)
        # self._update_status(row, None) # Check failed -> FAILED to prevent loop

    def mark_sender_rounds(self, row, rounds):
        # Update rounds column AND status
        status = f"{SenderStatus.PENDING}:{rounds}"
        self.db.execute("UPDATE senders SET status = ?, rounds_completed = ? WHERE original_row = ?", (status, rounds, row))

    # --------------------------------------------------------------------
    # REPORTING / RETRY
    # --------------------------------------------------------------------
    def get_pending_rows(self):
        query = """
            SELECT original_row FROM senders 
            WHERE (status IS NULL OR status = '' OR status = 'PENDING' OR status = 'NOT_LOGINED' OR status = 'FAILED' OR status LIKE 'PENDING:%')
            AND status != 'USED-L' AND status != 'BLOCKED' AND status NOT LIKE 'USED%'
        """
        rows = self.db.fetch_all(query)
        return [r['original_row'] for r in rows]

    def get_failed_and_blocked_rows(self):
        query = "SELECT email, password FROM senders WHERE status IN ('FAILED', 'BLOCKED')"
        rows = self.db.fetch_all(query)
        result_map = {}
        for r in rows:
            result_map[r['email']] = r['password']
        return result_map

    def get_used_accounts(self):
        # Only standard USED or USED-R (Reuse) or USED-L (Limit)
        query = "SELECT email FROM senders WHERE status = 'USED' OR status LIKE 'USED-R%' OR status = 'USED-L'"
        rows = self.db.fetch_all(query)
        return [r['email'] for r in rows]

    def get_limit_reached_accounts(self):
        query = "SELECT email FROM senders WHERE status = 'USED-L'"
        rows = self.db.fetch_all(query)
        return [r['email'] for r in rows]

    def get_failed_accounts(self):
        query = "SELECT email FROM senders WHERE status = 'FAILED'"
        rows = self.db.fetch_all(query)
        return [r['email'] for r in rows]

    def get_not_logined_accounts(self):
        query = "SELECT email FROM senders WHERE status = 'NOT_LOGINED'"
        rows = self.db.fetch_all(query)
        return [r['email'] for r in rows]

    def get_blocked_accounts(self):

        query = "SELECT email FROM senders WHERE status = 'BLOCKED'"
        rows = self.db.fetch_all(query)
        return [r['email'] for r in rows]
