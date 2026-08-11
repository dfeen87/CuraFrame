# Copyright (c) Don Michael Feeney Jr. Licensed under the MIT License.
from __future__ import annotations

from typing import List, Tuple


def get_available_bundles() -> List[Tuple[str, str]]:
    return [
        ("core-safety", "Core Safety"),
        ("lipinski", "Lipinski Ro5"),
        ("cns", "CNS Constraints"),
        ("cardiology", "Cardiology-Oriented"),
        ("cardianx", "CardiAnx Dual-Domain"),
        ("oncology", "Oncology"),
        ("anti-infective", "Anti-Infective"),
        ("metabolic-disease", "Metabolic Disease"),
    ]
