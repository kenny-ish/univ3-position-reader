# univ3-position-reader

Reads a Uniswap v3 liquidity position (an NFT) by its token id and computes what it holds at the
current price.

```bash
python position.py 1
python position.py 912345 --rpc http://localhost:8545
```

The calls, all `eth_call`:

1. `NonfungiblePositionManager.positions(id)` for token0, token1, fee tier, tick range and liquidity
   (`0xC36442b4...FE88`).
2. `UniswapV3Factory.getPool(token0, token1, fee)`, then `pool.slot0()` for the current
   `sqrtPriceX96` and tick.
3. Symbols and decimals of both tokens.

The amounts come from the v3 liquidity formulas:

```
sp = sqrtPriceX96 / 2^96, sa = sqrt(1.0001^tickLower), sb = sqrt(1.0001^tickUpper)
below range: amount0 = L (sb - sa) / (sa sb),  amount1 = 0
in range:    amount0 = L (sb - sp) / (sp sb),  amount1 = L (sp - sa)
above range: amount0 = 0,                      amount1 = L (sb - sa)
```

It prints the range as prices, whether the position is in range, the current amount of each token,
and `tokensOwed0/1`, the fees already credited to the position. Fees earned since the last update
need the pool's fee growth accounting and are not included.

## Tests

```bash
python -m unittest -v
```
