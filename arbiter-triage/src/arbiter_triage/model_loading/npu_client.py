"""NPU inference client via ONNX Runtime.

Attempts to use an NPU execution provider for hardware-accelerated inference.
Falls back transparently to CPU if NPU is unavailable.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

# Severity-level weights used to collapse a 5-class probability distribution
# into a single 0-100 exposure score.
_EXPOSURE_WEIGHTS: list[float] = [0.0, 25.0, 50.0, 75.0, 100.0]

# Labels corresponding to each output index.
SEVERITY_LABELS: list[str] = [
    "NONE",
    "MINIMAL",
    "MODERATE",
    "SIGNIFICANT",
    "ESSENTIAL",
]


class NPUClient:
    """Thin wrapper around ONNX Runtime that prefers NPU acceleration."""

    def __init__(self) -> None:
        self._session = None
        self._is_npu = False
        self._available = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def initialize(self, model_path: str) -> bool:
        """Create an ONNX InferenceSession, preferring NPU over CPU.

        Returns True if the session was created (on either provider).
        """
        try:
            import onnxruntime as ort

            # Try NPU first, then fall back to CPU
            npu_providers = ["VitisAIExecutionProvider", "QNNExecutionProvider"]
            cpu_providers = ["CPUExecutionProvider"]

            for provider in npu_providers:
                if provider in ort.get_available_providers():
                    try:
                        self._session = ort.InferenceSession(
                            model_path, providers=[provider]
                        )
                        self._is_npu = True
                        self._available = True
                        logger.info(
                            "ONNX session initialized on NPU (%s)", provider
                        )
                        return True
                    except Exception:
                        logger.debug(
                            "NPU provider %s failed, trying next", provider
                        )

            # CPU fallback
            self._session = ort.InferenceSession(
                model_path, providers=cpu_providers
            )
            self._is_npu = False
            self._available = True
            logger.warning(
                "No NPU provider available -- running in degraded CPU mode"
            )
            return True

        except Exception:
            logger.warning("Failed to initialize ONNX session", exc_info=True)
            self._available = False
            return False

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    async def infer(self, input_data: dict) -> list[float] | None:
        """Run inference and return a probability distribution.

        The distribution has five elements corresponding to
        [NONE, MINIMAL, MODERATE, SIGNIFICANT, ESSENTIAL].

        Returns None on failure.
        """
        if not self._available or self._session is None:
            logger.warning("Inference requested but ONNX session is not available")
            return None

        try:
            # Build the feed dict expected by the ONNX model.
            # The caller is responsible for providing numpy-compatible values
            # keyed by input node name.
            feed = {}
            for inp in self._session.get_inputs():
                if inp.name in input_data:
                    value = input_data[inp.name]
                    if not isinstance(value, np.ndarray):
                        value = np.array(value, dtype=np.float32)
                    feed[inp.name] = value

            output_names = [o.name for o in self._session.get_outputs()]
            results = self._session.run(output_names, feed)

            # Expect the first output to be the probability distribution.
            probs = results[0]
            if hasattr(probs, "tolist"):
                probs = probs.tolist()

            # Flatten if nested (e.g. batch dim of 1)
            if isinstance(probs, list) and len(probs) == 1 and isinstance(probs[0], list):
                probs = probs[0]

            return probs

        except Exception:
            logger.warning("ONNX inference failed", exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    @staticmethod
    def compute_exposure_score(probs: list[float]) -> float:
        """Compute a weighted exposure score in [0, 100] from class probabilities.

        weights = [0, 25, 50, 75, 100]  (one per severity level)
        score = sum(p_i * w_i)
        """
        if not probs or len(probs) != len(_EXPOSURE_WEIGHTS):
            return 0.0
        return sum(p * w for p, w in zip(probs, _EXPOSURE_WEIGHTS))

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_npu(self) -> bool:
        """True if the session is running on an NPU, False if CPU fallback."""
        return self._is_npu

    @property
    def available(self) -> bool:
        """True if the ONNX session is initialized and ready for inference."""
        return self._available
