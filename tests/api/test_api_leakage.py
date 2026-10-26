import pytest
import re

INTERNALS = [
    "Traceback",
    "File",
    "site-packages",
    "sk-ant",
]

PYTHON_FILE = re.compile(r"[\w_.-]+\.py\b")  #test_.py

ERROR_REQUESTS = [
    pytest.param("POST", "/retrieve", {"question": "   "}, 400, id="blank-question-400"),
    pytest.param("POST", "/retrieve", {"question": ""}, 422, id="empty-question-422"),
    pytest.param("POST", "/retrieve", {"question": "x", "top_k": 0}, 422, id="bad-top-k-422"),
    pytest.param("POST", "/retrieve", {}, 422, id="no-question-422"),
    pytest.param("GET", "/ask", None, 405, id="wrong-method-405"),
    pytest.param("GET", "/no-such-page", None, 404, id="unknown-page-404"),
]
