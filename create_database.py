import sqlite3

DB_PATH = 'your_database_path.db'  # Nama fail pangkalan data

def create_database():
    """Cipta pangkalan data dan jadual daily_usage jika belum wujud."""
    try:
        # Sambung ke pangkalan data (ia akan dicipta jika tidak wujud)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            
            # Cipta jadual daily_usage
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_usage (
                    user_id INTEGER NOT NULL,
                    feature TEXT NOT NULL,
                    usage INTEGER DEFAULT 0,
                    limit INTEGER DEFAULT 0,
                    last_updated DATE NOT NULL,
                    PRIMARY KEY (user_id, feature)
                )
            """)
            
            print("Pangkalan data dan jadual daily_usage telah dicipta atau sudah wujud.")
    
    except Exception as e:
        print(f"Ralat semasa mencipta pangkalan data: {e}")

if __name__ == "__main__":
    create_database()
