#!/usr/bin/env sage -python
"""
nonce bias verification for the Breitner & Heninger 2019 reproduction.

Reads data/raw/biased_signatures.csv and prints the actual bit length of every nonce k
(using the known private key) to double-check the requested bias
"""

import csv
import argparse
import sage.all as sage
from src.lattice_attack.constants import P, N, G_X, G_Y

E = sage.EllipticCurve(sage.GF(sage.ZZ(P)), [0, 7])
G = E(G_X, G_Y)

def bit_length(x: int) -> int:
    return x.bit_length() if x > 0 else 0

def check_nonce_bias(csv_file: str, private_key: int, bias_type: str):
    d = sage.ZZ(private_key) % N
    bit_lengths = []

    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = sage.ZZ(row["r"])
            s = sage.ZZ(row["s"])
            h = sage.ZZ(row["h"])

            # Recover k = (s⁻¹ · (h + d·r)) mod N (ECDSA inversion)
            k = (sage.inverse_mod(s, N) * (h + d * r)) % N
            bl = bit_length(int(k))
            bit_lengths.append(bl)

    # stats
    print(f"\nNonce bias check for {bias_type} ({len(bit_lengths)} signatures)")
    print(f"   Expected bias type : {bias_type}")
    print(f"   Min nonce bits     : {min(bit_lengths)}")
    print(f"   Max nonce bits     : {max(bit_lengths)}")
    print(f"   Average nonce bits : {sum(bit_lengths)/len(bit_lengths):.1f}")
    print(f"   All nonces ≤ 128 bits? : {'YES' if max(bit_lengths) <= 128 else 'NO'}")
    print(f"   All nonces have exactly the same MSB? : {'YES' if len(set(bit_lengths)) == 1 else 'NO'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check actual nonce bit lengths (Breitner & Heninger 2019)")
    parser.add_argument("--csv", default="data/raw/biased_signatures.csv", help="CSV file to check")
    parser.add_argument("--key", type=int, default=0x123456789ABCDEF0123456789ABCDEF0, help="Private key used for generation")
    parser.add_argument("--bias", default="short_128bit", help="Bias type (for reference only)")
    args = parser.parse_args()

    check_nonce_bias(args.csv, args.key, args.bias)

