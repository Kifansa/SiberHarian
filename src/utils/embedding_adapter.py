from typing import List, Optional
from src.utils.llm_adapter import GeminiLLMAdapter
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GeminiEmbeddingAdapter:
    """Interface adapter untuk embedding teks tunggal dan batch menggunakan Gemini API."""

    @classmethod
    def embed(cls, text: str) -> Optional[List[float]]:
        """Menghasilkan vector embedding untuk satu string teks."""
        try:
            res = GeminiLLMAdapter.embed_text(text)
            return res if res else None
        except Exception as e:
            logger.error(f"Embedding gagal: {e}")
            return None

    @classmethod
    def embed_batch(cls, texts: List[str], batch_size: int = 50) -> List[Optional[List[float]]]:
        """Menghasilkan vector embedding untuk kumpulan teks dalam batch terpadu."""
        try:
            return GeminiLLMAdapter.embed_documents(texts, batch_size=batch_size)
        except Exception as e:
            logger.error(f"Batch embedding gagal: {e}")
            return [None] * len(texts)

    @classmethod
    def reload_config(cls) -> None:
        GeminiLLMAdapter.reload_config()
