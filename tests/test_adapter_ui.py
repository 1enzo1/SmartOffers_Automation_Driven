def test_home_renders_adapter_execution_panel(app_client_factory):
    client, _ = app_client_factory("adapter-ui")

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "Adapters / Execu&ccedil;&atilde;o Controlada" in html
    assert 'id="adapterList"' in html
    assert 'id="adapterHealthList"' in html
    assert 'onclick="runAdapterRun()"' in html
    assert "/api/adapters" in html
    assert "/adapter-run" in html


def test_home_renders_legacy_runner_status_states(app_client_factory):
    client, _ = app_client_factory("presentation-ui")

    response = client.get("/")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "status-pass" in html
    assert "status-fail" in html
    assert "status-blocked" in html
    assert "status-running" in html
    assert 'data-filter="blocked"' in html
    assert 'data-filter="running"' in html
    assert "Guard real ativo por padrao" in html
    assert "getRunStatusMeta" in html
