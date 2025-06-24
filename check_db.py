from sqlalchemy import create_engine, text
from src.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url)

with engine.connect() as conn:
    print("Checking documents table:")
    result = conn.execute(text('SELECT * FROM documents'))
    rows = result.fetchall()
    print(f'Found {len(rows)} documents')
    for row in rows:
        print(row)
    
    print("\nChecking jobs table:")
    result = conn.execute(text('SELECT * FROM jobs'))
    rows = result.fetchall()
    print(f'Found {len(rows)} jobs')
    for row in rows:
        print(row)
