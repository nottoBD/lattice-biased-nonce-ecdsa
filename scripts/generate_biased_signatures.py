import argparse
from src.lattice_attack.ecdsa_generator import generate_biased_signatures

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate biased ECDSA signatures (Breitner & Heninger 2019)")
    parser.add_argument("--bias", choices=["short_64bit", "short_110bit", "short_128bit", "short_160bit",
                                           "shared_prefix_64lsb", "shared_suffix_128msb", "shared_suffix_224msb"],
                        default="short_128bit", help="Bias type from the paper")
    parser.add_argument("--num", type=int, default=80, help="Number of signatures")
    parser.add_argument("--key", type=int, default=0x123456789ABCDEF0123456789ABCDEF0, help="Private key (toy)")
    args = parser.parse_args()

    generate_biased_signatures(
        private_key=args.key,
        num_sigs=args.num,
        bias_type=args.bias,
    )
