#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable


SENSITIVE_PATTERNS = [
    ".env",
    ".env.*",
    "*.env",
    "*.key",
    "*.pem",
    "*.crt",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "*.secret",
    "*secret*",
    "*credential*",
    "*.credentials",
    ".npmrc",
    ".git-credentials",
]

NE_DIR_NAMES = {
    ".git",
    ".github",
    ".gitlab",
    ".svn",
    ".hg",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".cache",
    ".idea",
    ".vscode",
    "dist",
    "build",
    "target",
    "out",
    ".next",
    ".nuxt",
    "coverage",
    ".parcel-cache",
}

BINARY_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".ico", ".tiff", ".tif",
    ".pdf", ".zip", ".rar", ".7z", ".gz", ".bz2", ".xz", ".tar",
    ".exe", ".dll", ".so", ".dylib", ".bin",
    ".mp3", ".wav", ".flac", ".ogg",
    ".mp4", ".mkv", ".avi", ".mov",
    ".class", ".jar", ".war", ".ear",
    ".wasm",
    ".psd", ".ai",
}


def now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def path_id(p: Path) -> str:
    return str(p.resolve(strict=False))


def is_inside_root(root: Path, p: Path) -> bool:
    try:
        p.resolve(strict=False).relative_to(root.resolve(strict=False))
        return True
    except ValueError:
        return False


def resolve_target(root: Path, raw: str) -> Path:
    raw_path = Path(raw)
    if raw_path.is_absolute():
        candidate = raw_path.resolve(strict=False)
    else:
        candidate = (root / raw_path).resolve(strict=False)

    if not candidate.exists():
        raise FileNotFoundError(f"Не найден путь: {raw}")

    if not is_inside_root(root, candidate):
        raise ValueError(f"Путь вне текущей директории: {raw}")

    return candidate


def is_sensitive(rel_path: str) -> bool:
    name = Path(rel_path).name
    for pattern in SENSITIVE_PATTERNS:
        if fnmatch(name, pattern) or fnmatch(rel_path, pattern):
            return True
    return False


def is_ne_ignored(rel_path: str) -> bool:
    """
    Возвращает True, если путь относится к служебной папке,
    которую нужно скрыть при флаге -ne.
    """
    parts = Path(rel_path).parts
    for part in parts:
        if part in NE_DIR_NAMES:
            return True
    return False


def is_text_file(p: Path, sample_size: int = 8192) -> bool:
    """
    Простейшая проверка: файл считается текстовым, если:
    - это не явно бинарный тип по расширению;
    - в первых байтах нет NUL;
    - sample декодируется как UTF-8.

    Если файл не UTF-8 текстовый — он будет пропущен.
    """
    if p.suffix.lower() in BINARY_EXTENSIONS:
        return False

    try:
        with p.open("rb") as f:
            chunk = f.read(sample_size)
    except Exception:
        return False

    if not chunk:
        return True

    if b"\x00" in chunk:
        return False

    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return False

    return True


def read_text_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[Не удалось прочитать файл: {e}]"


def all_files(root: Path, ne: bool = False) -> list[Path]:
    files: list[Path] = []

    for dirpath, dirs, filenames in os.walk(root):
        current_dir = Path(dirpath)

        if ne:
            pruned_dirs = []
            for d in dirs:
                child = current_dir / d
                rel = child.relative_to(root).as_posix()
                if not is_ne_ignored(rel):
                    pruned_dirs.append(d)
            dirs[:] = pruned_dirs

        for name in filenames:
            p = current_dir / name
            rel = p.relative_to(root).as_posix()

            if ne and is_ne_ignored(rel):
                continue

            files.append(p)

    files.sort(key=lambda x: x.relative_to(root).as_posix())
    return files


def expand_targets(root: Path, targets: list[str], ne: bool = False) -> list[Path]:
    selected: dict[str, Path] = {}

    for raw in targets:
        if raw == ".":
            for p in all_files(root, ne=ne):
                selected[path_id(p)] = p
            continue

        p = resolve_target(root, raw)
        rel = p.relative_to(root).as_posix()

        if ne and is_ne_ignored(rel):
            continue

        if p.is_dir():
            for child in all_files(p, ne=ne):
                child_rel = child.relative_to(root).as_posix()
                if ne and is_ne_ignored(child_rel):
                    continue
                selected[path_id(child)] = child
        elif p.is_file():
            selected[path_id(p)] = p
        else:
            raise FileNotFoundError(f"Не найден файл или директория: {raw}")

    result = list(selected.values())
    result.sort(key=lambda x: x.relative_to(root).as_posix())
    return result


