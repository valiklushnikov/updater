# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ManekiTerminal Update Server - a Flask-based REST API server that manages software updates for the ManekiTerminal trading application. The server handles version checking, update distribution, and setup file downloads.

## Running the Server

```bash
python update_server.py
```

Server runs on `http://0.0.0.0:5000` with Flask debug mode enabled.

## Architecture

### Core Components

- **`update_server.py`** - Single-file Flask application containing all server logic
- **`ReleaseManager`** class - Handles all release-related operations (version lookup, file retrieval, version listing)

### Release Directory Structure

```
releases/
├── latest.json                      # Points to current latest version
├── ManekiTerminal-Setup-X.X.X.exe   # Installer files (in root)
└── X.X.X/                           # Version-specific folders
    ├── ManekiTerminal.exe           # Application binary
    └── version.json                 # Version metadata
```

### Version JSON Schema

```json
{
  "version": "0.0.4",
  "build": 1768486726,
  "release_date": "2026-01-15T16:18:46.907736",
  "download_url": "https://update.maneki.trading/api/updates/download/0.0.4",
  "size": 17376768,
  "sha256": "hash",
  "changelog": ["Change 1", "Change 2"],
  "required": false,
  "min_version": "0.0.1"
}
```

## API Endpoints

### Terminal Updates
- `GET /api/updates/latest` - Get latest version info
- `GET /api/updates/check?current=X.X.X` - Check for updates
- `GET /api/updates/download/<version>` - Download specific version
- `GET /api/updates/changelog/<version>` - Get version changelog
- `GET /api/updates/versions` - List all available versions

### Setup Downloads
- `GET /api/setup/latest` - Get latest setup info
- `GET /api/setup/download/latest` - Download latest installer
- `GET /api/setup/download/<version>` - Download specific installer

### Health
- `GET /health` - Server health check

## Dependencies

- Flask (web framework)
- Python standard library (pathlib, json)
