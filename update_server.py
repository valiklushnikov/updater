"""
Update Server для ManekiTerminal
"""
from flask import Flask, jsonify, send_file, request
from pathlib import Path
import json

app = Flask(__name__)

# Конфигурация
RELEASES_DIR = Path("releases")
RELEASES_DIR.mkdir(exist_ok=True)


class ReleaseManager:
    """Управление релизами"""

    def __init__(self, releases_dir: Path):
        self.releases_dir = releases_dir

    def get_latest_release(self) -> dict:
        """Получить последний релиз Terminal"""
        manifest_file = self.releases_dir / "latest.json"

        if not manifest_file.exists():
            return None

        with open(manifest_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_release(self, version: str) -> dict:
        """Получить конкретный релиз Terminal"""
        # Ищем version.json в папке версии
        manifest_file = self.releases_dir / version / "version.json"

        if not manifest_file.exists():
            return None

        with open(manifest_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_release_file(self, version: str) -> Path:
        """Получить файл Terminal.exe для версии"""
        # Terminal.exe всегда в папке версии
        terminal_file = self.releases_dir / version / "ManekiTerminal.exe"

        if terminal_file.exists():
            return terminal_file

        return None

    def get_latest_setup(self) -> Path:
        """Получить последний Setup файл"""
        # Ищем все Setup файлы в корне releases/
        setup_files = list(self.releases_dir.glob("ManekiTerminal-Setup-*.exe"))

        if not setup_files:
            return None

        # Сортируем по версии (извлекаем версию из имени файла)
        def extract_version(path: Path) -> tuple:
            # ManekiTerminal-Setup-0.0.2.exe -> 0.0.2
            name = path.stem  # ManekiTerminal-Setup-0.0.2
            version_str = name.replace("ManekiTerminal-Setup-", "")  # 0.0.2
            try:
                return tuple(int(x) for x in version_str.split('.'))
            except:
                return (0, 0, 0)

        # Сортируем и берем последний
        setup_files.sort(key=extract_version, reverse=True)
        return setup_files[0]

    def get_setup_by_version(self, version: str) -> Path:
        """Получить Setup конкретной версии"""
        setup_file = self.releases_dir / f"ManekiTerminal-Setup-{version}.exe"

        if not setup_file.exists():
            return None

        return setup_file

    def list_versions(self) -> list:
        """Получить список всех доступных версий Terminal"""
        versions = []

        # Найти все папки с версиями
        for version_dir in self.releases_dir.iterdir():
            if version_dir.is_dir():
                version_json = version_dir / "version.json"
                if version_json.exists():
                    with open(version_json, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        versions.append(data)

        # Сортировать по версии (новые сначала)
        versions.sort(
            key=lambda x: [int(p) for p in x["version"].split(".")],
            reverse=True
        )

        return versions


release_manager = ReleaseManager(RELEASES_DIR)


@app.route('/api/updates/latest', methods=['GET'])
def get_latest():
    """Получить последнюю версию Terminal"""
    try:
        release = release_manager.get_latest_release()

        if not release:
            return jsonify({
                "success": False,
                "error": "No releases available"
            }), 404

        return jsonify({
            "success": True,
            "data": release
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/updates/check', methods=['GET'])
def check_updates():
    """Проверить наличие обновлений Terminal"""
    try:
        current_version = request.args.get('current', '0.0.0')

        latest = release_manager.get_latest_release()

        if not latest:
            return jsonify({
                "success": False,
                "error": "No releases available"
            }), 404

        latest_version = latest['version']

        # Сравнить версии
        update_available = _compare_versions(latest_version, current_version) > 0

        response_data = {
            "success": True,
            "data": {
                "update_available": update_available,
                "latest_version": latest_version,
                "current_version": current_version,
            }
        }

        # Если обновление доступно (или это первая установка)
        if update_available or current_version == '0.0.0':
            response_data["data"].update({
                "version": latest_version,
                "build": latest.get("build"),
                "release_date": latest.get("release_date"),
                "download_url": latest.get("download_url"),
                "size": latest.get("size"),
                "sha256": latest.get("sha256"),
                "changelog": latest.get("changelog", []),
                "required": latest.get("required", False)
            })

        return jsonify(response_data)
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/updates/download/<version>', methods=['GET'])
def download_update(version: str):
    """Скачать Terminal.exe определенной версии"""
    try:
        terminal_file = release_manager.get_release_file(version)

        if not terminal_file:
            return jsonify({
                "success": False,
                "error": f"Terminal v{version} not found"
            }), 404

        return send_file(
            terminal_file,
            as_attachment=True,
            download_name=f"ManekiTerminal-{version}.exe"
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/updates/changelog/<version>', methods=['GET'])
def get_changelog(version: str):
    """Получить changelog конкретной версии"""
    try:
        release = release_manager.get_release(version)

        if not release:
            return jsonify({
                "success": False,
                "error": "Release not found"
            }), 404

        return jsonify({
            "success": True,
            "data": {
                "version": version,
                "changelog": release.get('changelog', []),
                "release_date": release.get('release_date')
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/updates/versions', methods=['GET'])
def get_versions():
    """Получить список всех доступных версий Terminal"""
    try:
        versions = release_manager.list_versions()

        return jsonify({
            "success": True,
            "data": {
                "versions": versions,
                "count": len(versions)
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== SETUP ENDPOINTS ====================

@app.route('/api/setup/latest', methods=['GET'])
def get_latest_setup():
    """Получить информацию о последнем Setup"""
    try:
        setup_file = release_manager.get_latest_setup()

        if not setup_file:
            return jsonify({
                "success": False,
                "error": "No setup files available"
            }), 404

        # Извлечь версию из имени файла
        # ManekiTerminal-Setup-0.0.2.exe -> 0.0.2
        version = setup_file.stem.replace("ManekiTerminal-Setup-", "")

        return jsonify({
            "success": True,
            "data": {
                "version": version,
                "filename": setup_file.name,
                "size": setup_file.stat().st_size,
                "download_url": f"/api/setup/download/latest"
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/setup/download/latest', methods=['GET'])
def download_latest_setup():
    """Скачать последний Setup"""
    try:
        setup_file = release_manager.get_latest_setup()

        if not setup_file:
            return jsonify({
                "success": False,
                "error": "No setup files available"
            }), 404

        return send_file(
            setup_file,
            as_attachment=True,
            download_name=setup_file.name
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/setup/download/<version>', methods=['GET'])
def download_setup_by_version(version: str):
    """Скачать Setup конкретной версии"""
    try:
        setup_file = release_manager.get_setup_by_version(version)

        if not setup_file:
            return jsonify({
                "success": False,
                "error": f"Setup v{version} not found"
            }), 404

        return send_file(
            setup_file,
            as_attachment=True,
            download_name=setup_file.name
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ManekiTerminal Update Server",
        "version": "3.0",
        "mode": "separate_launcher"
    })


def _compare_versions(v1: str, v2: str) -> int:
    """Сравнить версии. Возвращает: 1 если v1 > v2, -1 если v1 < v2, 0 если равны"""
    parts1 = [int(x) for x in v1.split('.')]
    parts2 = [int(x) for x in v2.split('.')]

    for i in range(max(len(parts1), len(parts2))):
        p1 = parts1[i] if i < len(parts1) else 0
        p2 = parts2[i] if i < len(parts2) else 0

        if p1 > p2:
            return 1
        elif p1 < p2:
            return -1

    return 0


if __name__ == '__main__':
    print("=" * 70)
    print("🚀 ManekiTerminal Update Server v3.0")
    print("=" * 70)
    print(f"\n📂 Releases directory: {RELEASES_DIR.absolute()}")
    print("📝 Mode: Separate Launcher + Downloadable Terminal + Setup")

    # Проверить наличие релизов
    latest = release_manager.get_latest_release()
    if latest:
        print(f"\n✓ Latest Terminal version: {latest.get('version')}")

        # Показать структуру
        version = latest.get('version')
        version_dir = RELEASES_DIR / version
        if version_dir.exists():
            print(f"✓ Structure: releases/{version}/")
            print(f"             ├── ManekiTerminal.exe")
            print(f"             └── version.json")
    else:
        print("\n⚠️  No Terminal releases found")

    # Проверить Setup
    setup = release_manager.get_latest_setup()
    if setup:
        version = setup.stem.replace("ManekiTerminal-Setup-", "")
        size_mb = setup.stat().st_size / (1024 * 1024)
        print(f"\n✓ Latest Setup: {setup.name}")
        print(f"  Version: {version}")
        print(f"  Size: {size_mb:.1f} MB")
    else:
        print("\n⚠️  No Setup files found")
        print("\nExpected: releases/ManekiTerminal-Setup-X.X.X.exe")

    print("\n" + "=" * 70)
    print("📡 Starting server on http://0.0.0.0:5000")
    print("=" * 70)
    print("\nTerminal Endpoints:")
    print("  GET  /api/updates/latest")
    print("  GET  /api/updates/check?current=0.0.1")
    print("  GET  /api/updates/download/<version>")
    print("  GET  /api/updates/changelog/<version>")
    print("  GET  /api/updates/versions")
    print("\nSetup Endpoints:")
    print("  GET  /api/setup/latest")
    print("  GET  /api/setup/download/latest")
    print("  GET  /api/setup/download/<version>")
    print("\nOther:")
    print("  GET  /health")
    print("\n")

    app.run(host='0.0.0.0', port=5000, debug=True)