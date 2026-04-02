import csv
import sage.all as sage
from .constants import P, N, G_X, G_Y

E = sage.EllipticCurve(sage.GF(sage.ZZ(P)), [0, 7])
G = E(G_X, G_Y)
SUPPORTED_BIAS_TYPES = ("known_lsb", "known_msb", "short", "shared_suffix")


def _validate_param(bias_type: str, param: int):
    if not 0 <= param <= 256:
        raise ValueError("param must be between 0 and 256 inclusive.")
    if bias_type == "short" and param == 0:
        raise ValueError("short bias requires param >= 1.")


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


def _sample_short_nonce(bitlen: int):
    limit = 1 << bitlen
    while True:
        k = sage.ZZ.random_element(limit)
        if 1 <= k < N:
            return k, k


def _sample_shared_suffix_nonce(suffix_bits: int, fixed_suffix: sage.Integer):
    if suffix_bits == 256:
        return fixed_suffix, fixed_suffix

    while True:
        high = sage.ZZ.random_element(1 << (256 - suffix_bits))
        k = (high << suffix_bits) | fixed_suffix
        if 1 <= k < N:
            return k, fixed_suffix


def _sample_hash_value():
    return sage.ZZ.random_element(N)


def _make_nonce_sampler(bias_type: str, param: int):
    if bias_type == "known_lsb":
        modulus = 1 << param
        return lambda: (
            (k := sage.ZZ.random_element(1, N)),
            (k % modulus) if param else sage.ZZ(0),
        )

    if bias_type == "known_msb":
        unknown_bits = 256 - param
        return lambda: (
            (k := sage.ZZ.random_element(1, N)),
            k >> unknown_bits,
        )

    if bias_type == "short":
        return lambda: _sample_short_nonce(param)

    if bias_type == "shared_suffix":
        if param == 256:
            fixed_suffix = sage.ZZ.random_element(1, N)
        else:
            fixed_suffix = sage.ZZ.random_element(1 << param)
        return lambda: _sample_shared_suffix_nonce(param, fixed_suffix)

    raise ValueError(
        f"Unknown bias_type: {bias_type}. Use {', '.join(repr(name) for name in SUPPORTED_BIAS_TYPES)}."
    )


def generate_biased_signatures(
    private_key: int,
    num_sigs: int = 80,
    bias_type: str = "known_lsb",
    param: int = 3,
    output_csv: str = None,
):
    """Generate ECDSA signatures with paper-aligned nonce leakage modes."""
    d = sage.ZZ(private_key) % N
    signatures = []
    _validate_param(bias_type, param)
    sample_nonce = _make_nonce_sampler(bias_type, param)

    if output_csv is None:
        output_csv = f"data/raw/biased_signatures_{bias_type}_{param}.csv"

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

    print(f"Generated {num_sigs} signatures with bias '{bias_type}' (param={param}) → {output_csv}")
    return signatures
