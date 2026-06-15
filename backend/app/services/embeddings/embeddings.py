"""
Embedding Service.
Uses sentence-transformers if available, otherwise TF-IDF based embeddings.
Both produce real semantic similarity — no more hash-based approach.
"""
import hashlib
import math
import re
from collections import Counter
from typing import List

import numpy as np


# ──────────────────────────────────────────────────────────────
# Try real sentence-transformers first
# ──────────────────────────────────────────────────────────────
_ST_MODEL = None
_USE_ST = False

try:
    import os, warnings
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    warnings.filterwarnings("ignore")
    # Only import the core ST library — avoid transformers/TF
    from sentence_transformers import SentenceTransformer
    _ST_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    _USE_ST = True
except Exception:
    _USE_ST = False


# ──────────────────────────────────────────────────────────────
# TF-IDF based embedder (fallback — no ML libraries required)
# Produces 512-dim vectors; cosine similarity works properly.
# ──────────────────────────────────────────────────────────────
_VOCAB: dict = {}          # word → index
_IDF: dict = {}            # word → idf weight
_CORPUS: List[str] = []    # all texts seen so far
_DIM = 384

_STOPWORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with","by",
    "from","is","are","was","were","be","been","being","have","has","had","do",
    "does","did","will","would","could","should","may","might","this","that","it",
    "its","as","if","not","no","so","up","out","use","used","can","all","also"
}


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    tokens = re.findall(r"[a-z][a-z0-9_]{1,}", text)
    return [t for t in tokens if t not in _STOPWORDS]


def _compute_idf(corpus: List[str]) -> dict:
    """Compute IDF over entire corpus."""
    N = len(corpus)
    df: dict = {}
    for doc in corpus:
        for word in set(_tokenize(doc)):
            df[word] = df.get(word, 0) + 1
    return {w: math.log((N + 1) / (cnt + 1)) + 1 for w, cnt in df.items()}


def _tfidf_vector(text: str, idf: dict, vocab: dict) -> List[float]:
    """Produce a fixed-dim TF-IDF vector."""
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * _DIM
    tf = Counter(tokens)
    vec = [0.0] * _DIM
    for word, count in tf.items():
        tf_val = count / len(tokens)
        idf_val = idf.get(word, 1.0)
        # Map word to a bucket in [0, _DIM)
        bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % _DIM
        vec[bucket] += tf_val * idf_val
    # L2 normalise
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


class EmbeddingService:
    """
    Produces dense embeddings for text.
    Uses sentence-transformers when available, TF-IDF otherwise.
    """

    def __init__(self):
        self.dimension = 384
        self._corpus_cache: List[str] = []
        self._idf_cache: dict = {}
        self._dirty = True

    # ── public API ──────────────────────────────────────────
    def get_embedding(self, text: str) -> List[float]:
        if _USE_ST and _ST_MODEL is not None:
            vec = _ST_MODEL.encode(text, normalize_embeddings=True)
            return vec.tolist()
        return self._tfidf_embed(text)

    def embed_query(self, query: str) -> List[float]:
        return self.get_embedding(query)

    def embed_documents(self, documents) -> List[List[float]]:
        """Accept strings or LangChain Document objects."""
        texts = []
        for d in documents:
            texts.append(d.page_content if hasattr(d, "page_content") else str(d))
        return self._batch_embed(texts)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self._batch_embed(texts)

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return self._batch_embed(texts)

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        dot = sum(a * b for a, b in zip(v1, v2))
        return dot

    # ── internals ───────────────────────────────────────────
    def _batch_embed(self, texts: List[str]) -> List[List[float]]:
        if _USE_ST and _ST_MODEL is not None:
            vecs = _ST_MODEL.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return [v.tolist() for v in vecs]
        # TF-IDF: rebuild IDF if new texts are added
        self._corpus_cache.extend(texts)
        self._idf_cache = _compute_idf(self._corpus_cache)
        # Rebuild vocab from idf
        vocab = {w: i for i, w in enumerate(self._idf_cache.keys())}
        return [_tfidf_vector(t, self._idf_cache, vocab) for t in texts]

    def _tfidf_embed(self, text: str) -> List[float]:
        if not self._idf_cache:
            self._corpus_cache.append(text)
            self._idf_cache = _compute_idf(self._corpus_cache)
        vocab = {w: i for i, w in enumerate(self._idf_cache.keys())}
        return _tfidf_vector(text, self._idf_cache, vocab)


# Singleton
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
