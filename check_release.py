#!/usr/bin/env python3
"""
Проверка целостности releases
Проверяет что размеры и хеши в version.json совпадают с реальными файлами
"""
import json
import hashlib
from pathlib import Path


def calculate_sha256(filepath: Path) -> str:
    """Вычислить SHA256"""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def format_size(size: int) -> str:
    """Форматировать размер"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def check_releases():
    """Проверить все releases"""
    releases_dir = Path("releases")

    if not releases_dir.exists():
        print("❌ Папка releases/ не найдена!")
        print(f"   Ожидается: {releases_dir.absolute()}")
        return False

    print("=" * 80)
    print("🔍 Проверка целостности releases")
    print("=" * 80)

    # Найти все версии
    versions = []
    for version_dir in releases_dir.iterdir():
        if version_dir.is_dir() and (version_dir / "version.json").exists():
            versions.append(version_dir)

    if not versions:
        print("\n⚠️  Не найдено ни одного релиза")
        print("\nОжидаемая структура:")
        print("releases/")
        print("├── 0.0.2/")
        print("│   ├── ManekiTerminal.exe")
        print("│   └── version.json")
        print("└── latest.json")
        return False

    # Сортировать версии
    versions.sort(key=lambda p: [int(x) for x in p.name.split('.')])

    all_ok = True

    for version_dir in versions:
        version = version_dir.name
        version_json = version_dir / "version.json"
        terminal_exe = version_dir / "ManekiTerminal.exe"

        print(f"\n📦 Проверка версии {version}")
        print("-" * 80)

        # Проверить наличие файлов
        if not terminal_exe.exists():
            print(f"❌ Файл не найден: {terminal_exe}")
            all_ok = False
            continue

        # Прочитать version.json
        try:
            with open(version_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Ошибка чтения version.json: {e}")
            all_ok = False
            continue

        # Проверить размер
        actual_size = terminal_exe.stat().st_size
        expected_size = data.get('size', 0)

        size_match = actual_size == expected_size
        size_icon = "✓" if size_match else "✗"

        print(f"\n📏 Размер файла:")
        print(f"  {size_icon} Ожидается: {format_size(expected_size)} ({expected_size:,} bytes)")
        print(f"  {size_icon} Реальный:  {format_size(actual_size)} ({actual_size:,} bytes)")

        if not size_match:
            diff = abs(actual_size - expected_size)
            diff_percent = (diff / expected_size) * 100 if expected_size > 0 else 0
            print(f"  ❌ Разница: {format_size(diff)} ({diff_percent:.2f}%)")
            all_ok = False

        # Проверить хеш
        print(f"\n🔐 SHA256 хеш:")
        print(f"  Вычисление...")

        actual_hash = calculate_sha256(terminal_exe)
        expected_hash = data.get('sha256', '')

        hash_match = actual_hash == expected_hash
        hash_icon = "✓" if hash_match else "✗"

        print(f"  {hash_icon} Ожидается: {expected_hash}")
        print(f"  {hash_icon} Реальный:  {actual_hash}")

        if not hash_match:
            print(f"  ❌ Хеши не совпадают!")
            all_ok = False

        # Дополнительная информация
        print(f"\n📋 Информация о релизе:")
        print(f"  Версия:       {data.get('version')}")
        print(f"  Build:        {data.get('build')}")
        print(f"  Дата релиза:  {data.get('release_date')}")
        print(f"  Download URL: {data.get('download_url')}")

        changelog = data.get('changelog', [])
        if changelog:
            print(f"\n  Changelog:")
            for item in changelog:
                print(f"    • {item}")

        if size_match and hash_match:
            print(f"\n✅ Версия {version} проверена - всё в порядке!")
        else:
            print(f"\n❌ Версия {version} содержит ошибки!")

    # Проверить latest.json
    print("\n" + "=" * 80)
    print("📌 Проверка latest.json")
    print("-" * 80)

    latest_json = releases_dir / "latest.json"
    if latest_json.exists():
        try:
            with open(latest_json, 'r', encoding='utf-8') as f:
                latest_data = json.load(f)

            latest_version = latest_data.get('version')
            print(f"✓ Последняя версия: {latest_version}")

            # Проверить что папка этой версии существует
            latest_dir = releases_dir / latest_version
            if latest_dir.exists():
                print(f"✓ Папка {latest_version}/ существует")
            else:
                print(f"❌ Папка {latest_version}/ не найдена!")
                all_ok = False
        except Exception as e:
            print(f"❌ Ошибка чтения latest.json: {e}")
            all_ok = False
    else:
        print(f"❌ Файл latest.json не найден!")
        all_ok = False

    # Итоги
    print("\n" + "=" * 80)
    if all_ok:
        print("✅ ВСЕ РЕЛИЗЫ ПРОВЕРЕНЫ - ОШИБОК НЕТ!")
    else:
        print("❌ ОБНАРУЖЕНЫ ОШИБКИ!")
        print("\nРешение:")
        print("1. Пересоберите Terminal: python build_nuitka.py <version>")
        print("2. Перепубликуйте: python publish_release.py <version>")
    print("=" * 80)

    return all_ok


def fix_version_json(version: str):
    """Исправить version.json для версии"""
    releases_dir = Path("releases")
    version_dir = releases_dir / version
    version_json = version_dir / "version.json"
    terminal_exe = version_dir / "ManekiTerminal.exe"

    if not terminal_exe.exists():
        print(f"❌ {terminal_exe} не найден!")
        return False

    if not version_json.exists():
        print(f"❌ {version_json} не найден!")
        return False

    print(f"🔧 Исправление version.json для версии {version}...")

    # Прочитать текущий
    with open(version_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Вычислить правильные значения
    actual_size = terminal_exe.stat().st_size
    actual_hash = calculate_sha256(terminal_exe)

    print(f"  Старый размер: {data.get('size')}")
    print(f"  Новый размер:  {actual_size}")
    print(f"  Старый хеш:    {data.get('sha256')}")
    print(f"  Новый хеш:     {actual_hash}")

    # Обновить
    data['size'] = actual_size
    data['sha256'] = actual_hash

    # Записать
    with open(version_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ version.json обновлен!")

    # Обновить latest.json если это последняя версия
    latest_json = releases_dir / "latest.json"
    if latest_json.exists():
        with open(latest_json, 'r', encoding='utf-8') as f:
            latest_data = json.load(f)

        if latest_data.get('version') == version:
            print(f"  Обновление latest.json...")
            with open(latest_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ latest.json обновлен!")

    return True


def main():
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "fix" and len(sys.argv) > 2:
            version = sys.argv[2]
            success = fix_version_json(version)
            sys.exit(0 if success else 1)
        else:
            print("Usage:")
            print("  python check_releases.py           # Проверить все релизы")
            print("  python check_releases.py fix 0.0.2 # Исправить version.json")
            sys.exit(1)

    success = check_releases()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()