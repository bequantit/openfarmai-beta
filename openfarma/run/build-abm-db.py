import os, sys
import pandas as pd
import streamlit as st
from pathlib import Path
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from openfarma.src.params import ABM_PATH, CHROMA_DB_PATH

OPENFARMA_API_KEY = st.secrets["OPENFARMA_API_KEY"]
BASE_COLUMNS = ['Marca', 'Nombre', 'Presentacion']
ID_COLUMN = 'EAN'

def get_column_combinations(df):
    """Generate all possible column combinations for vector databases."""
    combinations = []
    remaining_columns = [col for col in df.columns if col not in BASE_COLUMNS + [ID_COLUMN]]
    
    for col in remaining_columns:
        combinations.append(BASE_COLUMNS + [col])
    
    return combinations

def create_vector_db(documents, persist_directory, embedding):
    """Create a vector database with the given documents."""
    return Chroma.from_documents(
        documents=documents,
        embedding=embedding,
        persist_directory=persist_directory
    )

def add_to_vector_db(documents, persist_directory, embedding):
    """Add new documents to an existing vector database."""
    db = Chroma(persist_directory=persist_directory, embedding_function=embedding)
    db.add_documents(documents)
    return db

def get_existing_eans(persist_directory):
    """Get EANs from existing vector database if it exists."""
    if os.path.exists(persist_directory):
        db = Chroma(persist_directory=persist_directory)
        return set(doc.get('EAN') for doc in db.get()['metadatas'])
    return set()

def process_database_combination(df, columns, embedding, name:str=None):
    """Process a single database combination and create/update its vector database.
    
    Args:
        df (pd.DataFrame): DataFrame containing the product data
        columns (list): List of columns to use for this database
        embedding: The embedding model to use
    
    Returns:
        tuple: (database_name, number_of_documents_added)
    """
    # Extract the column that's not in BASE_COLUMNS
    extra_col = [col for col in columns if col not in BASE_COLUMNS+[ID_COLUMN]]
    db_name = f"db_{extra_col[0]}" if name is None else name
    persist_dir = os.path.join(CHROMA_DB_PATH, db_name)
    
    # Get current and existing EANs
    current_eans = set(df[ID_COLUMN].astype(str))
    existing_eans = get_existing_eans(persist_dir)
    
    # Find new EANs that need to be added
    new_eans = current_eans - existing_eans
    
    if not new_eans:
        print(f"Base de datos {db_name} está actualizada. No hay nuevos documentos para agregar.")
        return db_name, 0
    
    # Create documents only for new products
    documents = []
    for _, row in df.iterrows():
        ean = str(row[ID_COLUMN])
        
        # Skip if not a new EAN or if all required columns are empty
        if ean not in new_eans or all(pd.isna(row[col]) for col in columns):
            continue
        
        # Create text content from selected columns
        content_parts = []
        for col in columns:
            if not pd.isna(row[col]):
                text = str(row[col]).strip()
                if text:
                    text = f"{col}: {text}"
                    content_parts.append(text)
        
        if content_parts:
            content = ' '.join(content_parts)
            documents.append(Document(
                metadata={'EAN': ean},
                page_content=content
            ))
    
    if documents:
        if os.path.exists(persist_dir):
            # Add new documents to existing database
            add_to_vector_db(documents, persist_dir, embedding)
            print(f"Base de datos {db_name} actualizada con {len(documents)} nuevos documentos.")
        else:
            # Create new database if it doesn't exist
            create_vector_db(documents, persist_dir, embedding)
            print(f"Base de datos {db_name} creada con {len(documents)} documentos.")
        
        return db_name, len(documents)
    
    return db_name, 0

def process_csv_data():
    """Process CSV data and create/update vector databases."""
    df = pd.read_csv(ABM_PATH, sep=',', encoding='utf-8')
    combinations = get_column_combinations(df)
    embedding = OpenAIEmbeddings(api_key=OPENFARMA_API_KEY)
    
    # Process a database with all columns
    db_name, num_docs = process_database_combination(df, df.columns.tolist(), embedding, name="db_all")
    results = [(db_name, num_docs)]
    
    # Process each combination
    for cols in combinations:
        db_name, num_docs = process_database_combination(df, cols, embedding)
        results.append((db_name, num_docs))
    
    # Print summary
    print("\nResumen de actualización:")
    for db_name, num_docs in results:
        if num_docs > 0:
            print(f"- {db_name}: {num_docs} documentos procesados")

if __name__ == "__main__":
    process_csv_data()
