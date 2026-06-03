import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

#creating sessions
def get_session():

    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET", "POST"]
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session