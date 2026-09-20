"""Advisory-augmented F2; weights are declared preferences, not measured utility."""
import numpy as np

ADVISORY_WEIGHT = 1.0
SENSITIVITY_WEIGHTS = (0.5, 1.0, 2.0)

def advisory_f2(tp, denominator, advisories, penalties, weight=ADVISORY_WEIGHT):
    """Pooled-count score. Advisories get positive credit; unsupported findings a penalty.

    Reuses F2's five numerator units per bug. Does not change bug recall or assert
    an advisory recall denominator. With no advisories it reduces to bug-only F2.
    """
    num = 5 * np.asarray(tp) + weight * np.asarray(advisories)
    den = 4 * np.asarray(denominator) + tp + weight * np.asarray(advisories) + penalties
    return np.divide(num, den, out=np.zeros_like(num, dtype=float), where=den > 0)
