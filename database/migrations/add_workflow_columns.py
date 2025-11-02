"""
Migration: Add LinkedIn automation workflow columns to contacts table
"""

from sqlalchemy import create_engine, text
from pathlib import Path

# Get database path
db_path = Path(__file__).parent.parent / "leadon.db"
engine = create_engine(f'sqlite:///{db_path}')

def upgrade():
    """Add workflow tracking columns to contacts table"""
    with engine.connect() as conn:
        # Add workflow_stage column
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN workflow_stage VARCHAR(50) DEFAULT 'new'"))
            print("✅ Added 'workflow_stage' column")
        except Exception as e:
            print(f"⚠️  'workflow_stage' column might already exist: {e}")
        
        # Add last_action column
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN last_action VARCHAR(100)"))
            print("✅ Added 'last_action' column")
        except Exception as e:
            print(f"⚠️  'last_action' column might already exist: {e}")
        
        # Add last_action_date column
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN last_action_date DATETIME"))
            print("✅ Added 'last_action_date' column")
        except Exception as e:
            print(f"⚠️  'last_action_date' column might already exist: {e}")
        
        # Add next_action column
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN next_action VARCHAR(100)"))
            print("✅ Added 'next_action' column")
        except Exception as e:
            print(f"⚠️  'next_action' column might already exist: {e}")
        
        # Add next_action_date column
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN next_action_date DATETIME"))
            print("✅ Added 'next_action_date' column")
        except Exception as e:
            print(f"⚠️  'next_action_date' column might already exist: {e}")
        
        # Add automation_notes column
        try:
            conn.execute(text("ALTER TABLE contacts ADD COLUMN automation_notes TEXT"))
            print("✅ Added 'automation_notes' column")
        except Exception as e:
            print(f"⚠️  'automation_notes' column might already exist: {e}")
        
        conn.commit()
        print("✅ Migration complete!")
        print("\n📊 Workflow stages available:")
        print("   - new: Contact just added")
        print("   - connect_sent: Connection request sent")
        print("   - connected: Connection accepted")
        print("   - liked: Liked their posts")
        print("   - commented: Commented on their posts")
        print("   - messaged: Sent first message")
        print("   - replied: They replied to message")
        print("   - qualified: Qualified lead")
        print("   - disqualified: Not a good fit")

if __name__ == "__main__":
    print("Running migration: add_workflow_columns")
    upgrade()

