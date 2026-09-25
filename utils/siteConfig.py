"""
Public URL configuration for the web pages and the Flash client.

Every template gets a `SITE` object (see app.py's context processor):

  SITE.server_url  scheme://host[:port] of this server, no trailing slash.
                   Used for links and form actions (e.g. /authenticate).
  SITE.assets_url  Base URL for page assets (CSS, JS, images), no trailing
                   slash. Files live under /assets and /templates/styles.
  SITE.api_host    host[:port] for the flash var `apiHost`. The client adds
                   the scheme itself and calls {apiHost}/ZooApi.php.
  SITE.cdn_host    host[:port]/path for the flash var `cdnHost`. The client
                   adds the scheme itself and loads {cdnHost}{cv path}.
  SITE.is_https    Whether the client should use https:// (flash var `isHTTPS`).
  SITE.swf_suffix  "-DEBUG" in local dev mode (loads Zoomumba-DEBUG.swf).

Environment variables (all optional):

  PUBLIC_URL   Public base URL, e.g. https://zoomumba.example.com. Set this
               when the server runs behind a proxy/tunnel whose address
               differs from what Flask sees. If unset, it's taken from the
               incoming request.
  ASSETS_URL   Base URL for page assets and the game's CDN files. Defaults to
               PUBLIC_URL. Must use the same scheme (the Flash client forces
               its own http/https on cdnHost).
  TRUST_PROXY  1 = honour X-Forwarded-Proto/-Host from a reverse proxy
               (cloudflared, nginx, ...), so pages behind an https proxy don't
               link to http:// URLs. Defaults to 1 unless LOCAL_DEV_MODE=1.
"""
import os
from dataclasses import dataclass
from urllib.parse import urlparse


# Read lazily: app.py calls load_dotenv() after importing this module.
def _env_flag(name, default):
    return os.getenv(name, default) == "1"


def local_dev_mode():
    return _env_flag("LOCAL_DEV_MODE", "0")


def trust_proxy():
    return _env_flag("TRUST_PROXY", "0" if local_dev_mode() else "1")


@dataclass(frozen=True)
class SiteConfig:
    server_url: str
    assets_url: str
    api_host: str
    cdn_host: str
    is_https: bool
    swf_suffix: str


def _strip_scheme(url):
    parsed = urlparse(url)
    return parsed.netloc + parsed.path.rstrip("/")


def get_site_config(request):
    server_url = (os.getenv("PUBLIC_URL") or "").rstrip("/") or request.host_url.rstrip("/")
    assets_url = (os.getenv("ASSETS_URL") or "").rstrip("/") or server_url
    return SiteConfig(
        server_url=server_url,
        assets_url=assets_url,
        api_host=_strip_scheme(server_url),
        cdn_host=_strip_scheme(assets_url) + "/assets",
        is_https=urlparse(server_url).scheme == "https",
        swf_suffix="-DEBUG" if local_dev_mode() else "",
    )
