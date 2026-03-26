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

Supported bias types

- short_64bit, short_110bit, short_128bit, short_160bit
- shared_prefix_64lsb
- shared_suffix_128msb
- shared_suffix_224msb

(Change the bias_type= line in Gen command)

