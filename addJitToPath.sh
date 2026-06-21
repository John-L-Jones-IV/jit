#!/usr/bin/env bash
parent_path=$(cd "$(dirname "${BASH_SOURCE[0]}")" ; pwd - P)
cd "$parent_path"
script_location="bin"
jit_location="${PWD}/${script_location}"
echo $jit_location
export PATH="$PATH:$jit_location"
echo ${PWD}
PYTHONPATH="${PYTHONPATH}:${PWD}"
