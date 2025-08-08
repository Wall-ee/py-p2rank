#!/usr/bin/env python3
"""
Test P2Rank Configuration System

Test the converted configuration system to ensure it works correctly.
"""

import sys
import json
from pathlib import Path
import logging

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_py import ConfigLoader, P2RankConfig, ConfigValidator

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_config_loading():
    """Test loading all configuration files"""
    print("🧪 Testing Configuration System")
    print("="*60)
    
    config_dir = Path("config_py/core")
    loader = ConfigLoader(config_dir)
    validator = ConfigValidator()
    
    # Test configs to load
    test_configs = [
        "base",
        "test_default", 
        "test_alphafold",
        "test_conservation",
        "train_default",
        "train_conservation"
    ]
    
    results = {}
    
    for config_name in test_configs:
        print(f"\n📋 Testing config: {config_name}")
        
        try:
            # Load configuration
            config = loader.load_config(config_name)
            
            # Validate configuration
            errors = validator.validate_config(config)
            warnings = validator.get_warnings(config)
            
            # Test results
            result = {
                "status": "SUCCESS" if not errors else "FAILED",
                "errors": errors,
                "warnings": warnings,
                "model": config.model,
                "features": config.features,
                "classifier": config.classifier,
                "rf_trees": config.rf_trees
            }
            
            if not errors:
                print(f"   ✅ SUCCESS")
                print(f"      Model: {config.model}")
                print(f"      Features: {len(config.features)} ({', '.join(config.features)})")
                print(f"      Classifier: {config.classifier} ({config.rf_trees} trees)")
                
                if warnings:
                    print(f"      ⚠️  Warnings: {len(warnings)}")
                    for warning in warnings:
                        print(f"         • {warning}")
            else:
                print(f"   ❌ FAILED")
                for error in errors:
                    print(f"      • {error}")
            
            results[config_name] = result
            
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results[config_name] = {
                "status": "ERROR",
                "error": str(e)
            }
    
    return results

def test_config_inheritance():
    """Test configuration inheritance"""
    print(f"\n{'='*60}")
    print("🔗 Testing Configuration Inheritance")
    print("="*60)
    
    config_dir = Path("config_py/core")
    loader = ConfigLoader(config_dir)
    
    try:
        # Load base config
        base_config = loader.load_config("base")
        print(f"✅ Base config loaded - Features: {len(base_config.features)}")
        
        # Load derived config
        test_config = loader.load_config("test_default")
        print(f"✅ Test config loaded - Features: {len(test_config.features)}")
        
        # Test inheritance
        print(f"\n📊 Inheritance Test:")
        print(f"   Base visualizations: {base_config.visualizations}")
        print(f"   Test visualizations: {test_config.visualizations}")
        print(f"   Base rf_batch_prediction: {base_config.rf_batch_prediction}")
        print(f"   Test rf_batch_prediction: {test_config.rf_batch_prediction}")
        
        # Verify inheritance worked
        assert test_config.visualizations == False, "Inheritance override failed"
        assert test_config.rf_batch_prediction == True, "Inheritance override failed"
        assert test_config.features == base_config.features, "Feature inheritance failed"
        
        print(f"✅ Inheritance working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Inheritance test failed: {e}")
        return False

def test_specialized_features():
    """Test specialized model configurations"""
    print(f"\n{'='*60}")
    print("🔬 Testing Specialized Configurations")
    print("="*60)
    
    config_dir = Path("config_py/core")
    loader = ConfigLoader(config_dir)
    
    try:
        # Test AlphaFold config (no bfactor)
        alphafold_config = loader.load_config("test_alphafold")
        print(f"✅ AlphaFold config:")
        print(f"   Model: {alphafold_config.model}")
        print(f"   Features: {alphafold_config.features}")
        assert "bfactor" not in alphafold_config.features, "AlphaFold should not have bfactor"
        
        # Test Conservation config (with conservation)
        conservation_config = loader.load_config("test_conservation")
        print(f"✅ Conservation config:")
        print(f"   Model: {conservation_config.model}")
        print(f"   Features: {conservation_config.features}")
        print(f"   Load conservation: {conservation_config.load_conservation}")
        assert "conservation" in conservation_config.features, "Conservation config should have conservation feature"
        assert conservation_config.load_conservation == True, "Conservation should be enabled"
        
        return True
        
    except Exception as e:
        print(f"❌ Specialized config test failed: {e}")
        return False

def generate_summary_report(results):
    """Generate summary report"""
    print(f"\n{'='*60}")
    print("📊 CONFIGURATION SYSTEM TEST SUMMARY")
    print("="*60)
    
    total_configs = len(results)
    successful_configs = sum(1 for r in results.values() if r["status"] == "SUCCESS")
    failed_configs = total_configs - successful_configs
    
    print(f"Total configurations tested: {total_configs}")
    print(f"Successful configurations: {successful_configs}")
    print(f"Failed configurations: {failed_configs}")
    print(f"Success rate: {successful_configs/total_configs*100:.1f}%")
    
    # Successful configs
    if successful_configs > 0:
        print(f"\n✅ SUCCESSFUL CONFIGURATIONS:")
        for name, result in results.items():
            if result["status"] == "SUCCESS":
                features_str = f"{len(result['features'])} features"
                trees_str = f"{result['rf_trees']} trees"
                warnings_str = f", {len(result.get('warnings', []))} warnings" if result.get('warnings') else ""
                print(f"   • {name:20} - {result['model']:15} - {features_str}, {trees_str}{warnings_str}")
    
    # Failed configs
    if failed_configs > 0:
        print(f"\n❌ FAILED CONFIGURATIONS:")
        for name, result in results.items():
            if result["status"] in ["FAILED", "ERROR"]:
                error_info = result.get("error", f"{len(result.get('errors', []))} errors")
                print(f"   • {name:20} - {error_info}")
    
    # Save detailed results
    results_file = "config_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    return successful_configs == total_configs

def main():
    setup_logging()
    
    print("🎯 P2Rank Configuration System Test")
    print("Testing the conversion from Groovy to Python/YAML configurations")
    print()
    
    # Test configuration loading
    results = test_config_loading()
    
    # Test inheritance
    inheritance_ok = test_config_inheritance()
    
    # Test specialized features
    specialized_ok = test_specialized_features()
    
    # Generate summary
    all_passed = generate_summary_report(results)
    
    # Final status
    if all_passed and inheritance_ok and specialized_ok:
        print(f"\n🎉 ALL CONFIGURATION TESTS PASSED! 🎉")
        print(f"P2Rank Python configuration system is working correctly!")
        return 0
    else:
        print(f"\n⚠️  SOME TESTS FAILED")
        print(f"Please check the errors above and fix the configuration issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

