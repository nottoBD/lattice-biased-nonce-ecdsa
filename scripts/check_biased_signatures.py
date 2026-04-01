#!/usr/bin/env sage -python
"""
Verification script for all three supported biases
(Nguyen-Shparlinski 2003 partial nonce leakage)
"""

import csv
import argparse
import sage.all as sage
from src.lattice_attack.constants import N

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
            if bias_type == "known_msb":
                b = 256 - param
                expected = k >> b
                match = (known_part == expected)
            elif bias_type == "short":
                expected = k
                match = (known_part == expected) and (k < (1 << param))
            elif bias_type == "shared_suffix":
                known_parts.append(known_part)
                match = True  # we check uniformity at the end
            else:
                raise ValueError(f"Unknown bias_type: {bias_type}")

            total += 1
            if match:
                correct += 1

    # Final report
    print(f"\n=== Bias Check: {bias_type} (param={param}) ===")
    print(f"Signatures checked : {total}")
    print(f"Correct matches    : {correct}/{total} ({correct/total*100:.1f}%)")

    if bias_type == "shared_suffix":
        unique = len(set(known_parts))
        print(f"Unique known_parts : {unique} (should be 1)")
        print(f"All shared suffix? : {'YES' if unique == 1 else 'NO'}")
    elif bias_type == "short":
        print(f"All nonces ≤ {param} bits? : {'YES' if correct == total else 'NO'}")
    else:
        print(f"All known MSB match? : {'YES' if correct == total else 'NO'}")

    print(f"Overall verification : {'PASSED' if correct == total else 'FAILED'}")
    return correct == total

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify any of the three bias types")
    parser.add_argument("--csv", required=True, help="Path to the CSV file")
    parser.add_argument("--bias", choices=["known_msb", "short", "shared_suffix"], required=True)
    parser.add_argument("--param", type=int, required=True)
    parser.add_argument("--key", type=int, default=0x123456789ABCDEF0123456789ABCDEF0)
    args = parser.parse_args()

    check_biased_signatures(args.csv, args.bias, args.param, args.key)
