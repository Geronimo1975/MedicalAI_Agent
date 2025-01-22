import os
from pathlib import Path
from typing import List, Optional
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import torch

class DocumentProcessor:
    def __init__(self, docs_dir: str = "attached_assets"):
        self.docs_dir = Path(docs_dir)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cuda' if torch.cuda.is_available() else 'cpu'}
        )
        self.vector_store = None
        self.initialize_vector_store()

    def initialize_vector_store(self):
        """Initialize or load the vector store with medical documentation."""
        if not self.docs_dir.exists():
            raise FileNotFoundError(f"Documents directory {self.docs_dir} not found")

        documents = []
        for pdf_file in self.docs_dir.glob("*.pdf"):
            try:
                loader = PyPDFLoader(str(pdf_file))
                documents.extend(loader.load())
            except Exception as e:
                print(f"Error loading {pdf_file}: {str(e)}")

        if documents:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            texts = text_splitter.split_documents(documents)
            
            # Create vector store
            self.vector_store = FAISS.from_documents(texts, self.embeddings)

    def search_documentation(self, query: str, k: int = 3) -> List[str]:
        """Search the documentation for relevant context based on the query."""
        if not self.vector_store:
            return []

        results = self.vector_store.similarity_search(query, k=k)
        return [doc.page_content for doc in results]

    def get_relevant_context(self, query: str) -> str:
        """Get relevant context from the documentation for a given query."""
        results = self.search_documentation(query)
        if not results:
            return "No relevant information found in the medical documentation."
        
        # Combine the results into a single context string
        context = "\n\n".join(results)
        return f"Based on the medical documentation:\n\n{context}"
