import os, shutil, csv
import streamlit as st
from dotenv import load_dotenv
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from openfarma.src.params import PRODUCTS_PATH, CHROMA_DB_PATH

load_dotenv()

OPENFARMA_API_KEY = os.getenv("OPENFARMA_API_KEY")

# Check if the directory exists and remove it
if os.path.exists(CHROMA_DB_PATH):
    shutil.rmtree(CHROMA_DB_PATH)

# Build documents
documents = []

try:
    with open(PRODUCTS_PATH, "r", encoding="utf-8") as file:
        read_csv = csv.reader(file)
        next(read_csv)  # skip header
        for row in read_csv:
            ean = row[0].strip() if row[0] else ""
            brand = row[1].strip() if row[1] else ""
            description = row[2].strip() if row[2] else ""
            documents.append(
                Document(
                    metadata={"Marca": brand, "EAN": ean}, page_content=description
                )
            )
        print(f"{len(documents)} documentos añadidos desde el archivo {PRODUCTS_PATH}.")
except Exception as e:
    print(f"Error procesando el archivo {PRODUCTS_PATH}: {e}")

# Build the vector database
embedding = OpenAIEmbeddings(api_key=OPENFARMA_API_KEY)
smalldb = Chroma.from_documents(
    documents=documents, embedding=embedding, persist_directory=CHROMA_DB_PATH
)
size = len(smalldb.get()["ids"])
print(f"Embeddings completados. Base de datos Chroma lista con {size} documentos.")
