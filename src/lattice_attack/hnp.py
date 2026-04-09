import csv
import os
import re
from typing import Dict, List, Optional

from .constants import N


DEFAULT_PRIVATE_KEY = 0x123456789ABCDEF0123456789ABCDEF0
KNOWN_LSB_FILENAME_RE = re.compile(r"known_lsb_(\d+)(?:\.[^.]+)?$")


def centered_mod(value: int, modulus: int) -> int:
    value %= modulus
    if value > modulus // 2:
        value -= modulus
    return value


def known_lsb_bound(ell: int, modulus: int = N) -> int:
    if not 0 <= ell <= 256:
        raise ValueError("ell must be between 0 and 256 inclusive.")
    return (modulus - 1) // (1 << ell if ell else 1)


def infer_known_lsb_ell(csv_file: str) -> Optional[int]:
    basename = os.path.basename(csv_file)
    match = KNOWN_LSB_FILENAME_RE.search(basename)
    if not match:
        return None
    return int(match.group(1))


def looks_like_known_lsb_dataset(csv_file: str) -> bool:
    return "known_lsb" in os.path.basename(csv_file)


def load_signature_rows(csv_file: str, num_samples: Optional[int] = None) -> List[Dict[str, int]]:
    rows: List[Dict[str, int]] = []

    with open(csv_file, newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"r", "s", "h", "known_part"}
        missing = required.difference(reader.fieldnames or [])
        if missing:
            missing_str = ", ".join(sorted(missing))
            raise ValueError(f"CSV file is missing required columns: {missing_str}")

        for index, row in enumerate(reader, start=1):
            rows.append(
                {
                    "index": index,
                    "r": int(row["r"]),
                    "s": int(row["s"]),
                    "h": int(row["h"]),
                    "known_part": int(row["known_part"]),
                }
            )
            if num_samples is not None and len(rows) >= num_samples:
                break

    return rows


def compute_known_lsb_hnp_rows(
    csv_file: str,
    ell: int,
    num_samples: Optional[int] = None,
) -> List[Dict[str, int]]:
    rows = load_signature_rows(csv_file, num_samples=num_samples)
    two_inv_ell = pow(pow(2, ell, N), -1, N)
    leakage_modulus = 1 << ell if ell else 1
    enriched_rows: List[Dict[str, int]] = []

    for row in rows:
        s_inv = pow(row["s"], -1, N)
        alpha = row["known_part"] % N
        t_i = (two_inv_ell * row["r"] * s_inv) % N
        u_i = (two_inv_ell * ((alpha - (s_inv * row["h"])) % N)) % N

        enriched_row = dict(row)
        enriched_row.update(
            {
                "alpha": alpha,
                "alpha_in_range": 0 <= row["known_part"] < leakage_modulus,
                "t_i": t_i,
                "u_i": u_i,
            }
        )
        enriched_rows.append(enriched_row)

    return enriched_rows


def diagnose_candidate(candidate: int, rows: List[Dict[str, int]], ell: int, modulus: int = N) -> Dict[str, int]:
    residues = [centered_mod((candidate * row["t_i"] - row["u_i"]) % modulus, modulus) for row in rows]
    max_abs_residue = max((abs(value) for value in residues), default=0)
    sum_sq_residue = sum(value * value for value in residues)
    return {
        "candidate": candidate % modulus,
        "max_abs_residue": max_abs_residue,
        "sum_sq_residue": sum_sq_residue,
        "within_bound": max_abs_residue <= known_lsb_bound(ell, modulus),
    }