def build_tree(root: Path, ignore_ids: set[str] | None = None, ne: bool = False) -> str:
    ignore_ids = ignore_ids or set()
    lines = ["."]

    def walk(dir_path: Path, prefix: str = "") -> None:
        entries = []

        for child in dir_path.iterdir():
            if path_id(child) in ignore_ids:
                continue

            rel = child.relative_to(root).as_posix()
            if ne and is_ne_ignored(rel):
                continue

            entries.append(child)

        entries.sort(key=lambda p: (not (p.is_dir() and not p.is_symlink()), p.name.lower()))

        for i, child in enumerate(entries):
            last = i == len(entries) - 1
            connector = "└── " if last else "├── "
            label = child.name + ("/" if child.is_dir() and not child.is_symlink() else "")
            lines.append(prefix + connector + label)

            if child.is_dir() and not child.is_symlink():
                walk(child, prefix + ("    " if last else "│   "))

    walk(root)
    return "\n".join(lines)


def build_contents(root: Path, files: Iterable[Path], ns: bool = False, ne: bool = False) -> str:
    parts: list[str] = []

    for p in files:
        rel = p.relative_to(root).as_posix()

        if ne and is_ne_ignored(rel):
            continue

        if ns and is_sensitive(rel):
            content = "[Содержимое скрыто по -ns]"
        elif not is_text_file(p):
            continue
        else:
            content = read_text_file(p)

        parts.append(f"{rel}\n\n{content}\n\n")

    return "".join(parts)


def make_output_path(root: Path, command: str, custom: str | None = None) -> Path:
    if custom:
        p = Path(custom)
        return p if p.is_absolute() else (root / p)
    return root / f"ayn_{command}_{now_stamp()}.txt"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ayn",
        description="Сохранение структуры проекта и содержимого файлов"
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_struc = sub.add_parser("struc", help="Сохраняет только структуру проекта")
    p_struc.add_argument("-ne", action="store_true", help="Скрыть служебные папки (.git, .venv, node_modules и т.п.)")
    p_struc.add_argument("-o", "--output", help="Имя выходного файла")

    p_cont = sub.add_parser("cont", help="Сохраняет структуру и содержимое файлов")
    p_cont.add_argument("paths", nargs="*", help="Файлы или директории внутри текущей директории")
    p_cont.add_argument("-ns", action="store_true", help="Не включать чувствительные файлы (.env и т.п.)")
    p_cont.add_argument("-ne", action="store_true", help="Скрыть служебные папки (.git, .venv, node_modules и т.п.)")
    p_cont.add_argument("-ex", nargs="+", dest="exclude", help="Исключить указанные файлы/директории из содержимого")
    p_cont.add_argument("-o", "--output", help="Имя выходного файла")

    args = parser.parse_args()
    root = Path.cwd().resolve()

    if args.cmd == "struc":
        out = make_output_path(root, "struc", args.output)
        tree_text = build_tree(root, ignore_ids={path_id(out)}, ne=args.ne)
        out.write_text(tree_text + "\n", encoding="utf-8")
        print(str(out))
        return

    if args.cmd == "cont":
        if args.exclude and args.paths:
            parser.error("-ex нельзя использовать вместе с позиционными путями")

        out = make_output_path(root, "cont", args.output)
        ignore_ids = {path_id(out)}

        if args.exclude:
            excluded = expand_targets(root, args.exclude, ne=args.ne)
            excluded_ids = {path_id(p) for p in excluded}
            files = [p for p in all_files(root, ne=args.ne) if path_id(p) not in excluded_ids]
        elif args.paths:
            files = expand_targets(root, args.paths, ne=args.ne)
        else:
            files = all_files(root, ne=args.ne)

        # Доп. фильтрация
        filtered: list[Path] = []
        seen: set[str] = set()
        for p in files:
            rel = p.relative_to(root).as_posix()

            if args.ne and is_ne_ignored(rel):
                continue

            if path_id(p) in seen:
                continue
            seen.add(path_id(p))

            filtered.append(p)

        tree_text = build_tree(root, ignore_ids=ignore_ids, ne=args.ne)
        content_text = build_contents(root, filtered, ns=args.ns, ne=args.ne)

        final_text = tree_text + "\n\n" + content_text if content_text else tree_text + "\n"
        out.write_text(final_text, encoding="utf-8")
        print(str(out))
        return


if __name__ == "__main__":
    main()
