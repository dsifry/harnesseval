"""A small, dependency-free QR code encoder (byte mode, error-correction level M, versions 1-10).

Used at build time by tools/sdlc_report_html.py to put a scannable link on each share image, so the
page stays self-contained and offline. tests/test_sdlc_report.py checks the output against the
`segno` reference encoder and round-trips it through OpenCV's decoder when those are installed.

    >>> m = encode("https://example.com/")
    >>> len(m), m[0][:7]
    (21, [1, 1, 1, 1, 1, 1, 1])

`encode` returns the module matrix (1 = dark) without a quiet zone.
"""
from __future__ import annotations

# ---- version tables, error-correction level M -------------------------------------------------
# (total data codewords, ec codewords per block, [block data sizes]) for versions 1..10
_BLOCKS = {
    1: (16, 10, [16]),
    2: (28, 16, [28]),
    3: (44, 26, [44]),
    4: (64, 18, [32, 32]),
    5: (86, 24, [43, 43]),
    6: (108, 16, [27, 27, 27, 27]),
    7: (124, 18, [31, 31, 31, 31]),
    8: (154, 22, [38, 38, 39, 39]),
    9: (182, 22, [36, 36, 36, 37, 37]),
    10: (216, 26, [43, 43, 43, 43, 44]),
}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
          7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}
_REMAINDER_BITS = {1: 0, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7, 7: 0, 8: 0, 9: 0, 10: 0}

# ---- GF(256) arithmetic for Reed-Solomon ------------------------------------------------------
_EXP = [0] * 512
_LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x
    _LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    _EXP[_i] = _EXP[_i - 255]


def _gf_mul(a: int, b: int) -> int:
    return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]


def _rs_generator(n: int) -> list[int]:
    g = [1]
    for i in range(n):
        g = [0] + g
        for j in range(len(g) - 1):
            g[j] ^= _gf_mul(g[j + 1], _EXP[i])
    return g  # lowest degree first: g[k] is the coefficient of x^k, g[n] == 1


def _rs_ec(data: list[int], n: int) -> list[int]:
    gen = _rs_generator(n)
    rem = [0] * n  # remainder, highest degree first
    for d in data:
        factor = d ^ rem[0]
        rem = rem[1:] + [0]
        if factor:
            for k in range(n):
                rem[k] ^= _gf_mul(gen[n - 1 - k], factor)
    return rem


# ---- bit packing ------------------------------------------------------------------------------
def _codewords(payload: bytes, version: int) -> list[int]:
    data_cw, ec_n, blocks = _BLOCKS[version]
    bits: list[int] = []

    def put(value: int, n: int) -> None:
        bits.extend((value >> (n - 1 - i)) & 1 for i in range(n))

    put(0b0100, 4)                                     # byte mode
    put(len(payload), 16 if version >= 10 else 8)      # character count
    for b in payload:
        put(b, 8)
    capacity = data_cw * 8
    if len(bits) > capacity:
        raise ValueError("payload too long for this version")
    bits.extend([0] * min(4, capacity - len(bits)))    # terminator
    bits.extend([0] * (-len(bits) % 8))                # byte align
    words = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    for pad in (0xEC, 0x11) * data_cw:
        if len(words) >= data_cw:
            break
        words.append(pad)

    # split into blocks, compute EC per block, interleave
    pos, dblocks, eblocks = 0, [], []
    for size in blocks:
        blk = words[pos:pos + size]
        pos += size
        dblocks.append(blk)
        eblocks.append(_rs_ec(blk, ec_n))
    out: list[int] = []
    for i in range(max(blocks)):
        out.extend(blk[i] for blk in dblocks if i < len(blk))
    for i in range(ec_n):
        out.extend(blk[i] for blk in eblocks)
    return out


# ---- matrix construction ----------------------------------------------------------------------
def _version_for(payload: bytes) -> int:
    for v in range(1, 11):
        overhead = 4 + (16 if v >= 10 else 8)
        if len(payload) * 8 + overhead <= _BLOCKS[v][0] * 8:
            return v
    raise ValueError("payload too long (max version 10)")


def _bch(value: int, poly: int, bits: int, total: int) -> int:
    """Append BCH remainder: value has `bits` bits, result has `total` bits."""
    shifted = value << (total - bits)
    rem = shifted
    for i in range(total - 1, total - bits - 1, -1):   # divide by the generator, degree total-bits
        if rem >> i & 1:
            rem ^= poly << (i - (total - bits))
    return shifted | rem


def _format_bits(mask: int) -> int:
    return _bch((0b00 << 3) | mask, 0b10100110111, 5, 15) ^ 0b101010000010010   # level M = 00


def _version_bits(version: int) -> int:
    return _bch(version, 0b1111100100101, 6, 18)


