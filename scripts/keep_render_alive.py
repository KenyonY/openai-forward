from urllib.parse import urljoin

import httpx
import schedule


def job(url: str = "https://render.openai-forward.com"):
    health_url = urljoin(url, "/healthz")
    try:
        r = httpx.get(health_url, timeout=5)
        result = r.json()
        print(result)
        assert result == "OK"
    except Exception as e:
        print(e)


if __name__ == "__main__":
    job()
    schedule.every(12).minutes.do(job)
    while True:
        schedule.run_pending()
