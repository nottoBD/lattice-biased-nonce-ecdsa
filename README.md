# Lattice-Biased-Nonce-ECDSA

Reproduction of **biased nonce generation** from the paper  
**Biased Nonce Sense: Lattice Attacks against Weak ECDSA Signatures in Cryptocurrencies**  
Joachim Breitner & Nadia Heninger (Financial Cryptography 2019).

**Phase 2 of our group project** => Env + artificial biased signature generation

## Tested on
- **Arch-based Linux**
- SageMath 3.14.3  

**Note:** On other Linux distributions the SageMath commands may differ (e.g. `sage --python` or `sage --pip`).  
The commands below work reliably on Arch-based Linux.

## Quick Start

### 1. Install SageMath
```bash
sudo pacman -S sagemath
```

### 2. Generate biased signatures
```bash
sage -c '
import sys
sys.path.insert(0, ".")
from src.lattice_attack.ecdsa_generator import generate_biased_signatures
generate_biased_signatures(
    private_key=0x123456789ABCDEF0123456789ABCDEF0,
    num_sigs=80,
    bias_type="short_128bit"
)
'
```

### 3. Verify nonce bias
```bash
sage -c '
import sys
sys.path.insert(0, ".")
import argparse
from scripts.check_nonce_bias import check_nonce_bias
parser = argparse.ArgumentParser()
parser.add_argument("--csv", default="data/raw/biased_signatures.csv")
parser.add_argument("--key", type=int, default=0x123456789ABCDEF0123456789ABCDEF0)
parser.add_argument("--bias", default="short_128bit")
args = parser.parse_args(["--bias", "short_128bit"])
check_nonce_bias(args.csv, args.key, args.bias)
'
```

--- 
## Quickstart Ubuntu 20.04

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

You can now start the project like this : 
Parameters : 
- --num Numbers of signature generated
- --bias Type of signature generated
    - short_{length}bit (e.g., short_128bit, short_64bit)
    - shared_prefix_64lsb
    - shared_suffix_128msb
    - shared_suffix_224msb
    - Unknow bias throw error

```bash
python -m scripts.generate_biased_signatures --bias short_128bit --num 80
```

Output : 
```bash
Generated 80 biased signatures (short_128bit) → data/raw/biased_signatures.csv
```

Check the output
```bash
python -m scripts.check_nonce_bias --bias short_128bit
```
Output :
```bash
Nonce bias check for short_128bit (80 signatures)
   Expected bias type : short_128bit
   Min nonce bits     : 124
   Max nonce bits     : 128
   Average nonce bits : 127.2
   All nonces ≤ 128 bits? : YES
   All nonces have exactly the same MSB? : NO

```

---

Supported bias types

- short_64bit, short_110bit, short_128bit, short_160bit
- shared_prefix_64lsb
- shared_suffix_128msb
- shared_suffix_224msb

(Change the bias_type= line in Gen command)

