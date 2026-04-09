import csv
import sage.all as sage
from .constants import P, N, G_X, G_Y

E = sage.EllipticCurve(sage.GF(sage.ZZ(P)), [0, 7])
G = E(G_X, G_Y)


def _validate_param(param: int):
    if not 0 <= param <= 256:
        raise ValueError("param must be between 0 and 256 inclusive.")


def _recover_signature_components(private_key: sage.Integer, h: sage.Integer, k: sage.Integer):
    if not (1 <= k < N):
        return None

    r = sage.ZZ((k * G).xy()[0]) % N
    if r == 0:
        return None

    s = (sage.inverse_mod(k, N) * (h + private_key * r)) % N
    if s == 0:
        return None

    return int(r), int(s), int(h)


def _sample_hash_value():
    return sage.ZZ.random_element(N)


def _make_nonce_sampler(param: int):
    modulus = 1 << param
    return lambda: (
        (k := sage.ZZ.random_element(1, N)),
        (k % modulus) if param else sage.ZZ(0),
    )


def generate_biased_signatures(
    private_key: int,
    num_sigs: int = 80,
    param: int = 3,
    output_csv: str = None,
):
    """Generate ECDSA signatures with paper-aligned known_lsb leakage."""
    d = sage.ZZ(private_key) % N
    signatures = []
    _validate_param(param)
    sample_nonce = _make_nonce_sampler(param)

    if output_csv is None:
        output_csv = f"data/raw/biased_signatures_known_lsb_{param}.csv"

    for _ in range(num_sigs):
        h = _sample_hash_value()
        while True:
            k, known_part = sample_nonce()
            signed = _recover_signature_components(d, h, k)
            if signed is None:
                continue
            r, s, h_int = signed
            signatures.append((r, s, h_int, int(known_part)))
            break

    with open(output_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["r", "s", "h", "known_part"])
        writer.writerows(signatures)

    print(f"Generated {num_sigs} signatures with bias 'known_lsb' (param={param}) → {output_csv}")
    return signatures
