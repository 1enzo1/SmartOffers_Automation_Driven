from pathlib import Path


def test_home_contains_an_isolated_standard_qa4_mock_control_seam():
    html = Path("templates/index.html").read_text(encoding="utf-8")

    assert 'id="qa4StandardEnvironment"' in html
    assert 'id="qa4StandardProfile"' in html
    assert 'id="runQa4StandardMockButton"' in html
    assert "Executar Standard mock" in html
    assert 'id="qa4StandardMockResult"' in html
    assert 'onclick="runQa4StandardMock()"' in html
    assert 'fetch("/api/qa4/standard/mock-run"' in html
    assert "getRunStatusMeta" in html


def test_standard_qa4_mock_control_uses_the_http_contract_environment_value():
    html = Path("templates/index.html").read_text(encoding="utf-8")

    assert '<option value="QA4" selected>QA4</option>' in html


def test_standard_qa4_mock_handler_uses_text_only_result_rendering():
    html = Path("templates/index.html").read_text(encoding="utf-8")
    start = html.index("async function runQa4StandardMock()")
    end = html.index("\nfunction ", start + 1)
    handler = html[start:end]

    assert "textContent" in handler
    assert "innerHTML" not in handler
    assert "/api/qa4/standard/mock-run" in handler
