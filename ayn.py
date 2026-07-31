#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Iterable


SENSITIVE_PATTERNS = (
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
)

NE_DIR_PATTERNS = (
    ".git",
    ".git*",
    ".github",
    ".github*",
    ".gitlab",
    ".gitlab*",
    ".svn",
    ".svn*",
    ".hg",
    ".hg*",
    ".venv",
    ".venv*",
    "venv",
    "venv*",
    "env",
    "env*",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".nox",
    ".pytype",
    ".cache",
    ".ipynb_checkpoints",
    ".idea",
    ".idea*",
    ".vscode",
    ".vscode*",
    "dist",
    "build",
    "target",
    "out",
    "coverage",
    ".parcel-cache",
    ".next",
    ".nuxt",
    ".turbo",
    ".gradle",
    "pip-wheel-metadata",
    "*.egg-info",
    "*.dist-info",
    ".terraform",
    ".terraform*",
    "Cargo.lock"
)

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
    return any(
        fnmatch(name, pattern) or fnmatch(rel_path, pattern)
        for pattern in SENSITIVE_PATTERNS
    )


def is_ne_ignored(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    for part in parts:
        for pattern in NE_DIR_PATTERNS:
            if fnmatch(part, pattern):
                return True
    return False


def looks_like_virtualenv(dir_path: Path) -> bool:
    markers = (
        dir_path / "pyvenv.cfg",
        dir_path / "bin" / "activate",
        dir_path / "bin" / "python",
        dir_path / "Scripts" / "activate.bat",
        dir_path / "Scripts" / "python.exe",
        dir_path / "Lib" / "site-packages",
        dir_path / "site-packages",
    )
    return any(marker.exists() for marker in markers)


def should_skip_ne(root: Path, p: Path) -> bool:
    try:
        rel = p.relative_to(root).as_posix()
    except ValueError:
        rel = p.as_posix()

    if is_ne_ignored(rel):
        return True

    if p.is_dir() and not p.is_symlink() and looks_like_virtualenv(p):
        return True

    return False


def get_excluded_paths(root: Path, exclude_raw: list[str]) -> set[str]:
    """
    Собирает path_id() всех указанных в -ex файлов и папок,
    включая их содержимое рекурсивно.
    """
    excluded_ids: set[str] = set()
    for raw in exclude_raw:
        try:
            target = resolve_target(root, raw)
            excluded_ids.add(path_id(target))

            if target.is_dir() and not target.is_symlink():
                for child in target.rglob("*"):
                    excluded_ids.add(path_id(child))
        except FileNotFoundError:
            continue
    return excluded_ids


def is_text_file(p: Path, sample_size: int = 8192) -> bool:
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
        return True
    except UnicodeDecodeError:
        return False


def read_text_file(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[Не удалось прочитать файл: {e}]"


def all_files(root: Path, ignore_ids: set[str] | None = None, ne: bool = False) -> list[Path]:
    ignore_ids = ignore_ids or set()
    files: list[Path] = []

    for dirpath, dirs, filenames in os.walk(root, topdown=True, followlinks=False):
        current_dir = Path(dirpath)

        if path_id(current_dir) in ignore_ids:
            dirs[:] = []
            continue

        pruned_dirs: list[str] = []
        for d in dirs:
            child = current_dir / d
            if child.is_symlink():
                continue
            if path_id(child) in ignore_ids:
                continue
            if ne and should_skip_ne(root, child):
                continue
            pruned_dirs.append(d)
        dirs[:] = pruned_dirs

        for name in filenames:
            p = current_dir / name
            if path_id(p) in ignore_ids:
                continue
            if ne and should_skip_ne(root, p):
                continue
            files.append(p)

    files.sort(key=lambda x: x.relative_to(root).as_posix().lower())
    return files


def expand_targets(root: Path, targets: list[str], ignore_ids: set[str] | None = None, ne: bool = False) -> list[Path]:
    ignore_ids = ignore_ids or set()
    selected: dict[str, Path] = {}

    for raw in targets:
        if raw == ".":
            for p in all_files(root, ignore_ids=ignore_ids, ne=ne):
                selected[path_id(p)] = p
            continue

        p = resolve_target(root, raw)
        pid = path_id(p)

        if pid in ignore_ids:
            continue

        if ne and should_skip_ne(root, p):
            continue

        if p.is_dir() and not p.is_symlink():
            for child in all_files(p, ignore_ids=ignore_ids, ne=ne):
                selected[path_id(child)] = child
        elif p.is_file():
            selected[pid] = p

    result = list(selected.values())
    result.sort(key=lambda x: x.relative_to(root).as_posix().lower())
    return result


def build_tree(root: Path, ignore_ids: set[str] | None = None, ne: bool = False) -> str:
    ignore_ids = ignore_ids or set()
    lines = ["."]

    def walk(dir_path: Path, prefix: str = "") -> None:
        try:
            children = list(dir_path.iterdir())
        except PermissionError:
            return

        entries = []
        for child in children:
            if path_id(child) in ignore_ids:
                continue
            if ne and should_skip_ne(root, child):
                continue
            entries.append(child)

        entries.sort(key=lambda p: (not (p.is_dir() and not p.is_symlink()), p.name.lower()))

        for i, child in enumerate(entries):
            last = i == len(entries) - 1
            connector = "└── " if last else "├── "
            is_dir = child.is_dir() and not child.is_symlink()
            label = child.name + ("/" if is_dir else "")
            lines.append(prefix + connector + label)

            if is_dir:
                walk(child, prefix + ("    " if last else "│   "))

    walk(root)
    return "\n".join(lines)


def build_contents(root: Path, files: Iterable[Path], ns: bool = False, ne: bool = False) -> str:
    parts: list[str] = []

    for p in files:
        rel = p.relative_to(root).as_posix()

        if ne and should_skip_ne(root, p):
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
    p_cont.add_argument("-ex", nargs="+", dest="exclude", help="Исключить указанные файлы/директории из содержимого и структуры")
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
            excluded_ids = get_excluded_paths(root, args.exclude)
            ignore_ids.update(excluded_ids)
            files = all_files(root, ignore_ids=ignore_ids, ne=args.ne)
        elif args.paths:
            files = expand_targets(root, args.paths, ignore_ids=ignore_ids, ne=args.ne)
        else:
            files = all_files(root, ignore_ids=ignore_ids, ne=args.ne)

        unique_files: list[Path] = []
        seen: set[str] = set()
        for p in files:
            pid = path_id(p)
            if pid in ignore_ids or pid in seen:
                continue
            seen.add(pid)
            unique_files.append(p)

        tree_text = build_tree(root, ignore_ids=ignore_ids, ne=args.ne)
        content_text = build_contents(root, unique_files, ns=args.ns, ne=args.ne)

        final_text = tree_text + "\n\n" + content_text if content_text else tree_text + "\n"
        out.write_text(final_text, encoding="utf-8")
        print(str(out))
        return


if __name__ == "__main__":
    main()
