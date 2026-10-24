import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
connection = os.environ.get("DATABASE_URL")
if not connection:
    print("No DATABASE_URL found in .env")
    exit(1)

engine = create_engine(connection)
with engine.connect() as session:
    print("Checking Gemini collection ('kb_gemini')...")
    # Query to count total embeddings
    query_total = text("""
        SELECT count(*) 
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name = 'kb_gemini'
    """)
    total = session.execute(query_total).scalar()
    print(f"Total chunks in DB (kb_gemini): {total}")
    
    # Query to count by exercise_id in metadata
    query_group = text("""
        SELECT e.cmetadata->>'exercise_id' as exercise, count(*) 
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name = 'kb_gemini'
        GROUP BY exercise
        ORDER BY exercise
    """)
    result = session.execute(query_group)
    print("\nChunks by Exercise ID:")
    for row in result:
        print(f" - {row[0]}: {row[1]} chunks")
        
    print("\nChecking Local collection ('kb_local')...")
    query_total_local = text("""
        SELECT count(*) 
        FROM langchain_pg_embedding e
        JOIN langchain_pg_collection c ON e.collection_id = c.uuid
        WHERE c.name = 'kb_local'
    """)
    total_local = session.execute(query_total_local).scalar()
    print(f"Total chunks in DB (kb_local): {total_local}")
