# Paper Reproduction Notes

**Reference**

P. Q. Nguyen and I. E. Shparlinski, “The Insecurity of the Elliptic Curve Digital Signature Algorithm with Partially Known Nonces”, *Designs, Codes and Cryptography*, 2003.

## Scope Of This Repository

This repository now implements only the paper-aligned `known_lsb` setting.

That means:

- each synthetic nonce leaks its lowest `param` bits
- the leaked value is stored as `known_part`
- `known_part = k mod 2^param`
- datasets are written as `data/raw/biased_signatures_known_lsb_{param}.csv`

The project does not currently implement other leakage families.

## Dataset Model

Each row of a generated dataset contains:

- `r`
- `s`
- `h`
- `known_part`

Each row is a valid ECDSA signature satisfying:

```text
k * s ≡ h + d * r (mod q)
```

with:

- `d` the synthetic private key
- `k` the per-signature nonce
- `known_part = k mod 2^ell`

The generator rejects edge cases until every row satisfies:

- `1 <= k < q`
- `r != 0`
- `s != 0`

## Paper-Derived Quantities

For the paper’s `known_lsb` reduction, the repository computes:

```text
t_i = 2^(-ell) * r_i * s_i^(-1) mod q
u_i = 2^(-ell) * (alpha_i - s_i^(-1) * h_i) mod q
```

where:

- `alpha_i = known_part`
- `alpha_i = k_i mod 2^ell`

The hidden-number relation is:

```text
a * t_i - u_i ≡ e_i (mod q)
```

with `e_i` small, roughly bounded by:

```text
|e_i| <= q / 2^ell
```

The script `scripts.check_paper_derived_quantities` verifies this relation and reports the centered residues.

## Current Attack Implementation

The attack script `scripts.attack_hnp_lattice` is a first BV-style proof of concept.

It does the following:

1. load a `known_lsb` dataset
2. infer `ell` from the filename when possible
3. compute `t_i` and `u_i`
4. form the paper-style approximation

```text
v_i = u_i + q / 2^(ell + 1)
```

so that:

```text
|a * t_i - v_i|_q <= q / 2^(ell + 1)
```

5. build a Boneh-Venkatesan style CVP lattice
6. scale that lattice by `q` so the basis is integral for Sage’s `LLL`
7. apply `LLL`
8. apply Babai’s nearest-plane algorithm
9. extract a key candidate
10. validate the candidate against the known synthetic key

## Lattice Used In The Prototype

The paper-style lattice basis in dimension `d + 1` is:

```text
[ q,   0, ...,   0,   0 ]
[ 0,   q, ...,   0,   0 ]
...
[ 0,   0, ...,   q,   0 ]
[ t_1, t_2, ..., t_d, 1/q ]
```

with target:

```text
[ v_1, ..., v_d, 0 ]
```

The repository uses the equivalent integer-scaled version:

```text
[ q^2,     0, ...,     0, 0 ]
[   0,   q^2, ...,     0, 0 ]
...
[   0,     0, ...,   q^2, 0 ]
[ q t_1, q t_2, ..., q t_d, 1 ]
```

with scaled target:

```text
[ q v_1, ..., q v_d, 0 ]
```

This scaling does not change the closest-vector problem. It only makes the basis compatible with Sage’s integer lattice routines.

## Meaning Of `--samples`

The attack script uses only the first `N` rows of the CSV, where `N` is the value passed to:

```text
--samples N
```

So:

- `--samples 24` uses the first 24 signatures
- `--samples 100` uses the first 100 signatures
- the lattice dimension becomes `(N + 1) x (N + 1)`

This parameter matters a lot in practice.

## Empirical Results In This Repository

Observed outcomes so far:

- `ell = 8`, generated dataset size `100`, attack with `--samples 100`: success
- `ell = 8`, attack with `--samples 24`: failure
- `ell = 3`, attack with `--samples 24`: failure

These are practical observations for this repository, not theoretical guarantees.

## Recommended Commands

Generate a dataset:

```bash
sage -python -m scripts.generate_partial_known --param 8 --num 100
```

Verify the leaked bits:

```bash
sage -python -m scripts.check_biased_signatures \
  --csv data/raw/biased_signatures_known_lsb_8.csv \
  --param 8
```

Compute `t_i` and `u_i`:

```bash
python -m scripts.check_paper_derived_quantities \
  --csv data/raw/biased_signatures_known_lsb_8.csv \
  --ell 8
```

Run the attack on the known working setting:

```bash
sage -python -m scripts.attack_hnp_lattice \
  --csv data/raw/biased_signatures_known_lsb_8.csv \
  --samples 100 \
  --verbose
```

## Limitations

- It only supports `known_lsb`.
- It uses only the direct BV-style reduction.
- It uses `LLL + Babai`, not a stronger CVP oracle.
- It is designed as a reproduction prototype, not an optimized attack.
- It can return candidates that satisfy the HNP bounds but are not the true key.
- Candidate validation is therefore mandatory.

In short:

- some parameter settings work
- some parameter settings are still too hard
- the current success/failure boundary is empirical, not final
