import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from bav.dupont import dupont_3, dupont_5


def test_dupont_consistency():
    r3 = dupont_3(100, 1000, 2000, 800)
    assert abs(r3["roe"] - 100 / 800) < 1e-12
    r5 = dupont_5(100, 130, 150, 1000, 2000, 800)
    assert abs(r5["roe"] - 100 / 800) < 1e-12
