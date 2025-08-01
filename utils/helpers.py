def array_diff(a1, a2):
    s1 = set(a1)
    s2 = set(a2)

    assert len(a1) == len(s1), f"Duplicate entries in {a1}"
    assert len(a2) == len(s2), f"Duplicate entries in {a2}"

    a1_only = list(s1 - s2)
    a2_only = list(s2 - s1)

    matching = len(a1_only) == 0 and len(a2_only) == 0

    return (matching, a1_only, a2_only)