def _place_function_patterns(m: list[list[int | None]], version: int) -> None:
    n = len(m)

    def finder(r0: int, c0: int) -> None:
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = r0 + r, c0 + c
                if 0 <= rr < n and 0 <= cc < n:
                    inside = 0 <= r <= 6 and 0 <= c <= 6
                    ring = inside and (r in (0, 6) or c in (0, 6) or (2 <= r <= 4 and 2 <= c <= 4))
                    m[rr][cc] = 1 if ring else 0
    finder(0, 0)
    finder(0, n - 7)
    finder(n - 7, 0)
    for r in _ALIGN[version]:                          # alignment (before timing: some centres sit on row/col 6)
        for c in _ALIGN[version]:
            if (r <= 8 and c <= 8) or (r <= 8 and c >= n - 9) or (r >= n - 9 and c <= 8):
                continue                               # would overlap a finder pattern
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    m[r + dr][c + dc] = 1 if max(abs(dr), abs(dc)) != 1 else 0
    for i in range(8, n - 8):                          # timing
        if m[6][i] is None:
            m[6][i] = 1 - (i & 1)
        if m[i][6] is None:
            m[i][6] = 1 - (i & 1)
    for i in range(9):                                 # format-info areas (filled later)
        if i != 6:
            m[8][i] = m[i][8] = 0
        if i < 8:
            m[8][n - 1 - i] = 0
            m[n - 1 - i][8] = 0
    m[n - 8][8] = 1                                    # the always-dark module
    if version >= 7:                                   # version-info areas (filled later)
        for i in range(6):
            for j in range(3):
                m[i][n - 11 + j] = m[n - 11 + j][i] = 0


def _place_data(m: list[list[int | None]], reserved: list[list[bool]], words: list[int], version: int) -> None:
    n = len(m)
    bits = [(w >> (7 - k)) & 1 for w in words for k in range(8)] + [0] * _REMAINDER_BITS[version]
    idx = 0
    col = n - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(n - 1, -1, -1) if upward else range(n)
        for r in rows:
            for c in (col, col - 1):
                if not reserved[r][c]:
                    m[r][c] = bits[idx] if idx < len(bits) else 0
                    idx += 1
        upward = not upward
        col -= 2


def _mask_fn(mask: int):
    return [
        lambda r, c: (r + c) % 2 == 0,
        lambda r, c: r % 2 == 0,
        lambda r, c: c % 3 == 0,
        lambda r, c: (r + c) % 3 == 0,
        lambda r, c: (r // 2 + c // 3) % 2 == 0,
        lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
        lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0,
        lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0,
    ][mask]


def _penalty(m: list[list[int]]) -> int:
    n = len(m)
    score = 0
    for lines in (m, [list(col) for col in zip(*m)]):  # rule 1: runs of 5+
        for line in lines:
            run, prev = 0, None
            for v in line + [None]:
                if v == prev:
                    run += 1
                else:
                    if run >= 5:
                        score += 3 + (run - 5)
                    run, prev = 1, v
    for r in range(n - 1):                             # rule 2: 2x2 blocks
        for c in range(n - 1):
            if m[r][c] == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]:
                score += 3
    pat1, pat2 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
    for lines in (m, [list(col) for col in zip(*m)]):  # rule 3: finder-like patterns
        for line in lines:
            for i in range(n - 10):
                if line[i:i + 11] in (pat1, pat2):
                    score += 40
    dark = sum(map(sum, m))                            # rule 4: dark-module balance
    k = abs(dark * 100 // (n * n) - 50) // 5
    score += k * 10
    return score


def encode(text: str) -> list[list[int]]:
    payload = text.encode("utf-8")
    version = _version_for(payload)
    n = 17 + 4 * version
    base: list[list[int | None]] = [[None] * n for _ in range(n)]
    _place_function_patterns(base, version)
    reserved = [[v is not None for v in row] for row in base]
    words = _codewords(payload, version)
    _place_data(base, reserved, words, version)
    best, best_score = None, None
    for mask in range(8):
        fn = _mask_fn(mask)
        m = [[(base[r][c] ^ 1 if fn(r, c) else base[r][c]) if not reserved[r][c] else base[r][c]
              for c in range(n)] for r in range(n)]
        fmt = _format_bits(mask)
        fbits = [(fmt >> (14 - i)) & 1 for i in range(15)]
        for i in range(6):
            m[8][i] = fbits[i]
            m[i][8] = fbits[14 - i]
        m[8][7], m[8][8], m[7][8] = fbits[6], fbits[7], fbits[8]
        for i in range(8):
            m[8][n - 1 - i] = fbits[14 - i]
            m[n - 1 - i][8] = fbits[i]
        m[n - 8][8] = 1
        if version >= 7:
            vb = _version_bits(version)
            for i in range(18):
                bit = (vb >> i) & 1
                m[i // 3][n - 11 + i % 3] = bit
                m[n - 11 + i % 3][i // 3] = bit
        score = _penalty(m)  # type: ignore[arg-type]
        if best_score is None or score < best_score:
            best, best_score = m, score
    return best  # type: ignore[return-value]


def as_strings(matrix: list[list[int]]) -> list[str]:
    return ["".join("1" if v else "0" for v in row) for row in matrix]


if __name__ == "__main__":
    import sys
    for row in encode(sys.argv[1] if len(sys.argv) > 1 else "https://example.com/"):
        print("".join("██" if v else "  " for v in row))
