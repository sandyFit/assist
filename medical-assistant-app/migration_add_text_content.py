from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration - adjust this to match your setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./medical_assistant.db")

def add_text_content_column():
    """Add text_content column to the file table"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as connection:
            # Add the text_content column
            connection.execute(text("""
                ALTER TABLE file 
                ADD COLUMN text_content TEXT;
            """))
            connection.commit()
            print("✅ Successfully added text_content column to file table")
            
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  Column text_content already exists")
        else:
            print(f"❌ Error adding column: {e}")
    
    finally:
        engine.dispose()

if __name__ == "__main__":
    add_text_content_column()
