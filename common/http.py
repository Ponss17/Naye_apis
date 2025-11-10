import os
import requests
from requests.adapters import HTTPAdapter
try:
    from urllib3.util import Retry
except Exception:
    from urllib3.util.retry import Retry  # type: ignore


def get_session(user_agent: str | None = None) -> requests.Session:
    ua = user_agent or os.environ.get("API_USER_AGENT", "NayeAPIs/1.0")
    s = requests.Session()
    s.headers.update({
        "User-Agent": ua,
        "Connection": "keep-alive",
    })

    retry = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s