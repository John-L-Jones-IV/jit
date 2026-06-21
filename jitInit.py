#!/usr/bin/env -S uv run
import os
import sys
from pathlib import Path


def main(args):
    if Path('.jit/').exists():
        print('Did Nothing - a Jit repository already exists here.')
        return 1

    os.mkdir('.jit/')
    os.mkdir('.jit/objects/')
    os.mkdir('.jit/objects/pack')
    os.mkdir('.jit/objects/info')
    os.mkdir('.jit/refs/')
    os.mkdir('.jit/refs/heads/')
    os.mkdir('.jit/refs/tags/')
    os.mkdir('.jit/branches')
    Path('.jit/description').touch()
    Path('.jit/HEAD').touch()
    with open('.jit/HEAD', 'w', encoding='utf-8') as f:
        f.write('ref: refs/heads/master\n')

    print(f'Initialized empty Jit repository in {os.getcwd()}/.jit/')
    return 0


if __name__ == '__main__':
    args = sys.argv[:2]
    main(args)
    
