#!/usr/bin/env -S uv run --script
import sys

from .. import odb


def main(args):
    print(odb.get_hash_key(Path(args[0])))


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)
