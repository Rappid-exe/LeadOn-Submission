"""
Migration: Add tags, source_reason, and search_query to contacts table
"""

from sqlalchemy import create_engine, Column, String, JSON, text
from pathlib import Path

# Get database path
db_path = Path(__file__).parent.parent / "leadon.db"
engine = create_engine(f'sqlite:///{db_path}')

def upgrade():
    """Add new columns to contacts table"""
    with engine.connect() as conn:
        # Add tags column (JSON)
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN tags TEXT"))
            print("✅ Added 'tags' column")
        except Exception as e:
            print(f"⚠️  'tags' column might already exist: {e}")
        
        # Add source_reason column
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN source_reason VARCHAR(500)"))
            print("✅ Added 'source_reason' column")
        except Exception as e:
            print(f"⚠️  'source_reason' column might already exist: {e}")
        
        # Add search_query column
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN search_query VARCHAR(500)"))
            print("✅ Added 'search_query' column")
        except Exception as e:
            print(f"⚠️  'search_query' column might already exist: {e}")
        
        conn.commit()
        print("✅ Migration complete!")

if __name__ == "__main__":
    print("Running migration: add_contact_tags")
    upgrade()

