#!/usr/bin/env -S uv run --script
"""
JIT - A Git-like version control system
Main entry point and command dispatcher
"""
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent

def main():
    """Main entry point for jit commands"""
    
    # Check if any command was provided
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    # Get the command and remaining arguments
    command = sys.argv[1].lower()
    args = sys.argv[2:]
    
    # Map commands to their corresponding modules
    commands = {
        'init': 'jitInit',
        'add': 'jitAdd',
        'commit': 'jitCommit',
        'status': 'jitStatus'
    }
    
    # Validate command
    if command not in commands:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)
    
    # Get the module name
    module_name = commands[command]
    
    try:
        # Dynamically import the module
        module = __import__(module_name)
        
        # Check if module has a main function
        if not hasattr(module, 'main'):
            print(f"Error: {module_name}.py is missing a main() function")
            sys.exit(1)
        
        # Call the module's main function with remaining arguments
        exit_code = module.main(args)
        
        # Exit with the returned code (0 for success, non-zero for error)
        sys.exit(exit_code if exit_code is not None else 0)
        
    except ImportError as e:
        print(f"Error: Could not import {module_name}.py")
        print(f"Details: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error: Command '{command}' failed")
        print(f"Details: {e}")
        sys.exit(1)


def print_usage():
    """Print usage information"""
    print("Usage: jit <command> [<args>]")
    print()
    print("Available commands:")
    print("  init       Initialize a new jit repository")
    print("  add        Add file contents to the staging area")
    print("  commit     Record changes to the repository")
    print("  status     Show the working tree status")


if __name__ == "__main__":
    main()
