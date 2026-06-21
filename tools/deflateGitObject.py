#!/usr/bin/env -S uv run
import sys
import zlib

def main(args):
    if '-h' in args or '--help' in args:
        print_usage()
        return

    with open(args[0], 'rb') as f:
        b = f.read()
    c = zlib.decompress(b)
    sys.stdout.buffer.write(c)


def print_usage():
    print("jit cat-file [-options] <object-filepath>")
    print("jit cat-file [-options] <object-hash>")
    print("options:")
    print("\t-p: pretty print")
    print("\t-t: object type")
    print("\t-r: raw bytes dump")


def print_tree(c):
    i = 0

    # header
    header = bytearray()
    while c[i] != 0:
        header.append(c[i])
        i+=1
    i+=1
    
    while i < len(c) - 3:
        # name & mode
        name_buf = bytearray()
        while c[i] != 0:
            name_buf.append(c[i])
            i+=1
        i+=1
        mode, name = name_buf.split(b' ')
        odb_type, permissions = from_mode(mode)

        # hash
        start = i
        hash_buf = bytearray()
        for i in range(start, start + 20):
            hash_buf.append(c[i])
        print(f'{permissions:06} {odb_type} {hash_buf.hex()}\t{name.decode()}')


def print_blob(c):
    i = c.find(b'\00')
    print(c[i:].decode(), end='')


def print_commit(c):
    i = c.find(b'\00')
    print(c[i:].decode(), end='')


def from_mode(mode):
    if mode == b'40000':
        return 'tree', '040000'
    return 'blob', f'{mode[-6:].decode()}'


if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)

