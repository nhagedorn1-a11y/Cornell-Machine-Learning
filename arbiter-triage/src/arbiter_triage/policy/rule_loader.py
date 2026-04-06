"""Load and verify signed rule files for vertical packs."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_POLICY_DIR = Path(__file__).parent / "vertical_packs"


class RuleLoader:
    """Loads vertical-pack rule files (.rules) and extracts patterns."""

    def __init__(self, policy_dir: str | None = None) -> None:
        self._policy_dir = Path(policy_dir) if policy_dir else _DEFAULT_POLICY_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def load_vertical_rules(self, vertical_pack: str) -> list[dict]:
        """Load rules from the .rules file for *vertical_pack*.

        Each .rules file is JSON-lines (one JSON object per line).
        Returns an empty list if the file is missing or unparseable.
        """
        rules_path = self._policy_dir / f"{vertical_pack.lower()}.rules"

        if not rules_path.exists():
            logger.warning("Rules file not found: %s", rules_path)
            return []

        if not self.verify_signature(str(rules_path)):
            logger.warning(
                "Signature verification failed for %s -- loading anyway (dev mode)",
                rules_path,
            )

        rules: list[dict] = []
        try:
            with open(rules_path, "r") as fh:
                for lineno, line in enumerate(fh, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rules.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(
                            "Skipping malformed JSON on line %d of %s",
                            lineno,
                            rules_path,
                        )
        except Exception:
            logger.warning("Failed to read rules file %s", rules_path, exc_info=True)

        logger.info(
            "Loaded %d rules from %s", len(rules), rules_path.name
        )
        return rules

    def verify_signature(self, rules_path: str) -> bool:
        """Verify the cryptographic signature of a rules file.

        In production this would check an Ed25519 (or similar) detached
        signature stored in a companion ``.sig`` file.  For now we only
        check that the ``.sig`` file exists.
        """
        sig_path = Path(rules_path).with_suffix(".sig")
        if sig_path.exists():
            logger.debug("Signature file found: %s", sig_path)
            return True

        logger.warning(
            "No signature file found for %s (expected %s)", rules_path, sig_path
        )
        return False

    def get_additional_red_patterns(self, vertical_pack: str) -> list[str]:
        """Return ALWAYS_RED regex patterns defined in *vertical_pack*.

        This is a synchronous convenience wrapper that reads the rules file
        directly and filters for ``type == "ALWAYS_RED"``.
        """
        rules_path = self._policy_dir / f"{vertical_pack.lower()}.rules"
        patterns: list[str] = []

        if not rules_path.exists():
            return patterns

        try:
            with open(rules_path, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rule = json.loads(line)
                        if rule.get("type") == "ALWAYS_RED" and "pattern" in rule:
                            patterns.append(rule["pattern"])
                    except json.JSONDecodeError:
                        continue
        except Exception:
            logger.warning(
                "Error reading patterns from %s", rules_path, exc_info=True
            )

        return patterns
