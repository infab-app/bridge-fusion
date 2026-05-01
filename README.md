# Bridge for Autodesk Fusion

**An Autodesk Fusion add-in by [Infab Softworks](https://infab.app)** that connects Autodesk Fusion to [Infab Bridge](https://bridge.infab.app), enabling users to upload design files and supporting documents to Infab part definitions directly from within Fusion. Bridge embeds a palette inside Fusion that provides seamless access to your Infab workspace without leaving the CAD environment.

> **Note:** Bridge for Fusion is the open-source client add-in for [Infab Bridge](https://infab.app), a cloud platform that requires an active Infab subscription. The add-in source code is publicly available, but a subscription is required to authenticate and use the service.

## How It Works

Bridge adds an **Infab Bridge** palette to Fusion that connects directly to your Infab account. From there you can browse parts, upload design files, and load models into Fusion, all without leaving the application.

1. **Sign In** — Authenticate with your Infab account through the embedded palette
2. **Browse & Select** — Navigate your Infab parts and definitions within Fusion
3. **Upload** — Select a design and have it uploaded directly to a line item as a supporting document
4. **Download** — Download models from Infab and load them directly into Fusion in supported formats 

### Key Features

- **Embedded Palette** — A docked HTML palette inside Fusion provides full access to your Infab Bridge workspace without switching applications.
- **Multi-Format Upload** — Upload designs or Fusion exports as supporting documents to line items.
- **Model Download** — Download models from Infab and load them directly into Fusion with automatic format detection.
- **Secure Authentication** — Session management with token exchange, automatic session refresh, and secure local session persistence.
- **Structured Logging** — Per-session JSONL log files with timestamps, event details, severity levels, and machine context for diagnostics and troubleshooting.
- **Cross-Platform** — Single Python codebase for Windows and macOS.

## Installation

The `Bridge` folder in this repository is the complete add-in. Copy just this folder into Autodesk Fusion's add-ins directory.

**Option 1: Download from GitHub Releases (recommended)**

1. Go to the [latest release](https://github.com/infab-app/bridge-fusion/releases/latest)
2. Download `Bridge-v{version}.zip`
3. Extract the zip — you'll get a `Bridge/` folder
4. Drag-and-drop or copy the `Bridge` folder into Autodesk Fusion's add-ins directory:
   - **Windows:** `%AppData%\Autodesk\Autodesk Fusion\API\AddIns\`
   - **macOS:** `~/Library/Application Support/Autodesk/Autodesk Fusion/API/AddIns/`

**Option 2: Download the repository as a ZIP**

1. Click **Code > Download ZIP** on the repository page
2. Extract the zip and copy only the `Bridge` folder into the add-ins directory above

**Option 3: Clone with git**

**Windows:**
```
git clone https://github.com/infab-app/bridge-fusion.git
xcopy /E bridge-fusion\Bridge "%AppData%\Autodesk\Autodesk Fusion\API\AddIns\Bridge\"
```

**macOS:**
```
git clone https://github.com/infab-app/bridge-fusion.git
cp -R bridge-fusion/Bridge ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/AddIns/Bridge
```

> **Important:** For options 2 and 3, copy only the `Bridge` folder, not the entire repository. The other files (CI config, linter config) are for development and are not needed by the add-in.

### Updating

To update, delete the existing `Bridge` folder from your Autodesk Fusion add-ins directory and replace it with the `Bridge` folder from the [latest release](https://github.com/infab-app/bridge-fusion/releases/latest). Your session data and logs are stored separately (`~/.bridge/`) and will not be affected.

The resulting directory in your Add-Ins folder should look like:
```
Bridge/
├── Bridge.py
├── Bridge.manifest
├── bridge_config.py
├── bridge_lib/
├── bridge_commands/
├── resources/
└── ...
```

Then in Autodesk Fusion:
1. Open **Utilities > Add-Ins** (or press `Shift+S` by default)
2. Go to the **Add-Ins** tab
3. Click the green **+** icon and navigate to the `Bridge` folder (or it may appear automatically)
4. Check **Run on Startup** (recommended)
5. Click **Run**

## Usage

Once running, Bridge adds a **Bridge** tab to the toolbar in both the Design and Manufacture workspaces.

### Signing In

1. Click **Open Bridge** in the Bridge toolbar tab
2. The Infab Bridge palette opens inside Fusion
3. Sign in with your Infab account credentials
4. Your session is saved locally and refreshes automatically

### Uploading Design Files

1. Open or create a design in Fusion
2. Open the Bridge palette and navigate to a part definition
3. Select the file and click upload
4. Your design is uploaded to Infab via authenticated URLs

### Downloading Models

1. Browse your Infab parts in the Bridge palette
2. Select a model to download
3. The model is downloaded and loaded directly into Fusion

## Repository Structure

```
bridge-fusion/
├── Bridge/                        # Add-in folder (copy this into Autodesk Fusion)
│   ├── Bridge.py                  # Entry point
│   ├── Bridge.manifest            # Add-in metadata
│   ├── bridge_config.py           # Configuration and constants
│   ├── bridge_lib/
│   │   ├── auth_manager.py        # Session and authentication
│   │   ├── infab_client.py        # HTTP client for Infab API
│   │   ├── palette_manager.py     # UI palette management
│   │   ├── export_manager.py      # File export and upload
│   │   ├── bridge_logger.py       # Structured JSONL logging
│   │   ├── settings.py            # Persistent settings
│   │   ├── ui_components.py       # Toolbar and button setup
│   │   ├── integrity.py           # Checksum verification
│   │   └── path_validation.py     # Path and URL security validation
│   ├── bridge_commands/
│   │   ├── open_bridge.py         # Open Bridge palette command
│   │   └── view_log.py            # View log command
│   └── resources/                 # Toolbar icons (16x16 and 32x32 PNG)
├── .github/workflows/             # CI and release workflows
└── ruff.toml                      # Linter configuration
```

## Logs

Logs are stored as JSONL files at:
- **Windows:** `%APPDATA%\.bridge\logs\`
- **macOS:** `~/.bridge/logs/`

Each line is a JSON object with timestamp, event name, detail, severity, user, and machine name. Click **View Log** in the Bridge toolbar to open the current log file.

## Requirements

- **Autodesk Fusion** (Windows or macOS)
- **Infab subscription** — Bridge connects to [Infab Bridge](https://bridge.infab.app), which requires an active Infab account. [Learn more at infab.app](https://infab.app).
- **Internet connection** — Required for authentication and file upload/download

## License

This repository is source-available. The code is provided for transparency, review, and community contribution. Bridge for Fusion is not licensed under MIT or any other open-source license. All rights are reserved by Infab Softworks unless otherwise stated. See [LICENSE](LICENSE) for details.

---

Built and maintained by **[Infab Softworks](https://infab.app)**
