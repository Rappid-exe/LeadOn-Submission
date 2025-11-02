"""
Migration script to add company enrichment fields
"""

from sqlalchemy import create_engine, text
from loguru import logger
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'leadon.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

def migrate():
    """Add enrichment fields to companies table and create company_profile table"""
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Add enrichment fields to companies table
            logger.info("Adding enrichment fields to companies table...")
            
            conn.execute(text("""
                ALTER TABLE companies ADD COLUMN industry_analysis TEXT
            """))
            conn.commit()
            logger.info("✅ Added industry_analysis column")
            
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"industry_analysis: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE companies ADD COLUMN pain_points TEXT
            """))
            conn.commit()
            logger.info("✅ Added pain_points column")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"pain_points: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE companies ADD COLUMN value_proposition TEXT
            """))
            conn.commit()
            logger.info("✅ Added value_proposition column")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"value_proposition: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE companies ADD COLUMN enrichment_notes TEXT
            """))
            conn.commit()
            logger.info("✅ Added enrichment_notes column")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"enrichment_notes: {e}")
        
        try:
            conn.execute(text("""
                ALTER TABLE companies ADD COLUMN last_enriched_at DATETIME
            """))
            conn.commit()
            logger.info("✅ Added last_enriched_at column")
        except Exception as e:
            if "duplicate column name" not in str(e).lower():
                logger.warning(f"last_enriched_at: {e}")
        
        # Create company_profile table
        try:
            logger.info("Creating company_profile table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS company_profile (
                    id INTEGER PRIMARY KEY,
                    website_url VARCHAR(500) NOT NULL,
                    company_name VARCHAR(255),
                    tagline VARCHAR(500),
                    description TEXT,
                    products_services TEXT,
                    target_customers TEXT,
                    value_propositions TEXT,
                    differentiators TEXT,
                    use_cases TEXT,
                    ai_summary TEXT,
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """))
            conn.commit()
            logger.info("✅ Created company_profile table")
        except Exception as e:
            logger.warning(f"company_profile table: {e}")
    
    logger.info("✅ Migration complete!")

if __name__ == "__main__":
    migrate()

