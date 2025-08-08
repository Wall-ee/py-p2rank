#!/usr/bin/env python3
"""
Test script for P2Rank Python Distribution

This script tests the basic functionality of the Python distribution package.
"""

import sys
import os
from pathlib import Path
import traceback

def test_imports():
    """Test if P2Rank modules can be imported"""
    print("Testing imports...")
    
    try:
        # Add current directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Test config loader
        from config_loader import ConfigLoader
        print("✓ ConfigLoader imported successfully")
        
        # Test P2Rank modules (if available)
        try:
            from p2rank.utils.math_utils import MathUtils
            print("✓ MathUtils imported successfully")
        except ImportError as e:
            print(f"⚠ P2Rank modules not available: {e}")
            print("  This is expected if running in distro_py directory without full p2rank package")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False


def test_config_loader():
    """Test configuration loading"""
    print("\nTesting configuration loader...")
    
    try:
        from config_loader import ConfigLoader
        
        loader = ConfigLoader()
        
        # Test listing configurations
        configs = loader.list_configs()
        print(f"✓ Found {len(configs)} configuration files: {configs}")
        
        # Test loading default config
        if 'default' in configs:
            config = loader.load_config('default')
            print(f"✓ Default config loaded successfully")
            print(f"  Model: {config.get('model', 'unknown')}")
            print(f"  Features: {config.get('features', [])}")
            print(f"  Threads: {config.get('threads', 'unknown')}")
        else:
            print("⚠ Default configuration not found")
        
        # Test loading AlphaFold config (if available)
        if 'alphafold' in configs:
            config = loader.load_config('alphafold')
            print(f"✓ AlphaFold config loaded successfully")
            print(f"  Model: {config.get('model', 'unknown')}")
            print(f"  Features: {config.get('features', [])}")
        
        return True
        
    except Exception as e:
        print(f"✗ Config loader test failed: {e}")
        traceback.print_exc()
        return False


def test_dependencies():
    """Test if required dependencies are available"""
    print("\nTesting dependencies...")
    
    required_packages = [
        ('numpy', 'NumPy'),
        ('scipy', 'SciPy'),
        ('sklearn', 'scikit-learn'),
        ('pandas', 'pandas'),
        ('yaml', 'PyYAML'),
    ]
    
    missing_packages = []
    
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"✓ {package_name} available")
        except ImportError:
            print(f"✗ {package_name} missing")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\nMissing packages: {missing_packages}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    return True


def test_launcher_scripts():
    """Test if launcher scripts exist and are executable"""
    print("\nTesting launcher scripts...")
    
    script_dir = Path(__file__).parent
    
    # Check main launchers
    scripts = [
        ('p2rank_py', 'Linux/macOS launcher'),
        ('p2rank_py.bat', 'Windows launcher'),
        ('p2rank_py.py', 'Python launcher'),
    ]
    
    all_good = True
    
    for script_name, description in scripts:
        script_path = script_dir / script_name
        
        if script_path.exists():
            print(f"✓ {description} exists")
            
            # Check if executable (Unix-like systems)
            if script_name != 'p2rank_py.bat' and hasattr(os, 'access'):
                if os.access(script_path, os.X_OK):
                    print(f"  ✓ {script_name} is executable")
                else:
                    print(f"  ⚠ {script_name} is not executable")
                    print(f"    Run: chmod +x {script_name}")
        else:
            print(f"✗ {description} missing: {script_path}")
            all_good = False
    
    return all_good


def test_data_availability():
    """Test if test data is available"""
    print("\nTesting test data availability...")
    
    script_dir = Path(__file__).parent
    test_data_dir = script_dir / "test_data"
    
    if test_data_dir.exists():
        print("✓ Test data directory exists")
        
        # Count some files
        pdb_files = list(test_data_dir.glob("*.pdb"))
        ds_files = list(test_data_dir.glob("*.ds"))
        
        print(f"  Found {len(pdb_files)} PDB files")
        print(f"  Found {len(ds_files)} dataset files")
        
        if pdb_files:
            print(f"  Example PDB: {pdb_files[0].name}")
        
        return True
    else:
        print("⚠ Test data directory not found")
        print("  This is expected if test_data symlink is not created")
        return False


def test_file_structure():
    """Test basic file structure"""
    print("\nTesting file structure...")
    
    script_dir = Path(__file__).parent
    
    expected_files = [
        ('README.md', 'Documentation'),
        ('requirements.txt', 'Dependencies'),
        ('LICENSE.txt', 'License'),
        ('config/default.yaml', 'Default configuration'),
    ]
    
    all_good = True
    
    for file_path, description in expected_files:
        full_path = script_dir / file_path
        
        if full_path.exists():
            print(f"✓ {description}: {file_path}")
        else:
            print(f"✗ {description} missing: {file_path}")
            all_good = False
    
    return all_good


def main():
    """Run all tests"""
    print("P2Rank Python Distribution Test")
    print("=" * 40)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Dependencies", test_dependencies),
        ("Imports", test_imports),
        ("Configuration Loader", test_config_loader),
        ("Launcher Scripts", test_launcher_scripts),
        ("Test Data", test_data_availability),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        icon = "✓" if result else "✗"
        print(f"{icon} {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The distribution appears to be working correctly.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 