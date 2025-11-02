"""
Migration: Add Telegram Campaign Support

Adds:
1. phone_number field to integrations table
2. telegram_messages table for tracking campaign messages
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.db_manager import get_db_manager


def migrate():
    """Run the migration"""
    print("🔄 Starting Telegram Campaign migration...")

    db_manager = get_db_manager()
    engine = db_manager.engine

    try:
        # Add phone_number column to integrations table
        print("📝 Adding phone_number column to integrations table...")
        with engine.connect() as conn:
            try:
                from sqlalchemy import text
                conn.execute(text("ALTER TABLE integrations ADD COLUMN phone_number VARCHAR(50)"))
                conn.commit()
                print("✅ Added phone_number column")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("⚠️  phone_number column already exists")
                else:
                    raise

        # Create telegram_messages table
        print("📝 Creating telegram_messages table...")
        with engine.connect() as conn:
            try:
                from sqlalchemy import text
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS telegram_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id INTEGER,
                        contact_id INTEGER NOT NULL,
                        integration_id INTEGER NOT NULL,
                        phone_number VARCHAR(50) NOT NULL,
                        telegram_user_id VARCHAR(100),
                        telegram_username VARCHAR(100),
                        message_text TEXT NOT NULL,
                        message_id VARCHAR(100),
                        status VARCHAR(20) DEFAULT 'pending',
                        error_message TEXT,
                        sent_at DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
                        FOREIGN KEY (contact_id) REFERENCES contacts(id),
                        FOREIGN KEY (integration_id) REFERENCES integrations(id)
                    )
                """))
                conn.commit()
                print("✅ Created telegram_messages table")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("⚠️  telegram_messages table already exists")
                else:
                    raise

        print("✅ Migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


if __name__ == "__main__":
    migrate()

