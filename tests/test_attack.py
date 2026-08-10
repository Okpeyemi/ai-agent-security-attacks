import re

import attack


def test_labels_unique_and_clean():
    labels = [attack._label(i) for i in range(2000)]
    assert len(set(labels)) == 2000  # all distinct
    for lab in labels:
        assert re.fullmatch(r"[a-z]{2}\d*", lab)  # letters then optional digits
        low = lab.lower()
        for word in attack.SENSITIVE_WORDS:
            assert word not in low


def test_msg_is_clean_and_short():
    for i in (0, 1, 675, 676, 1999):
        m = attack._msg(i)
        assert attack.PAYLOAD in m
        assert attack._url(i) in m
        assert len(m) <= 120  # short prompt keeps replay cost low
        low = m.lower()
        for bad in attack._FORBIDDEN_MSG_SUBSTRINGS:
            assert bad not in low


def test_forge_msg_appends_harmony_suffix():
    plain = attack._msg(3, forge=False)
    forged = attack._msg(3, forge=True)
    assert forged.startswith(plain) or attack.PAYLOAD in forged
    assert forged.endswith(attack.FORGE_SUFFIX)
    assert "<|channel|>analysis" in forged
