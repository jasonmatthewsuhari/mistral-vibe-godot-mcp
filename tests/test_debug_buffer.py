from mcp_server.debug_buffer import DebugRingBuffer


def test_cursor_and_limit_pagination() -> None:
    buffer = DebugRingBuffer(max_entries=10)
    for i in range(5):
        buffer.append("stdout", f"line-{i}", timestamp=f"t{i}")

    first = buffer.get(limit=2)
    assert [entry["message"] for entry in first["entries"]] == ["line-0", "line-1"]
    assert first["next_cursor"] == 2

    second = buffer.get(limit=2, cursor=first["next_cursor"])
    assert [entry["message"] for entry in second["entries"]] == ["line-2", "line-3"]
    assert second["next_cursor"] == 4


def test_ring_buffer_discards_oldest_entries() -> None:
    buffer = DebugRingBuffer(max_entries=3)
    for i in range(6):
        buffer.append("stderr", f"err-{i}", timestamp=f"t{i}")

    view = buffer.get(limit=10)
    assert [entry["message"] for entry in view["entries"]] == ["err-3", "err-4", "err-5"]
    assert view["entries"][0]["idx"] == 3

