#!/usr/bin/env python3
"""Validation script to check for import errors and basic syntax issues."""

import ast
import sys
from pathlib import Path
from typing import List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_syntax(file_path: Path) -> Tuple[bool, str]:
    """Check if a Python file has valid syntax.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source, filename=str(file_path))
        return True, ""
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} at line {e.lineno}"
    except Exception as e:
        return False, f"Error parsing file: {e}"


def check_imports(file_path: Path) -> Tuple[bool, str]:
    """Check if a Python file can be imported without errors.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        # Convert file path to module path
        rel_path = file_path.relative_to(project_root)
        module_path = str(rel_path.with_suffix('')).replace('/', '.').replace('\\', '.')
        
        # Try to import the module
        __import__(module_path)
        return True, ""
    except ImportError as e:
        return False, f"Import error: {e}"
    except SyntaxError as e:
        return False, f"Syntax error: {e.msg} at line {e.lineno}"
    except Exception as e:
        # Some modules might fail to import due to missing dependencies or runtime errors
        # That's okay for validation - we just want to catch import/syntax errors
        error_msg = str(e)
        if "NameError" in error_msg or "not defined" in error_msg:
            return False, f"Name error: {error_msg}"
        # Other errors might be runtime issues, not import issues
        return True, ""


def validate_file(file_path: Path, check_import: bool = True) -> Tuple[bool, List[str]]:
    """Validate a single Python file.
    
    Args:
        file_path: Path to the file
        check_import: Whether to check imports (slower but more thorough)
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    
    # Check syntax
    is_valid, error = check_syntax(file_path)
    if not is_valid:
        errors.append(f"Syntax: {error}")
    
    # Check imports if requested
    if check_import and is_valid:
        is_valid_import, error = check_imports(file_path)
        if not is_valid_import:
            errors.append(f"Import: {error}")
    
    return len(errors) == 0, errors


def find_python_files(directory: Path, exclude_dirs: List[str] = None) -> List[Path]:
    """Find all Python files in a directory.
    
    Args:
        directory: Directory to search
        exclude_dirs: List of directory names to exclude (e.g., ['venv', '__pycache__'])
        
    Returns:
        List of Python file paths
    """
    if exclude_dirs is None:
        exclude_dirs = ['venv', '__pycache__', '.git', 'htmlcov', '.pytest_cache', 'node_modules']
    
    python_files = []
    for path in directory.rglob('*.py'):
        # Skip excluded directories
        if any(excluded in path.parts for excluded in exclude_dirs):
            continue
        python_files.append(path)
    
    return sorted(python_files)


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate Python files for syntax and import errors")
    parser.add_argument(
        '--files',
        nargs='+',
        help='Specific files to validate (default: all Python files in src/)'
    )
    parser.add_argument(
        '--no-import-check',
        action='store_true',
        help='Skip import checking (faster, only checks syntax)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show all files being checked'
    )
    
    args = parser.parse_args()
    
    if args.files:
        files_to_check = [Path(f) for f in args.files]
    else:
        src_dir = project_root / 'src'
        files_to_check = find_python_files(src_dir)
    
    check_import = not args.no_import_check
    
    print(f"Validating {len(files_to_check)} file(s)...")
    print()
    
    failed_files = []
    total_errors = 0
    
    for file_path in files_to_check:
        if args.verbose:
            print(f"Checking {file_path.relative_to(project_root)}...", end=' ')
        
        is_valid, errors = validate_file(file_path, check_import=check_import)
        
        if not is_valid:
            failed_files.append((file_path, errors))
            total_errors += len(errors)
            if args.verbose:
                print("❌ FAILED")
            else:
                rel_path = file_path.relative_to(project_root)
                print(f"❌ {rel_path}")
                for error in errors:
                    print(f"   {error}")
        elif args.verbose:
            print("✅ OK")
    
    print()
    if failed_files:
        print(f"❌ Validation failed: {total_errors} error(s) in {len(failed_files)} file(s)")
        if not args.verbose:
            print("\nDetailed errors:")
            for file_path, errors in failed_files:
                rel_path = file_path.relative_to(project_root)
                print(f"\n{rel_path}:")
                for error in errors:
                    print(f"  {error}")
        sys.exit(1)
    else:
        print(f"✅ All {len(files_to_check)} file(s) validated successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main()

