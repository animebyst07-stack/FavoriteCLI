"""
favorite/skills/fs_tools.py
Скилл: операции с файлами в WORKDIR (read, write, list, append).
"""
from pathlib import Path


def fs_op(op: str, rel_path: str, content: str, workdir: str) -> str:
    """
    op: read | write | append | list
    rel_path: путь относительно workdir
    content: для write/append
    Возвращает строку с результатом.
    """
    base = Path(workdir).resolve()
    op = op.lower().strip()

    if op == "list":
        try:
            target = (base / rel_path).resolve() if rel_path else base
            if not str(target).startswith(str(base)):
                return "Ошибка: путь вне рабочей директории."
            entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
            lines = [f"{'F' if e.is_file() else 'D'}  {e.name}" for e in entries]
            return "\n".join(lines) if lines else "(пусто)"
        except Exception as e:
            return f"list error: {e}"

    if not rel_path:
        return "Ошибка: не указан путь."

    target = (base / rel_path).resolve()
    if not str(target).startswith(str(base)):
        return "Ошибка: путь вне рабочей директории."

    if op == "read":
        try:
            return target.read_text(encoding="utf-8")[:6000]
        except Exception as e:
            return f"read error: {e}"

    if op == "write":
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Записано: {rel_path}"
        except Exception as e:
            return f"write error: {e}"

    if op == "append":
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("a", encoding="utf-8") as f:
                f.write(content)
            return f"Дописано: {rel_path}"
        except Exception as e:
            return f"append error: {e}"

    return f"Неизвестная операция: {op}"
