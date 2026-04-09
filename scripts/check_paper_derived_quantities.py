#!/usr/bin/env python3
"""
Compute the Nguyen-Shparlinski derived quantities for partially known ECDSA nonces.

For each CSV row with columns r, s, h, known_part, this script computes:

    t_i = 2^{-ell} * r_i * s_i^{-1} mod N
    u_i = 2^{-ell} * (alpha_i - s_i^{-1} * h_i) mod N

and verifies that a * t_i - u_i is small modulo N in the centered sense.

This matches the paper's known-LSB formulation:

    k_i = 2^ell * b_i + alpha_i
    alpha_i = known_part = k_i mod 2^ell

For a valid known_lsb dataset, the centered residue of a * t_i - u_i equals b_i
and is bounded by roughly N / 2^ell.
"""

import argparse
import csv
from src.lattice_attack.constants import N
from src.lattice_attack.hnp import (
    DEFAULT_PRIVATE_KEY,
    centered_mod,
    compute_known_lsb_hnp_rows,
    known_lsb_bound,
)


def compute_quantities(csv_file: str, private_key: int, ell: int):
    modulus = 1 << ell if ell else 1
    rows = []

    for row in compute_known_lsb_hnp_rows(csv_file=csv_file, ell=ell):
        residue_mod_n = ((private_key % N) * row["t_i"] - row["u_i"]) % N
        centered_residue = centered_mod(residue_mod_n, N)

        recovered_k = (pow(row["s"], -1, N) * ((row["h"] + (private_key % N) * row["r"]) % N)) % N
        alpha_matches = (recovered_k % modulus) == row["known_part"] if ell else row["known_part"] == 0
        quotient_numerator = recovered_k - row["alpha"]
        quotient_integral = (quotient_numerator % modulus) == 0 if ell else True
        hidden_quotient = quotient_numerator // modulus if quotient_integral else None
        is_small = abs(centered_residue) <= known_lsb_bound(ell, N)
        exact_match = quotient_integral and centered_residue == hidden_quotient

        rows.append(
            {
                "index": row["index"],
                "r": row["r"],
                "s": row["s"],
                "h": row["h"],
                "known_part": row["known_part"],
                "alpha": row["alpha"],
                "t_i": row["t_i"],
                "u_i": row["u_i"],
                "a_t_minus_u_mod_n": residue_mod_n,
                "centered_residue": centered_residue,
                "recovered_k": recovered_k,
                "alpha_matches": alpha_matches,
                "quotient_integral": quotient_integral,
                "hidden_quotient": hidden_quotient,
                "abs_centered_residue": abs(centered_residue),
                "is_small": is_small,
                "exact_match": exact_match,
            }
        )

    return rows


def write_output_csv(output_csv: str, rows):
    fieldnames = [
        "index",
        "r",
        "s",
        "h",
        "known_part",
        "alpha",
        "t_i",
        "u_i",
        "a_t_minus_u_mod_n",
        "centered_residue",
        "recovered_k",
        "alpha_matches",
        "quotient_integral",
        "hidden_quotient",
        "abs_centered_residue",
        "is_small",
        "exact_match",
    ]
    with open(output_csv, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows, ell: int):
    total = len(rows)
    small_count = sum(row["is_small"] for row in rows)
    exact_count = sum(row["exact_match"] for row in rows)
    alpha_match_count = sum(row["alpha_matches"] for row in rows)
    quotient_integral_count = sum(row["quotient_integral"] for row in rows)
    max_abs_residue = max((row["abs_centered_residue"] for row in rows), default=0)
    smallness_bound = known_lsb_bound(ell, N)
    passed = total > 0 and small_count == total and exact_count == total and alpha_match_count == total

    print(f"\n=== Paper Derived Quantities Check ===")
    print(f"Rows processed            : {total}")
    print(f"ell                       : {ell}")
    print(f"known_part role           : alpha_i = k_i mod 2^ell")
    print(f"Smallness bound           : floor((N - 1) / 2^{ell}) = {smallness_bound}")
    print(f"known_part matches k mod  : {alpha_match_count}/{total}")
    print(f"(k_i - alpha_i)/2^ell int : {quotient_integral_count}/{total}")
    print(f"|a*t_i - u_i| small       : {small_count}/{total}")
    print(f"Centered residue matches  : {exact_count}/{total}")
    print(f"Max |centered residue|    : {max_abs_residue}")
    print(f"Overall verification      : {'PASSED' if passed else 'FAILED'}")


def print_sample_rows(rows, limit: int):
    if limit <= 0 or not rows:
        return

    print("\nSample rows:")
    for row in rows[:limit]:
        print(
            "  "
            f"#{row['index']}: "
            f"alpha={row['alpha']}, "
            f"t_i={row['t_i']}, "
            f"u_i={row['u_i']}, "
            f"centered(a*t_i-u_i)={row['centered_residue']}, "
            f"hidden_quotient={row['hidden_quotient']}"
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compute the paper's t_i, u_i values and verify centered smallness."
    )
    parser.add_argument("--csv", required=True, help="Path to the CSV file")
    parser.add_argument("--key", type=int, default=DEFAULT_PRIVATE_KEY, help="Private key a")
    parser.add_argument("--out", help="Optional output CSV path for the derived quantities")
    parser.add_argument("--sample", type=int, default=5, help="Number of rows to print in the summary")
    parser.add_argument(
        "--ell",
        "--param",
        dest="ell",
        type=int,
        required=True,
        help="Number of leaked least-significant bits ell",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    ell = args.ell

    if not 0 <= ell <= 256:
        raise ValueError("ell must be between 0 and 256 inclusive.")

    rows = compute_quantities(
        csv_file=args.csv,
        private_key=args.key,
        ell=ell,
    )

    if args.out:
        write_output_csv(args.out, rows)

    print_summary(rows, ell=ell)
    print_sample_rows(rows, limit=args.sample)
