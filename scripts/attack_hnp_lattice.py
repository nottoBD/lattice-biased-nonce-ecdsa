#!/usr/bin/env sage -python
"""
Minimal proof-of-concept BV-style lattice attack for synthetic `known_lsb` datasets.

This follows the paper's hidden-number reduction more closely than the previous
embedding-style prototype.

For known LSB leakage we have

    a * t_i - u_i ≡ e_i (mod q)
    0 <= e_i < q / 2^ell

so the paper defines an approximation

    v_i = u_i + q / 2^(ell + 1)

with

    |a * t_i - v_i|_q <= q / 2^(ell + 1).

The Boneh-Venkatesan lattice/CVP reduction uses the (d + 1)-dimensional basis

    [ q,   0, ...,   0,   0 ]
    [ 0,   q, ...,   0,   0 ]
    ...
    [ 0,   0, ...,   q,   0 ]
    [ t_1, t_2, ..., t_d, 1/q ]

with target vector

    c = [v_1, ..., v_d, 0].

To keep the basis integral for Sage's LLL routine, this script uses the exactly
equivalent basis obtained by multiplying every coordinate by q:

    [ q^2,     0, ...,     0, 0 ]
    [   0,   q^2, ...,     0, 0 ]
    ...
    [   0,     0, ...,   q^2, 0 ]
    [ q t_1, q t_2, ..., q t_d, 1 ]

and the scaled target

    c' = [q v_1, ..., q v_d, 0].

We then apply LLL followed by Babai's nearest-plane algorithm, which is the same
paper lineage used in the Nguyen-Shparlinski HNP reduction.
"""

import argparse
from typing import Dict, List

import sage.all as sage

from src.lattice_attack.constants import N
from src.lattice_attack.hnp import (
    DEFAULT_PRIVATE_KEY,
    compute_known_lsb_hnp_rows,
    diagnose_candidate,
    infer_known_lsb_ell,
    known_lsb_bound,
    looks_like_known_lsb_dataset,
)


def load_attack_rows(csv_file: str, ell: int, num_samples: int) -> List[Dict[str, int]]:
    rows = compute_known_lsb_hnp_rows(csv_file=csv_file, ell=ell, num_samples=num_samples)
    if len(rows) < num_samples:
        raise ValueError(
            f"Requested {num_samples} samples but the dataset only contains {len(rows)} rows."
        )
    if not all(row["alpha_in_range"] for row in rows):
        raise ValueError(
            "Some known_part values fall outside [0, 2^ell). "
            "This usually means the dataset is not known_lsb or ell is wrong."
        )
    return rows


def nearest_integer(value) -> sage.Integer:
    half = sage.QQ(1) / 2
    if value >= 0:
        return sage.ZZ(sage.floor(value + half))
    return -sage.ZZ(sage.floor(-value + half))


def babai_nearest_plane(reduced_basis, target):
    rows = [sage.vector(sage.QQ, row) for row in reduced_basis.rows()]
    orthogonal_rows = []
    orthogonal_norms = []

    for row in rows:
        ortho = sage.vector(sage.QQ, row)
        for prev_ortho, prev_norm in zip(orthogonal_rows, orthogonal_norms):
            if prev_norm == 0:
                continue
            mu = row.dot_product(prev_ortho) / prev_norm
            ortho -= mu * prev_ortho
        orthogonal_rows.append(ortho)
        orthogonal_norms.append(ortho.dot_product(ortho))

    residual = sage.vector(sage.QQ, target)
    coefficients = [sage.ZZ(0)] * len(rows)

    for index in range(len(rows) - 1, -1, -1):
        if orthogonal_norms[index] == 0:
            continue
        coefficient = nearest_integer(residual.dot_product(orthogonal_rows[index]) / orthogonal_norms[index])
        coefficients[index] = coefficient
        residual -= coefficient * rows[index]

    closest_vector = target - residual
    return coefficients, closest_vector, residual


def paper_approximation(row: Dict[str, int], ell: int):
    return sage.QQ(row["u_i"]) + (sage.QQ(N) / (1 << (ell + 1)))


def build_bv_basis(rows: List[Dict[str, int]]):
    dimension = len(rows) + 1
    basis_rows = []

    for index in range(len(rows)):
        row = [0] * dimension
        row[index] = N * N
        basis_rows.append(row)

    basis_rows.append([N * row["t_i"] for row in rows] + [1])
    return sage.matrix(sage.ZZ, basis_rows)


def build_bv_target(rows: List[Dict[str, int]], ell: int):
    target_entries = [sage.QQ(N) * paper_approximation(row, ell) for row in rows]
    target_entries.append(sage.QQ(0))
    return sage.vector(sage.QQ, target_entries)


def extract_candidates(
    closest_vector,
    rows: List[Dict[str, int]],
    ell: int,
    validation_key: int,
) -> List[Dict[str, int]]:
    last_coordinate = sage.QQ(closest_vector[-1])
    if last_coordinate.denominator() != 1:
        raise ValueError("Babai returned a non-integral last coordinate; expected an integral key candidate.")

    candidate = sage.ZZ(last_coordinate) % N
    diagnostics = diagnose_candidate(candidate=candidate, rows=rows, ell=ell, modulus=N)
    diagnostics.update(
        {
            "candidate_hex": hex(candidate),
            "last_coordinate": int(last_coordinate),
            "matches_validation_key": candidate == (validation_key % N),
        }
    )
    return [diagnostics]


