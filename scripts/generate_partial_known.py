import argparse
from src.lattice_attack.ecdsa_generator import generate_biased_signatures

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ECDSA signatures with common biases (Nguyen-Shparlinski 2003 + practical biases)")
    parser.add_argument("--bias", choices=["known_msb", "short", "shared_suffix"], default="known_msb", help="Bias type")
    parser.add_argument("--param", type=int, default=128, help="known_msb_bits / short bitlen / suffix_bits")
    parser.add_argument("--num", type=int, default=80, help="Number of signatures")
    parser.add_argument("--key", type=int, default=0x123456789ABCDEF0123456789ABCDEF0, help="Private key (toy)")
    args = parser.parse_args()

    generate_biased_signatures(
        private_key=args.key,
        num_sigs=args.num,
        bias_type=args.bias,
        param=args.param,
    )

