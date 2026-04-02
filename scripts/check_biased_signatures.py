#!/usr/bin/env sage -python
"""
Verification script for all supported nonce leakage modes
(Nguyen-Shparlinski 2003 partial nonce leakage)
"""

import csv
import argparse
import sage.all as sage
from src.lattice_attack.constants import N
from src.lattice_attack.ecdsa_generator import SUPPORTED_BIAS_TYPES

def check_biased_signatures(csv_file: str, bias_type: str, param: int, private_key: int):
    d = sage.ZZ(private_key) % N
    correct = 0
    total = 0
    known_parts = []

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

            # Verify according to bias type
            if bias_type == "known_lsb":
                expected = k % (1 << param) if param else sage.ZZ(0)
                match = (k != 0) and (known_part == expected)
            elif bias_type == "known_msb":
                b = 256 - param
                expected = k >> b
                match = (k != 0) and (known_part == expected)
            elif bias_type == "short":
                expected = k
                match = (known_part == expected) and (1 <= k < min(1 << param, N))
            elif bias_type == "shared_suffix":
                known_parts.append(known_part)
                expected = k % (1 << param) if param else sage.ZZ(0)
                match = (k != 0) and (known_part == expected)
            else:
                raise ValueError(f"Unknown bias_type: {bias_type}")

            total += 1
            if match:
                correct += 1

    # Final report
    print(f"\n=== Bias Check: {bias_type} (param={param}) ===")
    print(f"Signatures checked : {total}")
    print(f"Correct matches    : {correct}/{total} ({correct/total*100:.1f}%)")

    shared_suffix_consistent = True
    if bias_type == "shared_suffix":
        unique = len(set(known_parts))
        shared_suffix_consistent = unique == 1
        print(f"Unique known_parts : {unique} (should be 1)")
        print(f"All shared suffix? : {'YES' if shared_suffix_consistent else 'NO'}")
    elif bias_type == "short":
        print(f"All nonces ≤ {param} bits? : {'YES' if correct == total else 'NO'}")
    elif bias_type == "known_lsb":
        print(f"All known LSB match? : {'YES' if correct == total else 'NO'}")
    else:
        print(f"All known MSB match? : {'YES' if correct == total else 'NO'}")

    passed = (correct == total) and shared_suffix_consistent
    print(f"Overall verification : {'PASSED' if passed else 'FAILED'}")
    return passed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify any supported nonce leakage mode")
    parser.add_argument("--csv", required=True, help="Path to the CSV file")
    parser.add_argument("--bias", choices=SUPPORTED_BIAS_TYPES, required=True)
    parser.add_argument("--param", type=int, required=True)
    parser.add_argument("--key", type=int, default=0x123456789ABCDEF0123456789ABCDEF0)
    args = parser.parse_args()

    check_biased_signatures(args.csv, args.bias, args.param, args.key)
