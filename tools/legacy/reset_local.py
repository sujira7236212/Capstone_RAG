import os
from dotenv import load_dotenv
from langchain_postgres.vectorstores import PGVector
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

connection = os.environ.get("DATABASE_URL")
if not connection:
    print("Error: DATABASE_URL not found.")
    exit(1)

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
collection_name = "kb_local"

vectorstore = PGVector(
    embeddings=embeddings,
    collection_name=collection_name,
    connection=connection,
    use_jsonb=True,
)

print(f"Deleting collection '{collection_name}'...")
try:
    vectorstore.delete_collection()
    print("Collection deleted successfully.")
except Exception as e:
    print(f"Error deleting collection: {e}")
