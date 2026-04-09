# Lattice-Biased-Nonce-ECDSA

**Partial nonce leakage and HNP attack prototype**

This repository is a small research reproduction project around:

P. Q. Nguyen and I. E. Shparlinski, “The Insecurity of the Elliptic Curve Digital Signature Algorithm with Partially Known Nonces”, *Designs, Codes and Cryptography*, 2003.

The project currently focuses on:

- synthetic ECDSA signatures on `secp256k1`
- `known_lsb` leakage only
- computation of the paper-style hidden-number quantities `t_i` and `u_i`
- a first Boneh-Venkatesan style lattice attack prototype using `LLL + Babai`

## What The Project Does

The current workflow is:

1. generate a synthetic dataset where the lowest `param` bits of each nonce are known
2. verify that the CSV really contains the expected leaked bits
3. compute the paper-derived HNP quantities
4. run a BV-style lattice attack against the synthetic dataset
5. validate the recovered candidate against the known synthetic private key

The leaked value is stored in the CSV column `known_part`, where:

```text
known_part = k mod 2^param
```

Generated files are written to:

```text
data/raw/biased_signatures_known_lsb_{param}.csv
```

Each CSV row contains:

- `r`
- `s`
- `h`
- `known_part`

## Observed outcomes in this repository:

- `ell = 8`, dataset size `100`, attack with `--samples 100`: succeeded
- `ell = 8`, attack with `--samples 24`: may fail
- `ell = 3`: too hard for this minimal implementation in current tests

So the project should be understood as:

- a working end-to-end reproduction prototype
- with parameter regimes that succeed
- and harder regimes that still fail

## Repository Guide

Main scripts:

- `scripts.generate_partial_known`
  generates a synthetic `known_lsb` dataset
- `scripts.check_biased_signatures`
  checks that `known_part` really matches the nonce LSBs
- `scripts.check_paper_derived_quantities`
  computes `t_i`, `u_i`, and verifies the bounded modular-error relation
- `scripts.attack_hnp_lattice`
  runs the BV-style lattice attack and validates the recovered key candidate

Main library files:

- `src/lattice_attack/ecdsa_generator.py`
  dataset generation
- `src/lattice_attack/hnp.py`
  shared HNP helpers, row loading, and candidate diagnostics

## Quickstart Ubuntu 24.04

### Install with conda

Install Git and Miniconda:

```bash
sudo apt install git -y
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
```

Install Miniconda:

```bash
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
~/miniconda3/bin/conda init bash
```

Close and re-open the terminal, then create a dedicated environment before installing anything:

```bash
conda create -n sage_env python=3.11 -y
conda activate sage_env
```

Your prompt should now show the environment name, for example:

```bash
(sage_env) user@host:~/Desktop/cryptanalysis/lattice-biased-nonce-ecdsa$
```

Install SageMath inside that environment:

```bash
conda install -c conda-forge sage -y
```

This avoids installing packages into `base` and avoids common Python pin conflicts.

### Work from the repository root

All commands below assume you are in:

```bash
cd ~/Desktop/cryptanalysis/lattice-biased-nonce-ecdsa
```

## End-To-End Example

This is the clearest working example currently known for this repository.

Generate a dataset with 8 leaked LSBs and 100 signatures:

```bash
sage -python -m scripts.generate_partial_known --param 8 --num 100
```

Verify that the leaked bits are correct:

```bash
sage -python -m scripts.check_biased_signatures \
  --csv data/raw/biased_signatures_known_lsb_8.csv \
  --param 8
```

Compute the paper-derived quantities:

```bash
python -m scripts.check_paper_derived_quantities \
  --csv data/raw/biased_signatures_known_lsb_8.csv \
  --ell 8
```

Run the lattice attack:

```bash
sage -python -m scripts.attack_hnp_lattice \
  --csv data/raw/biased_signatures_known_lsb_8.csv \
  --samples 100 \
  --verbose
```

On this setting, the current prototype has been observed to recover the synthetic key successfully.

## What `--samples` Means

The attack script does not always use the whole CSV.

```text
--samples N
```

means:

- use the first `N` rows from the dataset
- compute `t_i` and `u_i` only for those rows
- build a lattice of dimension `(N + 1) x (N + 1)`

Larger `--samples` gives the attack more information, but also increases lattice dimension and runtime.

## Attack Summary

The current attack script:

- loads a `known_lsb` dataset
- infers `ell` from the filename when possible
- computes the paper’s `t_i` and `u_i`
- forms the approximation

```text
v_i = u_i + q / 2^(ell + 1)
```

- builds a Boneh-Venkatesan style CVP lattice
- uses an equivalent integer-scaled basis so Sage can run `LLL`
- applies Babai’s nearest-plane algorithm
- extracts a secret-key candidate
- validates that candidate against the known synthetic key

## Limitations

- It only supports `known_lsb`.
- It uses a direct BV-style reduction with `LLL + Babai`.
- It does not use stronger CVP machinery, stronger lattice reduction, or extra heuristics.
- Harder settings may produce plausible but incorrect candidates.
- External validation of the candidate key is always required.

In particular:

- `ell = 3` is still too hard in current tests
- even `ell = 8` can fail when too few samples are used
- success depends on both leakage size and number of samples

## Default Synthetic Key

By default, the scripts use the synthetic private key:

```text
0x123456789ABCDEF0123456789ABCDEF0
```

That key is intentionally known so the generated datasets and recovered candidates can be validated during experiments.
