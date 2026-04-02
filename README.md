# Lattice-Biased-Nonce-ECDSA

**Phase 2 – Artificial Biased Signature Generation**  
Reproduction of partial nonce leakage for the main research paper:  
**P. Q. Nguyen and I. E. Shparlinski, “The Insecurity of the Elliptic Curve Digital Signature Algorithm with Partially Known Nonces”, Designs, Codes and Cryptography, 2003.**

The generator creates valid ECDSA signatures on secp256k1 while artificially introducing one of four nonce leakage modes. The default experiment mode is `known_lsb`, which stores the leaked least-significant bits of each nonce in the CSV `known_part` column.

## Supported Bias Types
The generator currently supports the following biases:

| Bias Type       | Description                                      | `--param` meaning                  | Example command                              |
|-----------------|--------------------------------------------------|------------------------------------|----------------------------------------------|
| `known_lsb`     | Lowest bits of each nonce are known (default)    | Number of leaked LSB bits          | `--bias known_lsb --param 3 --num 100`       |
| `known_msb`     | Top bits of each nonce are known                 | Number of known MSB bits           | `--bias known_msb --param 3 --num 100`       |
| `short`         | Nonce is chosen from a small range               | Maximum bit length of nonce        | `--bias short --param 128`                   |
| `shared_suffix` | Lowest bits are identical across all nonces      | Number of shared LSB bits          | `--bias shared_suffix --param 128`           |

Each run produces a **dedicated CSV file** named `data/raw/biased_signatures_{bias_type}_{param}.csv`
For paper-style experiments, start with small leakage values such as `2`, `3`, `4`, or `8` bits. Values like `160` represent extremely strong leakage rather than the small partial exposure discussed in the paper.
Each generated row also uses an independently sampled hash representative `h` instead of the old `h = i mod N` debugging pattern.

## Quickstart Ubuntu 24.04

### Install with conda

Install Git and get the repo

```bash
sudo apt install git -y
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
```
Install Miniconda

```bash
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
~/miniconda3/bin/conda init bash
```
Close and re-open terminal.
Before your command line, there is a (base) :

```bash
(base) yostix@yostix:~/Bureau$
```

Install SageMath with Conda :

```bash
conda install -c conda-forge sage -y
```
If you have python 3.13, you will get an error : 
```bash
 Pins seem to be involved in the conflict. Currently pinned specs:

 - python=3.13 
```
To resolve that, create an environment with conda which will use python3.11
```bash
conda create -n sage_env python=3.11 -y
```
And switch to this environment

```bash
conda activate sage_env
```
The (base) will become (senge_env) like this

```bash
(sage_env) yostix@yostix:~/Bureau/lattice-biased-nonce-ecdsa$
```

Now retry to install SageMath with conda

```bash
conda install -c conda-forge sage -y
```

Generate biased signatures
```bash
python -m scripts.generate_partial_known --bias known_lsb --param 3 --num 100
python -m scripts.generate_partial_known --bias known_msb --param 3 --num 100
python -m scripts.generate_partial_known --bias short --param 128 --num 80
python -m scripts.generate_partial_known --bias shared_suffix --param 128 --num 80
```

Check output
```bash
# 1. Check the default paper-aligned known_lsb file
sage -python -m scripts.check_biased_signatures \
  --csv data/raw/biased_signatures_known_lsb_3.csv \
  --bias known_lsb --param 3

# 2. Check the known_msb with 3 leaked bits file
sage -python -m scripts.check_biased_signatures \
  --csv data/raw/biased_signatures_known_msb_3.csv \
  --bias known_msb --param 3

# 3. Check the short bias file
sage -python -m scripts.check_biased_signatures \
  --csv data/raw/biased_signatures_short_128.csv \
  --bias short --param 128

# 4. Check the shared suffix bias file
sage -python -m scripts.check_biased_signatures \
  --csv data/raw/biased_signatures_shared_suffix_128.csv \
  --bias shared_suffix --param 128
```

Compute the paper's derived quantities for a `known_lsb` dataset
```bash
python3 -m scripts.check_paper_derived_quantities \
  --csv data/raw/biased_signatures_known_lsb_3.csv \
  --ell 3
```
