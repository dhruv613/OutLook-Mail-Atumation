
import sqlite3
import os

DB_PATH = "automation.db"

def reset_recipients():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print("🔄 Resetting all 'USED' recipients to Available (NULL)...")
        
        # Count before
        cursor.execute("SELECT COUNT(*) FROM recipients WHERE status = 'USED'")
        count_used = cursor.fetchone()[0]
        print(f"   Found {count_used} USED recipients.")

        if count_used == 0:
            print("   No USED recipients to reset.")
            return

        # Execute Update
        cursor.execute("UPDATE recipients SET status = NULL WHERE status = 'USED'")
        conn.commit()
        
        print(f"✅ Successfully reset {count_used} recipients. You can run the automation start again.")

    except Exception as e:
        print(f"❌ Error resetting database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    confirm = input("Are you sure you want to reset all USED recipients? (y/n): ")
    if confirm.lower() == 'y':
        reset_recipients()
    else:
        print("Cancelled.")
