import csv
import sage.all as sage
from .constants import P, N, G_X, G_Y

E = sage.EllipticCurve(sage.GF(sage.ZZ(P)), [0, 7]) # secp256k1
G = E(G_X, G_Y)

def generate_biased_signatures(
    private_key: int,
    num_sigs: int = 80,
    bias_type: str = "short_128bit",
    output_csv: str = "data/raw/biased_signatures.csv",
):
    """Gen ECDSA sigs """
    d = sage.ZZ(private_key) % N

    signatures = []
    for i in range(num_sigs):
        # === Biased nonce k ===
        if bias_type.startswith("short_"):
            bitlen_str = bias_type.split("_")[1]
            bitlen = int(bitlen_str.replace("bit", ""))
            k = sage.ZZ.random_element(2**bitlen)
        elif bias_type == "shared_prefix_64lsb":
            k = (sage.ZZ.random_element(2**(256 - 64)) << 64) | sage.ZZ.random_element(2**64)
        elif bias_type == "shared_suffix_128msb":
            k = sage.ZZ.random_element(2**128) | (sage.ZZ.random_element(2**(256-128)) << 128)
        elif bias_type == "shared_suffix_224msb":
            k = sage.ZZ.random_element(2**224) | (sage.ZZ.random_element(2**(256-224)) << 224)
        else:
            raise ValueError(f"Unknown bias_type: {bias_type}")

        # ECDSA signature
        R_point = (k * G).xy()[0]
        R = sage.ZZ(R_point) % N
        r = int(R)
        h = sage.ZZ(i) % N
        s = (sage.inverse_mod(k, N) * (h + d * r)) % N

        signatures.append((r, int(s), int(h)))

    # save csv
    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["r", "s", "h"])
        writer.writerows(signatures)

    print(f"Generated {num_sigs} biased signatures ({bias_type}) → {output_csv}")
    return signatures

