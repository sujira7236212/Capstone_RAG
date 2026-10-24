import os
from dotenv import load_dotenv
from langchain_postgres.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from sqlalchemy import text

load_dotenv()
connection = os.environ.get('DATABASE_URL')
if not connection:
    print('No DATABASE_URL found')
    exit()

try:
    embeddings = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')
    vectorstore = PGVector(embeddings=embeddings, collection_name='kb_local', connection=connection, use_jsonb=True)
    with vectorstore._make_session() as session:
        result = session.execute(text("SELECT cmetadata->>'exercise_id' as exercise_id, count(*) FROM langchain_pg_embedding GROUP BY cmetadata->>'exercise_id'"))
        rows = result.fetchall()
        if not rows:
            print('No data found in kb_local.')
        for row in rows:
            print(f'{row[0]}: {row[1]} chunks')
except Exception as e:
    print('Error local:', e)

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    embeddings_g = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")
    vectorstore_g = PGVector(embeddings=embeddings_g, collection_name='kb_gemini', connection=connection, use_jsonb=True)
    with vectorstore_g._make_session() as session:
        result = session.execute(text("SELECT cmetadata->>'exercise_id' as exercise_id, count(*) FROM langchain_pg_embedding WHERE collection_id = (SELECT uuid FROM langchain_pg_collection WHERE name = 'kb_gemini') GROUP BY cmetadata->>'exercise_id'"))
        rows = result.fetchall()
        if not rows:
            print('No data found in kb_gemini.')
        for row in rows:
            print(f'Gemini {row[0]}: {row[1]} chunks')
except Exception as e:
    print('Error gemini:', e)
