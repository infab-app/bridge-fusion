import os
import sys
from pathlib import Path

ADDIN_NAME = "Bridge"
COMPANY_NAME = "Infab"
VERSION = "0.1.0"

ADDIN_DIR = Path(os.path.dirname(os.path.realpath(__file__)))

# Dev mode: set to True to use localhost URLs for testing
DEV_MODE = True

# URLs
if DEV_MODE:
    AUTH_URL = "http://localhost:4000"
    BRIDGE_APP_URL = "http://localhost:5176"
    API_URL = "http://localhost:3000"
else:
    AUTH_URL = "https://auth.infab.app"
    BRIDGE_APP_URL = "https://bridge.infab.app"
    API_URL = "https://api.infab.app"

# Command IDs
CMD_BRIDGE = "bridge_open"
CMD_VIEW_LOG = "bridge_view_log"

# Toolbar IDs
TOOLBAR_TAB_ID = "BridgeTab"
TOOLBAR_PANEL_ID = "BridgePanel"

# Palette IDs
PALETTE_BRIDGE_ID = "BridgePalette"
PALETTE_BRIDGE_NAME = "Infab Bridge"

# Palette dimensions
PALETTE_BRIDGE_WIDTH = 500
PALETTE_BRIDGE_HEIGHT = 700

# Export formats supported
ALLOWED_EXPORT_FORMATS = ["f3d", "step", "stl", "igs"]

# Platform-dependent paths
if sys.platform == "win32":
    _BASE_DIR = Path(os.environ.get("APPDATA", Path.home())) / ".bridge"
else:
    _BASE_DIR = Path.home() / ".bridge"

SESSION_FILE = _BASE_DIR / "session.json"
SETTINGS_FILE = _BASE_DIR / "settings.json"
TEMP_EXPORT_DIR = _BASE_DIR / "temp_exports"
LOG_DIR = _BASE_DIR / "logs"

# Icon resource paths
ICON_BRIDGE = str(ADDIN_DIR / "resources" / "bridge")

# Workspaces to add toolbar to
TARGET_WORKSPACES = ["FusionSolidEnvironment", "CAMEnvironment"]

# Session refresh interval (seconds)
SESSION_REFRESH_INTERVAL = 6 * 60 * 60

# HTTP request timeout (seconds)
HTTP_TIMEOUT = 30

# S3 upload timeout (seconds)
S3_UPLOAD_TIMEOUT = 300
