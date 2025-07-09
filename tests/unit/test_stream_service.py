import pytest
from app.services.stream_service import StreamService

service = StreamService()

@pytest.mark.parametrize("url,expected", [
    ("acestream://abc123def456abc123def456abc123def456abc123de", "abc123def456abc123def456abc123def456abc123de"),
    ("http://example.com/ace/getstream?id=abc123def456abc123def456abc123def456abc123de", "abc123def456abc123def456abc123def456abc123de"),
    ("http://example.com/stream/abc123def456abc123def456abc123def456abc123de", "abc123def456abc123def456abc123def456abc123de"),
    ("http://example.com/stream?pid=abc123def456abc123def456abc123def456abc123de", "abc123def456abc123def456abc123def456abc123de"),
    ("http://example.com/stream?acestream_id=abc123def456abc123def456abc123def456abc123de", "abc123def456abc123def456abc123def456abc123de"),
    ("http://example.com/no-id-here", None),
    ("not-a-url", None),
    ("", None),
    (None, None),
    (12345, None),
])
def test_extract_acestream_id(url, expected):
    assert service.extract_acestream_id(url) == expected
