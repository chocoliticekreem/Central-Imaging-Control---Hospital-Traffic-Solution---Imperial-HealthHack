"""
Re-ID (Re-Identification) Module
================================
Extracts visual signatures from people and matches them across frames.

For hackathon MVP: Uses color histogram of clothing as signature.
Future: Could use deep learning embeddings (torchreid, etc.)
"""

import numpy as np
import cv2
from typing import Optional, Tuple, List
from dataclasses import dataclass


@dataclass
class ReIDMatch:
    """Result of a Re-ID matching attempt."""
    patient_id: str
    confidence: float  # 0-1, higher = better match
    signature: np.ndarray


class ReIDExtractor:
    """
    Extracts visual signatures from person crops.

    Uses color histogram of upper body (clothing) as a simple but
    effective signature for short-term re-identification.
    """

    def __init__(self, hist_bins: int = 32):
        """
        Args:
            hist_bins: Number of bins per channel for color histogram
        """
        self.hist_bins = hist_bins

    def extract_signature(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extract Re-ID signature from a person's bounding box.

        Args:
            frame: Full BGR image
            bbox: (x1, y1, x2, y2) bounding box

        Returns:
            Flattened color histogram as signature vector
        """
        x1, y1, x2, y2 = bbox

        # Get upper body region (torso - where clothing is visible)
        h = y2 - y1
        torso_y1 = y1 + int(h * 0.15)  # Skip head
        torso_y2 = y1 + int(h * 0.6)   # Upper 60%

        # Crop region
        crop = frame[torso_y1:torso_y2, x1:x2]

        if crop.size == 0:
            return np.zeros(self.hist_bins * 3)

        # Convert to HSV for better color matching
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        # Calculate histogram for each channel
        hist_h = cv2.calcHist([hsv], [0], None, [self.hist_bins], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [self.hist_bins], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [self.hist_bins], [0, 256])

        # Normalize histograms
        cv2.normalize(hist_h, hist_h)
        cv2.normalize(hist_s, hist_s)
        cv2.normalize(hist_v, hist_v)

        # Concatenate into single signature
        signature = np.concatenate([hist_h, hist_s, hist_v]).flatten()

        return signature


class ReIDMatcher:
    """
    Matches tracked people against enrolled patient signatures.
    """

    def __init__(self, threshold: float = 0.6):
        """
        Args:
            threshold: Minimum similarity (0-1) to consider a match
        """
        self.threshold = threshold
        self.extractor = ReIDExtractor()

        # Enrolled patient signatures: patient_id -> signature
        self._enrolled: dict[str, np.ndarray] = {}

    def enroll(self, patient_id: str, signature: np.ndarray):
        """
        Enroll a patient with their visual signature.

        Called when nurse captures patient's appearance at intake.
        """
        # Normalize signature
        norm = np.linalg.norm(signature)
        if norm > 0:
            signature = signature / norm
        self._enrolled[patient_id] = signature

    def enroll_from_frame(self, patient_id: str, frame: np.ndarray, bbox: Tuple[int, int, int, int]):
        """
        Enroll a patient by extracting signature from current frame.
        """
        signature = self.extractor.extract_signature(frame, bbox)
        self.enroll(patient_id, signature)

    def unenroll(self, patient_id: str):
        """Remove a patient's enrollment (e.g., on discharge)."""
        if patient_id in self._enrolled:
            del self._enrolled[patient_id]

    def match(self, signature: np.ndarray) -> Optional[ReIDMatch]:
        """
        Find the best matching enrolled patient for a signature.

        Args:
            signature: Visual signature to match

        Returns:
            ReIDMatch if found above threshold, None otherwise
        """
        if len(self._enrolled) == 0:
            return None

        # Normalize input signature
        norm = np.linalg.norm(signature)
        if norm > 0:
            signature = signature / norm

        best_match = None
        best_score = 0.0

        for patient_id, enrolled_sig in self._enrolled.items():
            # Cosine similarity
            similarity = np.dot(signature, enrolled_sig)

            if similarity > best_score:
                best_score = similarity
                best_match = patient_id

        if best_score >= self.threshold and best_match:
            return ReIDMatch(
                patient_id=best_match,
                confidence=best_score,
                signature=signature
            )

        return None

    def match_from_frame(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[ReIDMatch]:
        """
        Extract signature and match in one step.
        """
        signature = self.extractor.extract_signature(frame, bbox)
        return self.match(signature)

    def get_enrolled_ids(self) -> List[str]:
        """Get list of enrolled patient IDs."""
        return list(self._enrolled.keys())

    def is_enrolled(self, patient_id: str) -> bool:
        """Check if a patient is enrolled."""
        return patient_id in self._enrolled
