import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Adjust sys.path to allow api.index to be imported
import sys
import os
# Assuming tests/ is at the root, and api/ is also at the root.
# api.index will try to import from project root.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Now we can import the app from api.index
# The following import needs to happen *after* sys.path is adjusted
# and *after* the mock for Macronizer is potentially set up if we were mocking at module load time.
# For TestClient, it's better to import app and then mock its dependencies.
from api.index import app, SCANSIONS # SCANSIONS is needed for valid scan_option_index

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_macronizer_instance():
    # This path for patch needs to be where 'macronizer_instance' is looked up by api.index
    # which is 'api.index.macronizer_instance'
    with patch('api.index.macronizer_instance', autospec=True) as mock_macronizer:
        # Configure the mock's methods to return something sensible or be further configurable in tests
        mock_macronizer.gettext.return_value = "mocked_macronized_text"
        # Ensure scan method exists on the mock
        mock_macronizer.scan = MagicMock()
        mock_macronizer.settext = MagicMock()
        yield mock_macronizer

def test_macronize_success_default_options(client, mock_macronizer_instance):
    response = client.post("/api/macronize", json={"text_to_macronize": "test text"})

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["macronized_text"] == "mocked_macronized_text"
    assert json_response["original_text"] == "test text"
    assert json_response["options_used"]["domacronize"] is True # Default

    mock_macronizer_instance.settext.assert_called_once_with("test text")
    # Scan should not be called if scan_option_index is default (0)
    mock_macronizer_instance.scan.assert_not_called()
    mock_macronizer_instance.gettext.assert_called_once_with(
        domacronize=True, alsomaius=False, performutov=False, performitoj=False, markambigs=False
    )

def test_macronize_success_custom_options(client, mock_macronizer_instance):
    # Assuming SCANSIONS has at least 2 options for this test, so index 1 is valid
    valid_scan_index = 0
    if len(SCANSIONS) > 1:
        valid_scan_index = 1

    payload = {
        "text_to_macronize": "custom text",
        "domacronize": False,
        "alsomaius": True,
        "scan_option_index": valid_scan_index,
        "performitoj": True,
        "performutov": True
    }
    response = client.post("/api/macronize", json=payload)

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["macronized_text"] == "mocked_macronized_text"
    assert json_response["original_text"] == "custom text"
    assert json_response["options_used"]["domacronize"] is False
    assert json_response["options_used"]["alsomaius"] is True
    assert json_response["options_used"]["scan_option_index"] == valid_scan_index
    assert json_response["options_used"]["performitoj"] is True
    assert json_response["options_used"]["performutov"] is True

    mock_macronizer_instance.settext.assert_called_once_with("custom text")
    if valid_scan_index > 0:
        # SCANSIONS[valid_scan_index][1] is the actual scan automaton/list
        mock_macronizer_instance.scan.assert_called_once_with(SCANSIONS[valid_scan_index][1])
    else:
        mock_macronizer_instance.scan.assert_not_called()

    mock_macronizer_instance.gettext.assert_called_once_with(
        domacronize=False, alsomaius=True, performutov=True, performitoj=True, markambigs=False
    )

def test_macronize_invalid_scan_option_index(client, mock_macronizer_instance):
    invalid_scan_index = len(SCANSIONS) # This index will always be out of bounds
    response = client.post("/api/macronize", json={
        "text_to_macronize": "test text",
        "scan_option_index": invalid_scan_index
    })

    assert response.status_code == 400
    json_response = response.json()
    assert "Invalid scan_option_index" in json_response["detail"]
    mock_macronizer_instance.gettext.assert_not_called() # Should not reach gettext

def test_macronize_macronizer_exception(client, mock_macronizer_instance):
    mock_macronizer_instance.gettext.side_effect = Exception("Internal Macronizer Error")

    response = client.post("/api/macronize", json={"text_to_macronize": "error text"})

    assert response.status_code == 500
    json_response = response.json()
    assert "An error occurred during macronization" in json_response["detail"]
    assert "Internal Macronizer Error" in json_response["detail"]
    assert "Exception" in json_response["detail"] # Check for exception type in detail

    mock_macronizer_instance.settext.assert_called_once_with("error text")
    # Scan might or might not be called depending on default scan_option_index,
    # but gettext is the one we are making fail.
    mock_macronizer_instance.gettext.assert_called_once()
