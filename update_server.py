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
        """Получить последний релиз"""
        manifest_file = self.releases_dir / "latest.json"

        if not manifest_file.exists():
            return None

        with open(manifest_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_release(self, version: str) -> dict:
        """Получить конкретный релиз"""
        manifest_file = self.releases_dir / f"{version}.json"

        if not manifest_file.exists():
            return None

        with open(manifest_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_release_file(self, version: str) -> Path:
        """Получить файл релиза"""
        release_file = self.releases_dir / f"ManekiTerminal-{version}.exe"

        if not release_file.exists():
            return None

        return release_file


release_manager = ReleaseManager(RELEASES_DIR)


@app.route('/api/updates/latest', methods=['GET'])
def get_latest():
    """Получить последнюю версию"""
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
    """Проверить наличие обновлений"""
    try:
        current_version = request.args.get('current', '1.0.0')

        latest = release_manager.get_latest_release()

        if not latest:
            return jsonify({
                "success": False,
                "error": "No releases available"
            }), 404

        latest_version = latest['version']

        # Сравнить версии
        update_available = _compare_versions(latest_version, current_version) > 0

        return jsonify({
            "success": True,
            "data": {
                "update_available": update_available,
                "latest_version": latest_version,
                "current_version": current_version,
                **(latest if update_available else {})
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/updates/download/<version>', methods=['GET'])
def download_update(version: str):
    """Скачать обновление"""
    try:
        release_file = release_manager.get_release_file(version)

        if not release_file:
            return jsonify({
                "success": False,
                "error": "Release not found"
            }), 404

        return send_file(
            release_file,
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
    """Получить changelog"""
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
                "changelog": release.get('changelog', [])
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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
    app.run(host='0.0.0.0', port=5000, debug=True)