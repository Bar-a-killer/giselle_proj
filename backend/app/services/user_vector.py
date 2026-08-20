from typing import Protocol

import numpy as np


class UserEmbedder(Protocol):
    """Turns a user's liked-venue vectors into one preference vector.

    Swappable seam: a trained two-tower "user tower" can implement this
    interface later without touching scoring.py or the API layer.
    """

    def embed_user(self, liked_venue_vectors: list[np.ndarray]) -> np.ndarray | None: ...


class CentroidUserEmbedder:
    def embed_user(self, liked_venue_vectors: list[np.ndarray]) -> np.ndarray | None:
        if not liked_venue_vectors:
            return None
        centroid = np.mean(np.stack(liked_venue_vectors), axis=0)
        norm = np.linalg.norm(centroid)
        if norm == 0:
            return None
        return centroid / norm


def get_user_embedder() -> UserEmbedder:
    return CentroidUserEmbedder()
