import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain_core.documents import Document

# 1. Load your Google Gemini API Key from .env
load_dotenv()

# 2. Database connection string (Docker)
CONNECTION_STRING = "postgresql+psycopg2://myuser:mypassword@localhost:5432/vectordb"

# 3. Define the collection name (table equivalent)
collection_name = "my_knowledge_base"

def main():
    print("Initializing Embedding Model...")
    # Using Gemini embedding model
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")

    print("Connecting to PostgreSQL (pgvector)...")
    # Connect to the Vector Store (LangChain creates the table if it doesn't exist)
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=CONNECTION_STRING,
        use_jsonb=True,
    )

    print("Preparing mock data...")
    # Create mock text documents
    docs = [
        Document(
            page_content="Overtime (OT) requests must be approved by the department manager at least 1 day before starting work.",
            metadata={"source": "HR_Manual.txt", "topic": "OT"}
        ),
        Document(
            page_content="The company will transfer salaries to employee accounts on the 25th of every month via Kasikorn Bank only.",
            metadata={"source": "HR_Manual.txt", "topic": "Payroll"}
        ),
        Document(
            page_content="If you forget your computer password or need to change your company email password, contact IT Support at internal extension 1111.",
            metadata={"source": "IT_Support.txt", "topic": "Password"}
        )
    ]

    print("Converting data to vectors and saving to database... (This may take a moment)")
    # This sends text to Gemini for vector embedding, then saves everything to Postgres
    vector_store.add_documents(docs)
    
    print("[SUCCESS] Data successfully saved to the database!\n")
    
    # ---------------------------------------------------------------------
    # Test Retrieval immediately
    # ---------------------------------------------------------------------
    print("--- Testing Retrieval ---")
    query = "When is payday and which bank is used?"
    print(f"Mock Query: '{query}'\n")
    
    # Find the top 1 most similar document (k=1)
    results = vector_store.similarity_search(query, k=1)
    
    for doc in results:
        print(f"[>] Retrieved Content: {doc.page_content}")
        print(f"[>] Metadata: {doc.metadata}")

if __name__ == "__main__":
    main()
