import numpy as np


def angle_between(a, b, c) -> float:
    """b noktasındaki a-b-c açısı (derece, 0-180)."""
    a, b, c = (np.asarray(p, dtype=float) for p in (a, b, c))
    ba, bc = a - b, c - b
    denom = np.linalg.norm(ba) * np.linalg.norm(bc)
    if denom == 0:
        return 0.0
    cos = np.clip(np.dot(ba, bc) / denom, -1.0, 1.0)
    return float(np.degrees(np.arccos(cos)))


def angle_from_vertical(top, bottom) -> float:
    """bottom->top vektörünün dikeyle yaptığı açı (derece). Görüntüde y aşağı doğrudur."""
    top, bottom = np.asarray(top, dtype=float), np.asarray(bottom, dtype=float)
    v = top - bottom
    n = np.linalg.norm(v)
    if n == 0:
        return 0.0
    return float(np.degrees(np.arccos(np.clip(-v[1] / n, -1.0, 1.0))))