def print_header(csv_file: str, rows: List[Dict[str, int]], ell: int):
    print("\n=== HNP Lattice Attack (known_lsb, BV-style) ===")
    print(f"Dataset                   : {csv_file}")
    print(f"Samples used              : {len(rows)}")
    print(f"Leakage bits ell          : {ell}")
    print(f"Approximation radius      : q / 2^(ell + 1) = {sage.QQ(N) / (1 << (ell + 1))}")
    print(f"Smallness bound           : floor((q - 1) / 2^ell) = {known_lsb_bound(ell, N)}")
    print(f"Lattice dimension         : {len(rows) + 1} x {len(rows) + 1}")
    print("Reduction / CVP step      : LLL + Babai nearest plane")


def print_candidates(candidates: List[Dict[str, int]]):
    print("\nRecovered candidates:")
    if not candidates:
        print("  none")
        return

    for candidate in candidates:
        print(
            "  "
            f"a={candidate['candidate_hex']}, "
            f"last_coord={candidate['last_coordinate']}, "
            f"max|a*t-u|={candidate['max_abs_residue']}, "
            f"within_bound={'YES' if candidate['within_bound'] else 'NO'}, "
            f"known_key={'YES' if candidate['matches_validation_key'] else 'NO'}"
        )


def print_verbose_notes(rows: List[Dict[str, int]], ell: int, basis, target, residual):
    print("\nPaper-style approximation samples:")
    for row in rows[:3]:
        print(
            "  "
            f"#{row['index']}: "
            f"alpha={row['alpha']}, "
            f"t_i={row['t_i']}, "
            f"u_i={row['u_i']}, "
            f"v_i={paper_approximation(row, ell)}"
        )

    print("\nBV basis (scaled by q to stay integral):")
    print("  Rows 1..d: q^2 on the diagonal")
    print("  Row d+1 : [q*t_1, ..., q*t_d, 1]")
    print("  Target  : [q*v_1, ..., q*v_d, 0]")
    print(f"  Basis shape             : {basis.nrows()} x {basis.ncols()}")
    print(f"  First target entry      : {target[0] if rows else 0}")

    if rows:
        first_coordinate_residuals = [abs(residual[index]) for index in range(len(rows))]
        print(f"  Max |scaled residual|   : {max(first_coordinate_residuals)}")
        print(f"  Expected scaled radius  : {(sage.QQ(N * N) / (1 << (ell + 1)))}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a BV-style hidden-number lattice attack against a synthetic known_lsb dataset."
    )
    parser.add_argument("--csv", required=True, help="Path to the known_lsb dataset CSV file")
    parser.add_argument("--samples", type=int, required=True, help="Number of samples to use from the dataset")
    parser.add_argument("--ell", type=int, help="Override the leakage bits if ell cannot be inferred from the filename")
    parser.add_argument("--key", type=int, default=DEFAULT_PRIVATE_KEY, help="Synthetic private key for validation")
    parser.add_argument("--verbose", action="store_true", help="Print basis and Babai diagnostics")
    parser.add_argument("--M", type=int, help=argparse.SUPPRESS)
    return parser.parse_args()


def main():
    args = parse_args()

    if args.samples <= 0:
        raise ValueError("--samples must be positive.")
    if args.M is not None:
        raise ValueError("--M is not used in the paper-style BV reduction.")

    if args.ell is not None:
        ell = args.ell
    else:
        ell = infer_known_lsb_ell(args.csv)
        if ell is None:
            raise ValueError(
                "Could not infer ell from the dataset filename. "
                "Use a generator-style name like biased_signatures_known_lsb_8.csv or pass --ell."
            )

    if not looks_like_known_lsb_dataset(args.csv) and args.ell is None:
        raise ValueError(
            "Only known_lsb datasets are supported. "
            "If the file was renamed, pass --ell explicitly to confirm the assumption."
        )
    if not 0 <= ell <= 256:
        raise ValueError("ell must be between 0 and 256 inclusive.")

    rows = load_attack_rows(csv_file=args.csv, ell=ell, num_samples=args.samples)
    basis = build_bv_basis(rows)
    target = build_bv_target(rows, ell)

    print_header(csv_file=args.csv, rows=rows, ell=ell)

    reduced_basis = basis.LLL()
    _, closest_vector, residual = babai_nearest_plane(reduced_basis=reduced_basis, target=target)
    candidates = extract_candidates(
        closest_vector=closest_vector,
        rows=rows,
        ell=ell,
        validation_key=args.key,
    )

    if args.verbose:
        print_verbose_notes(rows=rows, ell=ell, basis=basis, target=target, residual=residual)

    print_candidates(candidates)

    success = any(candidate["matches_validation_key"] for candidate in candidates)
    best = candidates[0] if candidates else None
    print("\nDiagnostics:")
    print(f"  Candidate count         : {len(candidates)}")
    if best is not None:
        print(f"  Best max|a*t-u|         : {best['max_abs_residue']}")
        print(f"  Babai last coordinate   : {best['last_coordinate']}")
    print(f"  Validation key          : {hex(args.key % N)}")
    print(f"  Recovery succeeded      : {'YES' if success else 'NO'}")


if __name__ == "__main__":
    main()
