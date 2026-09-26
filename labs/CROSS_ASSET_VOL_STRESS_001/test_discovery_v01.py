from datetime import date
from labs.CROSS_ASSET_VOL_STRESS_001 import discovery_v01 as d


def main():
    assert d.EXPECTED_CANONICAL_SHA == '48c16e171c06f61378ac216d75d76a22491b417ae904936c3538a34dfb6ab1be'
    assert list(d.EXPECTED_RAW) == list(range(2018,2025))
    assert d.START == date(2018,1,1) and d.END == date(2024,12,31)
    assert len(list(d.month_iter())) == 84
    # ms timestamp conversion sanity: 2018-01-01 UTC
    assert d.ts_to_date(1514764800000) == date(2018,1,1)
    # basic PF semantics
    assert abs(d.pf([10.0,-5.0,5.0]) - 3.0) < 1e-12
    # deterministic bootstrap and ordered CI
    a=d.block_bootstrap([1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0])
    b=d.block_bootstrap([1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0])
    assert a == b and a[0] <= a[1]
    # prospective timing semantics
    sd=date(2018,12,5); entry=sd+d.timedelta(days=2); exitd=entry+d.timedelta(days=7)
    assert entry == date(2018,12,7) and exitd == date(2018,12,14)
    print('DISCOVERY_SELF_TEST_PASS')

if __name__=='__main__': main()
