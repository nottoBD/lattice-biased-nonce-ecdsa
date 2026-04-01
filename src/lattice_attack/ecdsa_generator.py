import csv
import sage.all as sage
from .constants import P, N, G_X, G_Y

E = sage.EllipticCurve(sage.GF(sage.ZZ(P)), [0, 7])
G = E(G_X, G_Y)

def generate_biased_signatures(
    private_key: int,
    num_sigs: int = 80,
    bias_type: str = "known_msb",
    param: int = 128,
    output_csv: str = None,
):
    """Generate ECDSA signatures with one of the three most common biases
    (Nguyen-Shparlinski 2003 partial nonce leakage)."""
    d = sage.ZZ(private_key) % N
    signatures = []

    if output_csv is None:
        output_csv = f"data/raw/biased_signatures_{bias_type}_{param}.csv"

    if bias_type == "known_msb":
        b = 256 - param
        for i in range(num_sigs):
            k = sage.ZZ.random_element(1, N)
            k_known = k >> b
            R_point = (k * G).xy()[0]
            r = sage.ZZ(R_point) % N
            h = sage.ZZ(i) % N
            s = (sage.inverse_mod(k, N) * (h + d * r)) % N
            signatures.append((int(r), int(s), int(h), int(k_known)))

    elif bias_type == "short":
        bitlen = param
        for i in range(num_sigs):
            k = sage.ZZ.random_element(2**bitlen)
            R_point = (k * G).xy()[0]
            r = sage.ZZ(R_point) % N
            h = sage.ZZ(i) % N
            s = (sage.inverse_mod(k, N) * (h + d * r)) % N
            signatures.append((int(r), int(s), int(h), int(k)))

    elif bias_type == "shared_suffix":
        suffix_bits = param
        fixed_suffix = sage.ZZ.random_element(2**suffix_bits)
        for i in range(num_sigs):
            high = sage.ZZ.random_element(2**(256 - suffix_bits))
            k = (high << suffix_bits) | fixed_suffix
            R_point = (k * G).xy()[0]
            r = sage.ZZ(R_point) % N
            h = sage.ZZ(i) % N
            s = (sage.inverse_mod(k, N) * (h + d * r)) % N
            signatures.append((int(r), int(s), int(h), int(fixed_suffix)))

    else:
        raise ValueError(f"Unknown bias_type: {bias_type}. Use 'known_msb', 'short', or 'shared_suffix'.")

    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["r", "s", "h", "known_part"])
        writer.writerows(signatures)

    print(f"Generated {num_sigs} signatures with bias '{bias_type}' (param={param}) → {output_csv}")
    return signatures
