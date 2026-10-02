import pytest

from app.services.splitting import InvalidSplitError, split_equally, split_exactly

GROUP = {1, 2, 3, 4}


class TestSplitEqually:
    def test_remainder_goes_to_the_first_members(self):
        assert split_equally(1000, [1, 2, 3], GROUP) == {1: 334, 2: 333, 3: 333}

    def test_remainder_follows_the_given_order(self):
        assert split_equally(1000, [3, 1, 2], GROUP) == {3: 334, 1: 333, 2: 333}

    def test_several_extra_cents(self):
        assert split_equally(4910, [1, 2, 3, 4], GROUP) == {1: 1228, 2: 1228, 3: 1227, 4: 1227}

    def test_exact_division(self):
        assert split_equally(900, [1, 2, 3], GROUP) == {1: 300, 2: 300, 3: 300}

    def test_fewer_cents_than_members(self):
        assert split_equally(2, [1, 2, 3], GROUP) == {1: 1, 2: 1, 3: 0}

    @pytest.mark.parametrize("total", [1, 7, 99, 100, 8450, 123457])
    def test_shares_always_add_up_to_the_total(self, total):
        shares = split_equally(total, [1, 2, 3], GROUP)
        assert sum(shares.values()) == total
        assert max(shares.values()) - min(shares.values()) <= 1

    def test_needs_at_least_one_member(self):
        with pytest.raises(InvalidSplitError, match="al menos una persona"):
            split_equally(1000, [], GROUP)

    def test_rejects_repeated_members(self):
        with pytest.raises(InvalidSplitError, match="repetidas"):
            split_equally(1000, [1, 1, 2], GROUP)

    def test_rejects_members_outside_the_group(self):
        with pytest.raises(InvalidSplitError, match="no pertenece"):
            split_equally(1000, [1, 99], GROUP)


class TestSplitExactly:
    def test_valid_split(self):
        assert split_exactly(5000, [(1, 2000), (2, 3000)], GROUP) == {1: 2000, 2: 3000}

    def test_zero_share_is_allowed(self):
        assert split_exactly(5000, [(1, 5000), (2, 0)], GROUP) == {1: 5000, 2: 0}

    def test_shares_must_add_up_to_the_total(self):
        with pytest.raises(InvalidSplitError, match="El reparto suma 45,00, pero el gasto es de 50,00"):
            split_exactly(5000, [(1, 2000), (2, 2500)], GROUP)

    def test_rejects_negative_amounts(self):
        with pytest.raises(InvalidSplitError, match="negativos"):
            split_exactly(5000, [(1, 6000), (2, -1000)], GROUP)

    def test_rejects_repeated_members(self):
        with pytest.raises(InvalidSplitError, match="repetidas"):
            split_exactly(5000, [(1, 2500), (1, 2500)], GROUP)

    def test_rejects_members_outside_the_group(self):
        with pytest.raises(InvalidSplitError, match="no pertenece"):
            split_exactly(5000, [(1, 2500), (99, 2500)], GROUP)

    def test_needs_at_least_one_share(self):
        with pytest.raises(InvalidSplitError, match="al menos una persona"):
            split_exactly(5000, [], GROUP)
