import urllib.parse as urllib


def extract_youtube_url(url):
    """Extract the real youtube vedio url from a youtube url."""
    if "youtube.com" not in url and "youtu.be" not in url:
        raise ValueError(f"Invalid youtube url: {url}")
    url_data = urllib.urlparse(url)
    query = urllib.parse_qs(url_data.query)
    real_url = f"{url_data.scheme}://{url_data.hostname}/{url_data.path}"
    if "v" in query:
        real_url += f"?v={query['v'][0]}"
    return real_url
