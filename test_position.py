import unittest

from position import amounts, decode_position, signed


def w(n):
    return format(n % 2**256, "064x")


class PositionTest(unittest.TestCase):
    def test_signed_ticks(self):
        self.assertEqual(signed(w(-887220)), -887220)
        self.assertEqual(signed(w(200)), 200)

    def test_decode_position(self):
        t0, t1 = "aa" * 20, "bb" * 20
        data = "0x" + w(0) + w(0) + "0" * 24 + t0 + "0" * 24 + t1 + w(500) + w(-100) + w(100) + w(10**18) + w(0) + w(0) + w(7) + w(9)
        p = decode_position(data)
        self.assertEqual((p["token0"], p["fee"], p["tick_lower"], p["tick_upper"]), ("0x" + t0, 500, -100, 100))
        self.assertEqual((p["liquidity"], p["owed0"], p["owed1"]), (10**18, 7, 9))

    def test_amounts_by_region(self):
        L = 10**6
        below = amounts(L, int(0.5 * 2**96), 0, 100)  # price below range: all token0
        above = amounts(L, int(2.0 * 2**96), -100, 0)  # price above range: all token1
        inside = amounts(L, 2**96, -100, 100)
        self.assertGreater(below[0], 0)
        self.assertEqual(below[1], 0)
        self.assertEqual(above[0], 0)
        self.assertGreater(above[1], 0)
        self.assertGreater(inside[0], 0)
        self.assertGreater(inside[1], 0)
        # symmetric range around price 1: equal amounts of both
        self.assertAlmostEqual(inside[0], inside[1], delta=inside[0] * 1e-9)


if __name__ == "__main__":
    unittest.main()
