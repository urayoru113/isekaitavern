import aiohttp

from isekaitavern.errno.basic import TransmittableException
from isekaitavern.utils.logging import logger


class ImageDownloadError(TransmittableException):
    pass


async def download_url_bytes(
    session: aiohttp.ClientSession,
    url: str,
    *,
    max_size: int = 10 * 1024 * 1024,
    allowed_content_types: list[str] | None = None,  # e.g:['image/']
) -> bytes:
    """Downloads the content from the given URL and returns it as bytes."""
    if allowed_content_types is None:
        allowed_content_types = ["image/"]

    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                logger.error(f"Download failed: {url}, HTTP status code: {resp.status}")
                raise ImageDownloadError(f"Unable to download image, HTTP status code: {resp.status}.")

            content_type = resp.content_type
            if content_type:
                if not any(content_type.startswith(t) for t in allowed_content_types):
                    logger.error(f"Download failed: {url}, invalid content type: {content_type}")
                    raise ImageDownloadError(f"Invalid content type: {content_type}.")
            elif allowed_content_types:
                logger.error(f"Download failed: {url}, unable to determine content type.")
                raise ImageDownloadError("Unable to determine content type.")

            if resp.content_length is not None and resp.content_length > max_size:
                logger.error(f"Download failed: {url}, file too large (Content-Length): {resp.content_length}")
                raise ImageDownloadError(f"Download failed, file too large (Content-Length): {resp.content_length}.")

            image_bytes = await resp.read()

            if len(image_bytes) > max_size:
                logger.error(f"Download failed: {url}, file too large (actual size): {len(image_bytes)}")
                raise ImageDownloadError(f"Image too large (actual size): {len(image_bytes)} bytes.")

            logger.info(f"Downloaded successfully: {url}, size: {len(image_bytes)} bytes")
            return image_bytes

    except aiohttp.ClientError as e:
        logger.error(f"Download failed: {url}, error: {e}")
        raise ImageDownloadError(f"Download failed: {url}, error: {e}") from e
    except Exception as e:
        logger.error(f"Unknown error occurred while downloading {url}: {type(e).__name__}: {e}")
        raise ImageDownloadError(f"Unknown error occurred while downloading {url}: {type(e).__name__}: {e}") from e
