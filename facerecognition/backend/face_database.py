"""
Face Database - stores and searches face embeddings.

Storage format (face_db.json):
{
    "people": {
        "Ali Yilmaz": {
            "embedding": [0.123, -0.456, ...],  // 512-d averaged embedding
            "num_samples": 8,
            "enrolled_at": "2026-04-15T18:00:00",
            "updated_at": "2026-04-15T18:00:00"
        },
        ...
    }
}
"""

import os
import json
import numpy as np
from datetime import datetime
try:
    from config import FACE_DB_PATH, ENROLLED_FACES_DIR, RECOGNITION_THRESHOLD
except ImportError:
    from .config import FACE_DB_PATH, ENROLLED_FACES_DIR, RECOGNITION_THRESHOLD


class FaceDatabase:
    """
    Manages face embeddings storage and search.
    Uses JSON file for simplicity (upgradeable to PostgreSQL + pgvector).
    """

    def __init__(self):
        self._ensure_dirs()
        self.db = self._load()
        print(f"[FaceDB] Loaded {len(self.db.get('people', {}))} enrolled people")

    def _ensure_dirs(self):
        """Create data directories if they don't exist."""
        os.makedirs(os.path.dirname(FACE_DB_PATH), exist_ok=True)
        os.makedirs(ENROLLED_FACES_DIR, exist_ok=True)

    def _load(self):
        """Load database from disk."""
        if os.path.exists(FACE_DB_PATH):
            with open(FACE_DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"people": {}}

    def _save(self):
        """Save database to disk."""
        with open(FACE_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(self.db, f, indent=2, ensure_ascii=False)

    def enroll(self, name, embeddings):
        """
        Enroll a person with their face embeddings.

        Args:
            name: Person's name (unique identifier)
            embeddings: list of numpy arrays (512-d each)

        Returns:
            dict with enrollment result
        """
        if len(embeddings) < 1:
            raise ValueError("At least 1 embedding required")

        # Average all embeddings for robust representation
        avg_embedding = np.mean(embeddings, axis=0)
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)

        now = datetime.now().isoformat()

        self.db["people"][name] = {
            "embedding": avg_embedding.tolist(),
            "num_samples": len(embeddings),
            "enrolled_at": now,
            "updated_at": now,
        }

        self._save()
        print(f"[FaceDB] Enrolled '{name}' with {len(embeddings)} samples")

        return {
            "name": name,
            "num_samples": len(embeddings),
            "enrolled_at": now,
        }

    def update(self, name, new_embeddings):
        """
        Update an existing person's embeddings by adding new samples.
        Recomputes the average embedding.

        Args:
            name: Person's name
            new_embeddings: list of new numpy arrays to add
        """
        if name not in self.db["people"]:
            raise ValueError(f"Person '{name}' not found")

        person = self.db["people"][name]
        old_embedding = np.array(person["embedding"])
        old_count = person["num_samples"]

        # Weighted average: keep old samples' contribution
        all_embeddings = [old_embedding * old_count] + list(new_embeddings)
        total_count = old_count + len(new_embeddings)

        avg_embedding = np.sum(all_embeddings, axis=0) / total_count
        avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)

        person["embedding"] = avg_embedding.tolist()
        person["num_samples"] = total_count
        person["updated_at"] = datetime.now().isoformat()

        self._save()
        print(f"[FaceDB] Updated '{name}': {total_count} total samples")

    def recognize(self, query_embedding, threshold=None):
        """
        Find the best matching person for a query embedding.

        Args:
            query_embedding: numpy array (512-d)
            threshold: minimum similarity score (default from config)

        Returns:
            dict: {"name": str, "score": float, "matched": bool}
        """
        if threshold is None:
            threshold = RECOGNITION_THRESHOLD

        query_embedding = np.array(query_embedding)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        best_name = "unknown"
        best_score = 0.0

        for name, person in self.db.get("people", {}).items():
            stored_emb = np.array(person["embedding"])
            similarity = float(np.dot(query_embedding, stored_emb))

            if similarity > best_score:
                best_score = similarity
                best_name = name

        matched = best_score >= threshold

        return {
            "name": best_name if matched else "unknown",
            "score": round(best_score, 4),
            "matched": matched,
        }

    def search_top_k(self, query_embedding, k=5):
        """
        Find top-k most similar people.

        Args:
            query_embedding: numpy array (512-d)
            k: number of results to return

        Returns:
            list of dicts: [{"name": str, "score": float}, ...]
        """
        query_embedding = np.array(query_embedding)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)

        scores = []
        for name, person in self.db.get("people", {}).items():
            stored_emb = np.array(person["embedding"])
            similarity = float(np.dot(query_embedding, stored_emb))
            scores.append({"name": name, "score": round(similarity, 4)})

        scores.sort(key=lambda x: x["score"], reverse=True)
        return scores[:k]

    def get_all_people(self):
        """
        Get list of all enrolled people.

        Returns:
            list of dicts with person info (without embeddings)
        """
        people = []
        for name, person in self.db.get("people", {}).items():
            people.append({
                "name": name,
                "num_samples": person["num_samples"],
                "enrolled_at": person["enrolled_at"],
                "updated_at": person["updated_at"],
            })
        return people

    def remove_person(self, name):
        """
        Remove a person from the database.

        Args:
            name: Person's name

        Returns:
            bool: True if removed, False if not found
        """
        if name in self.db["people"]:
            del self.db["people"][name]
            self._save()
            print(f"[FaceDB] Removed '{name}'")
            return True
        return False

    def clear(self):
        """Remove all enrolled people."""
        self.db = {"people": {}}
        self._save()
        print("[FaceDB] Cleared all entries")
