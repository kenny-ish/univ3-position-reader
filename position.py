"""Read a Uniswap v3 position NFT and value it."""
import argparse
import json
import math
import urllib.request

NPM = "0xC36442b4a4522E871399CD717aBDD847Ab11FE88"
FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"
POSITIONS, GET_POOL, SLOT0 = "0x99fbab88", "0x1698ee82", "0x3850c7bd"
SYMBOL, DECIMALS = "0x95d89b41", "0x313ce567"


def call(url, to, data):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, "latest"]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "univ3-position-reader"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(resp["error"].get("message"))
    return resp["result"]


def words(hexdata):
    d = hexdata[2:]
    return [d[i:i + 64] for i in range(0, len(d), 64)]


def signed(word_hex):
    v = int(word_hex, 16)
    return v - 2**256 if v >= 2**255 else v


def decode_position(hexdata):
    w = words(hexdata)
    return {"token0": "0x" + w[2][24:], "token1": "0x" + w[3][24:], "fee": int(w[4], 16),
            "tick_lower": signed(w[5]), "tick_upper": signed(w[6]), "liquidity": int(w[7], 16),
            "owed0": int(w[10], 16), "owed1": int(w[11], 16)}


def amounts(liquidity, sqrt_price_x96, tick_lower, tick_upper):
    sp = sqrt_price_x96 / 2**96
    sa = math.sqrt(1.0001 ** tick_lower)
    sb = math.sqrt(1.0001 ** tick_upper)
    if sp <= sa:
        return liquidity * (sb - sa) / (sa * sb), 0.0
    if sp < sb:
        return liquidity * (sb - sp) / (sp * sb), liquidity * (sp - sa)
    return 0.0, liquidity * (sb - sa)


def symbol(url, token):
    raw = bytes.fromhex(call(url, token, SYMBOL)[2:])
    return raw.rstrip(b"\0").decode() if len(raw) == 32 else raw[64:64 + int.from_bytes(raw[32:64], "big")].decode()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("token_id", type=int)
    ap.add_argument("--rpc", default="https://ethereum-rpc.publicnode.com")
    a = ap.parse_args()

    try:
        p = decode_position(call(a.rpc, NPM, POSITIONS + format(a.token_id, "064x")))
    except RuntimeError as e:
        raise SystemExit(f"position {a.token_id} not found ({e})")
    pool = "0x" + words(call(a.rpc, FACTORY, GET_POOL + p["token0"][2:].rjust(64, "0") + p["token1"][2:].rjust(64, "0")
                             + format(p["fee"], "064x")))[0][24:]
    s = words(call(a.rpc, pool, SLOT0))
    sqrt_price, tick = int(s[0], 16), signed(s[1])
    s0, s1 = symbol(a.rpc, p["token0"]), symbol(a.rpc, p["token1"])
    d0, d1 = (int(call(a.rpc, t, DECIMALS), 16) for t in (p["token0"], p["token1"]))
    price = lambda t: 1.0001 ** t * 10 ** (d0 - d1)  # token1 per token0
    a0, a1 = amounts(p["liquidity"], sqrt_price, p["tick_lower"], p["tick_upper"])
    in_range = p["tick_lower"] <= tick < p["tick_upper"]

    print(f"position #{a.token_id}: {s0}/{s1} {p['fee'] / 10_000:.2f}% pool {pool}")
    print(f"range        {price(p['tick_lower']):.6g} - {price(p['tick_upper']):.6g} {s1} per {s0}  (ticks {p['tick_lower']}..{p['tick_upper']})")
    print(f"current      {price(tick):.6g} {s1} per {s0}  -> {'IN RANGE' if in_range else 'out of range, earning no fees'}")
    print(f"liquidity    {p['liquidity']}")
    print(f"holdings     {a0 / 10 ** d0:,.6f} {s0} + {a1 / 10 ** d1:,.6f} {s1}")
    print(f"owed         {p['owed0'] / 10 ** d0:,.6f} {s0} + {p['owed1'] / 10 ** d1:,.6f} {s1}  (credited, not yet collected)")


if __name__ == "__main__":
    main()
