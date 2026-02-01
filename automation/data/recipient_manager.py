from automation.data.database_manager import DatabaseManager
import threading

class RecipientStatus:
    PROCESSING = "PROCESSING"
    USED = "USED"
    FAILED = "FAILED"

class RecipientManager:
    # Mimic RecipientExcelManager
    _lock = threading.RLock()

    def __init__(self, file_path_ignored=None):
        self.db = DatabaseManager()
        # legacy attributes compatibility
        self.email_col = 1
        self.status_col = 2
        
    def get_batch_recipients(self, batch_size, sender_row_index):
        """
        Retrieves recipients atomically from DB.
        """
        # 1. Fetch Candidates (Available)
        # Using LIMIT to get exactly batch_size
        query = """
            SELECT id, email, original_row 
            FROM recipients 
            WHERE status IS NULL OR status = ''
            LIMIT ?
        """
        rows = self.db.fetch_all(query, (batch_size,))
        
        recipients = []
        rows_to_update = [] # We return original_row indices for compatibility
        
        if not rows:
            return [], []
            
        ids_to_lock = []
        
        for r in rows:
            recipients.append(r['email'])
            rows_to_update.append(r['original_row'])
            ids_to_lock.append(r['id'])
            
        # 2. Lock them immediately (Mark PROCESSING)
        # We update by ID which is indexed and fast
        if ids_to_lock:
            placeholders = ', '.join('?' for _ in ids_to_lock)
            update_query = f"UPDATE recipients SET status = 'PROCESSING' WHERE id IN ({placeholders})"
            # Correct Approach:
            # "UPDATE recipients SET status = 'PROCESSING' WHERE id IN (1, 2, 3)"
            self.db.execute(update_query, tuple(ids_to_lock))
            
        return recipients, rows_to_update

    def update_batch_status(self, rows, status):
        """
        Updates status for specific rows (original_row).
        rows: list of original_row integers
        """
        if not rows:
            return

        placeholders = ', '.join('?' for _ in rows)
        query = f"UPDATE recipients SET status = ? WHERE original_row IN ({placeholders})"
        
        # Status needs to be "STATUS" (clean)
        # Legacy code passed "USED", "FAILED"
        # We don't need date suffix in DB, we store that on Export or updated_at
        
        params = [status] + rows
        self.db.execute(query, tuple(params))

    def get_used_count(self):
        query = "SELECT COUNT(*) as count FROM recipients WHERE status = 'USED' OR status LIKE 'USED%'"
        res = self.db.fetch_one(query)
        return res['count'] if res else 0
