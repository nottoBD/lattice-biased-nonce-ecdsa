#!/usr/bin/env sage -python
"""
Verification script for known_lsb nonce leakage
(Nguyen-Shparlinski 2003 partial nonce leakage).
"""

import csv
import argparse
import sage.all as sage
from src.lattice_attack.constants import N


def check_biased_signatures(csv_file: str, param: int, private_key: int):
    d = sage.ZZ(private_key) % N
    correct = 0
    total = 0

    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = sage.ZZ(row["r"])
            s = sage.ZZ(row["s"])
            h = sage.ZZ(row["h"])
            known_part = sage.ZZ(row["known_part"])

            # Recover real nonce k
            inv_s = sage.inverse_mod(s, N)
            k = (inv_s * (h + d * r)) % N

            expected = k % (1 << param) if param else sage.ZZ(0)
            match = (k != 0) and (known_part == expected)

            total += 1
            if match:
                correct += 1

    # Final report
    print(f"\n=== Bias Check: known_lsb (param={param}) ===")
    print(f"Signatures checked : {total}")
    print(f"Correct matches    : {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"All known LSB match? : {'YES' if correct == total else 'NO'}")
    passed = correct == total
    print(f"Overall verification : {'PASSED' if passed else 'FAILED'}")
    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify a known_lsb nonce leakage dataset")
    parser.add_argument("--csv", required=True, help="Path to the CSV file")
    parser.add_argument("--param", "--ell", dest="param", type=int, required=True)
    parser.add_argument("--key", type=int, default=0x123456789ABCDEF0123456789ABCDEF0)
    args = parser.parse_args()

    check_biased_signatures(args.csv, args.param, args.key)
