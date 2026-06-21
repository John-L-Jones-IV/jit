#!/usr/bin/env -s uv run
import re
from pathlib import Path


def get_jit_config(jit_repo_dir) -> dict[str, dict[str, str]]:
    home = Path.home()
    config_places = [home/Path('.jitconfig'),
                     home/Path('.config/jit/config'),
                     jit_repo_dir/Path('.jit/config'),]
    config: dict[str, dict[str, str]] = {}
    section_pattern = re.compile(r'\[[a-z]*\]')
    key_pattern = re.compile(r'=')
    for p in config_places:
        if p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                buf = f.read()
            for line in buf.split('\n'):
                section_match = section_pattern.search(line) 
                if section_match:
                    section = section_match[0][1:-1]
                    if config.get(section) is None:
                        config[section] = dict()
                    continue
                key_match = key_pattern.search(line)
                if key_match:
                    key = line.split('=')[0].strip()
                    value = line.split('=')[1].strip()
                    config[section][key] = value
                
    return config

