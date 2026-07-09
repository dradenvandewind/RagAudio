"""
Indexation et interrogation RAG avec LlamaIndex, propulsé par Ollama.

100% local, sans clé API : LLM et embeddings tournent via un serveur
Ollama (local ou conteneur dédié), configurable via variables d'env :

    OLLAMA_BASE_URL   (défaut: http://localhost:11434)
    OLLAMA_LLM_MODEL  (défaut: llama3.1)
    OLLAMA_EMBED_MODEL(défaut: nomic-embed-text)

Les modèles doivent être présents côté serveur Ollama, ex:
    ollama pull llama3.1
    ollama pull nomic-embed-text
"""
import os
from typing import Optional

from llama_index.core import (
    VectorStoreIndex,
    Document,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding


class RAGEngine:
    def __init__(
        self,
        persist_dir: str,
        llm_model: Optional[str] = None,
        embed_model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.persist_dir = persist_dir

        base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        llm_model = llm_model or os.getenv("OLLAMA_LLM_MODEL", "llama3.1")
        embed_model = embed_model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

        Settings.llm = Ollama(model=llm_model, base_url=base_url, request_timeout=180.0)
        Settings.embed_model = OllamaEmbedding(model_name=embed_model, base_url=base_url)

        if os.path.exists(persist_dir) and os.listdir(persist_dir):
            storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
            self.index = load_index_from_storage(storage_context)
        else:
            self.index = VectorStoreIndex.from_documents([])
            self.index.storage_context.persist(persist_dir=persist_dir)

    def add_document(self, doc_id: str, text: str, metadata: Optional[dict] = None):
        """Ajoute une transcription à l'index et persiste sur disque."""
        doc = Document(text=text, doc_id=doc_id, metadata=metadata or {})
        self.index.insert(doc)
        self.index.storage_context.persist(persist_dir=self.persist_dir)

    def query(self, question: str, top_k: int = 4):
        """Interroge l'index et retourne (réponse, sources)."""
        query_engine = self.index.as_query_engine(similarity_top_k=top_k)
        response = query_engine.query(question)

        sources = []
        for node in response.source_nodes:
            src = node.metadata.get("source_url", node.node_id)
            if src not in sources:
                sources.append(src)

        return str(response), sources
