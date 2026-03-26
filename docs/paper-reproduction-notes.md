# Paper Reproduction Notes – Biased Signature Generation

**Reference:** Breitner & Heninger, FC 2019

## Biases implemented (as found in the wild, cfr paper pg. 1 & 4)
- short nonces: 64, 110, 128, 160 bits (Section 4.1)
- shared prefixes (varying only in the 64 LSB)
- shared suffixes (varying only in the 128 or 224 MSB)

These are the classes the authors discovered in Bitcoin/Ethereum blockchains

The generator produces (r, s, h) tuples saved as CSV
