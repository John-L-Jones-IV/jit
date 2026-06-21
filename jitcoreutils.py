#!/usr/bin/env -S uv run
import os
import stat
from pathlib import Path
from typing import Optional


def get_jit_repo_dir() -> Optional[Path]:
    cwd = Path(os.getcwd())
    if (cwd / Path('.jit')).is_dir():
        return cwd
    for parent in cwd.parents:
        if parent == Path.home().parent:
            return None
        if (Path(parent) / Path('.jit')).is_dir():
            return Path(parent)
    return None


def git_file_mode(mode:int ) -> str:
    if mode & stat.S_IXUSR:
        return '100755'
    return '100644'

