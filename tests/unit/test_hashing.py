from australian_health_policy_atlas.hashing import sha256_json, sha256_text


def test_canonical_json_hash_is_key_order_invariant() -> None:
    assert sha256_json({"b": 2, "a": 1}) == sha256_json({"a": 1, "b": 2})


def test_text_hash_is_stable() -> None:
    assert (
        sha256_text("abc")
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
