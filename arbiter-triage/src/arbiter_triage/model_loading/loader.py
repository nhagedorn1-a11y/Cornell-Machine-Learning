"""Model loading and verification for the Arbiter Triage Engine."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelLoader:
    """Loads and verifies ML models (ONNX router, spaCy NER) for the triage pipeline."""

    def __init__(self, model_dir: str = "/opt/arbiter/models") -> None:
        self._model_dir = Path(model_dir)
        self._router_session = None
        self._ner_model = None
        self._router_loaded = False
        self._ner_loaded = False

    # ------------------------------------------------------------------
    # Router model (ONNX)
    # ------------------------------------------------------------------

    async def load_router_model(self) -> bool:
        """Load the ONNX router model and verify its SHA-256 checksum.

        Returns True if the model was loaded successfully, False otherwise.
        Never raises on failure -- logs a warning instead.
        """
        try:
            import onnxruntime as ort  # noqa: F811

            model_path = self._model_dir / "router.onnx"
            checksums_path = self._model_dir / "checksums.sha256"

            if not model_path.exists():
                logger.warning("Router model not found at %s", model_path)
                return False

            # Verify SHA-256 hash if checksums file is available
            if checksums_path.exists():
                if not self._verify_checksum(model_path, checksums_path):
                    logger.warning(
                        "SHA-256 checksum verification failed for %s", model_path
                    )
                    return False
            else:
                logger.warning(
                    "No checksums file found at %s -- skipping verification",
                    checksums_path,
                )

            self._router_session = ort.InferenceSession(str(model_path))
            self._router_loaded = True
            logger.info("Router model loaded from %s", model_path)
            return True

        except Exception:
            logger.warning("Failed to load router model", exc_info=True)
            self._router_loaded = False
            return False

    # ------------------------------------------------------------------
    # NER model (spaCy)
    # ------------------------------------------------------------------

    async def load_ner_model(self, vertical_pack: str = "GENERIC") -> bool:
        """Load a spaCy NER model for the given vertical pack.

        Returns True if the model was loaded successfully, False otherwise.
        """
        try:
            import spacy  # noqa: F811

            model_name = f"ner_{vertical_pack.lower()}"
            model_path = self._model_dir / model_name

            if model_path.exists():
                self._ner_model = spacy.load(str(model_path))
            else:
                # Fall back to default English model
                logger.info(
                    "Vertical NER model %s not found, falling back to en_core_web_sm",
                    model_name,
                )
                self._ner_model = spacy.load("en_core_web_sm")

            self._ner_loaded = True
            logger.info("NER model loaded (vertical_pack=%s)", vertical_pack)
            return True

        except Exception:
            logger.warning("Failed to load NER model", exc_info=True)
            self._ner_loaded = False
            return False

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def is_router_available(self) -> bool:
        """Return True if the router ONNX model is loaded and ready."""
        return self._router_loaded and self._router_session is not None

    def is_ner_available(self) -> bool:
        """Return True if the NER model is loaded and ready."""
        return self._ner_loaded and self._ner_model is not None

    async def get_router_session(self):
        """Return the ONNX InferenceSession for the router, or None."""
        return self._router_session

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _verify_checksum(model_path: Path, checksums_path: Path) -> bool:
        """Verify the SHA-256 hash of *model_path* against *checksums_path*.

        The checksums file is expected to have lines of the form:
            <hex_digest>  <filename>
        """
        try:
            sha256 = hashlib.sha256()
            with open(model_path, "rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    sha256.update(chunk)
            computed = sha256.hexdigest()

            with open(checksums_path, "r") as fh:
                for line in fh:
                    parts = line.strip().split()
                    if len(parts) >= 2 and parts[1] == model_path.name:
                        return parts[0] == computed

            logger.warning(
                "No checksum entry found for %s in %s",
                model_path.name,
                checksums_path,
            )
            return False
        except Exception:
            logger.warning("Checksum verification error", exc_info=True)
            return False
