import re


def _page(app_client_factory):
    client, _ = app_client_factory("accessibility")
    response = client.get("/")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_primary_product_controls_have_native_elements_and_labels(app_client_factory):
    html = _page(app_client_factory)
    assert '<label for="productEnvironment">' in html
    assert '<label for="productTest">' in html
    assert re.search(r'<button[^>]+id="productValidate"', html)
    assert re.search(r'<button[^>]+id="productExecute"', html)
    assert re.search(r'<button[^>]+id="productViewEvidence"', html)


def test_secondary_surfaces_are_keyboard_operable_and_distinct(app_client_factory):
    html = _page(app_client_factory)
    assert '<details id="diagnosticsNav">' in html
    assert '<details id="diagnosticsSidebar">' in html
    assert re.search(r'<details[^>]+id="controlledEvidence"', html)
    assert '<h2>Historical runs</h2>' in html
    assert html.count('id="productValidate"') == 1
    assert html.count('id="productExecute"') == 1


def test_validate_and_execute_start_disabled_without_selected_test(app_client_factory):
    html = _page(app_client_factory)
    assert re.search(r'id="productValidate"[^>]*disabled', html)
    assert re.search(r'id="productExecute"[^>]*disabled', html)


def test_workspace_tabs_expose_selection_and_panel_relationships(app_client_factory):
    html = _page(app_client_factory)
    assert 'id="tab-product"' in html and 'aria-controls="panel-product"' in html
    assert 'id="tab-history"' in html and 'aria-controls="panel-history"' in html
    assert 'id="tab-product" type="button" aria-selected="true"' in html
    assert 'id="tab-history" type="button" aria-selected="false"' in html


def test_dynamic_product_readiness_and_execution_messages_are_live_regions(app_client_factory):
    html = _page(app_client_factory)
    assert 'id="productReadinessSummary"' in html and 'aria-live="polite"' in html
    assert 'id="productExecuteReason"' in html and 'aria-live="polite"' in html
