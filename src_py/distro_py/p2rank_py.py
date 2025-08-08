#!/usr/bin/env python3
"""
P2Rank Python Distribution Launcher

Cross-platform Python launcher for P2Rank Python version.
This script sets up the environment and launches the main P2Rank program.
"""

import sys
import os
from pathlib import Path
import logging


def setup_environment():
    """Set up the Python environment for P2Rank"""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    
    # Add P2Rank Python package to the path
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    # Set environment variables
    os.environ['P2RANK_INSTALL_DIR'] = str(script_dir)
    
    return script_dir


def check_dependencies():
    """Check if required dependencies are available"""
    required_packages = [
        ('numpy', 'NumPy'),
        ('scipy', 'SciPy'),
        ('sklearn', 'scikit-learn'),
        ('pandas', 'pandas'),
    ]
    
    missing_packages = []
    
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("Error: Required Python packages not found:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install missing dependencies:")
        print("  pip install -r requirements.txt")
        print("or:")
        print("  pip install numpy scipy scikit-learn pandas biopython")
        return False
    
    return True


def setup_logging():
    """Set up basic logging configuration"""
    # Check if verbose mode is requested
    verbose = any(arg in ['-v', '--verbose', '-vv'] for arg in sys.argv)
    
    if verbose:
        level = logging.DEBUG
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    else:
        level = logging.INFO
        format_str = '%(levelname)s: %(message)s'
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[logging.StreamHandler(sys.stdout)]
    )


def check_python_version():
    """Check if Python version is supported"""
    if sys.version_info < (3, 8):
        print(f"Error: Python 3.8+ is required. Found: Python {sys.version_info.major}.{sys.version_info.minor}")
        print("Please upgrade Python to version 3.8 or newer.")
        return False
    
    return True


def main():
    """Main launcher function"""
    # Check Python version first
    if not check_python_version():
        sys.exit(1)
    
    # Set up environment
    script_dir = setup_environment()
    
    # Set up logging
    setup_logging()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Show startup info in verbose mode
    if any(arg in ['-v', '--verbose'] for arg in sys.argv):
        print("P2Rank Python Distribution")
        print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
        print(f"Install directory: {script_dir}")
        print(f"Python executable: {sys.executable}")
        print("")
    
    try:
        # Import and run the main P2Rank program
        from p2rank.program.main import main as p2rank_main
        
        # Remove this script from sys.argv to avoid confusing the main program
        if len(sys.argv) > 0 and sys.argv[0].endswith('p2rank_py.py'):
            sys.argv = sys.argv[1:]
        
        # Run P2Rank
        success = p2rank_main()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except ImportError as e:
        print(f"Error: Could not import P2Rank modules: {e}")
        print("Please ensure that P2Rank Python package is properly installed.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if any(arg in ['-v', '--verbose', '-vv'] for arg in sys.argv):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 