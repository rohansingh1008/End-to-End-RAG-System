import os
from typing import List
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyMuPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    CSVLoader
)

class UniversalDocumentLoader:
    @staticmethod
    def load_file(file_path: str, original_filename: str) -> List[Document]:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            loader = PyMuPDFLoader(file_path)
        elif ext in [".txt", ".md"]:
            loader = TextLoader(file_path, encoding="utf-8")
        elif ext == ".docx":
            loader = UnstructuredWordDocumentLoader(file_path)
        elif ext == ".csv":
            loader = CSVLoader(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        documents = loader.load()
        for doc in documents:
            doc.metadata["source_file"] = original_filename
            doc.metadata["file_type"] = ext.replace(".", "")
            
        return documents