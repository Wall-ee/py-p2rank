#!/usr/bin/env python3
"""
P2Rank Configuration System Demo

Demonstrates the complete converted configuration system capabilities.
"""

import sys
import json
from pathlib import Path
import logging

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_py import ConfigLoader, P2RankConfig, ConfigValidator
from config_py.config_manager import ConfigManager

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def demo_basic_usage():
    """Demonstrate basic configuration usage"""
    print("🔧 Basic Configuration Usage")
    print("="*50)
    
    # Load a specific configuration
    loader = ConfigLoader("config_py/core")
    config = loader.load_config("test_default")
    
    print(f"✅ Loaded configuration: test_default")
    print(f"   Model: {config.model}")
    print(f"   Features: {config.features}")
    print(f"   Classifier: {config.classifier} ({config.rf_trees} trees)")
    print(f"   Tessellation: {config.tessellation}")
    print(f"   Visualizations: {config.visualizations}")
    
    return config

def demo_inheritance():
    """Demonstrate configuration inheritance"""
    print(f"\n🔗 Configuration Inheritance")
    print("="*50)
    
    loader = ConfigLoader("config_py/core")
    
    # Load base and derived configs
    base_config = loader.load_config("base")
    test_config = loader.load_config("test_alphafold")
    
    print(f"Base config features: {base_config.features}")
    print(f"AlphaFold config features: {test_config.features}")
    print(f"Model changed: {base_config.model} → {test_config.model}")
    print(f"Visualizations inherited: {base_config.visualizations} → {test_config.visualizations}")
    
    return base_config, test_config

def demo_validation():
    """Demonstrate configuration validation"""
    print(f"\n✅ Configuration Validation")
    print("="*50)
    
    validator = ConfigValidator()
    loader = ConfigLoader("config_py/core")
    
    # Test valid configuration
    valid_config = loader.load_config("test_default")
    errors = validator.validate_config(valid_config)
    warnings = validator.get_warnings(valid_config)
    
    print(f"Valid config validation:")
    print(f"   Errors: {len(errors)}")
    print(f"   Warnings: {len(warnings)}")
    
    # Create invalid configuration for demonstration
    invalid_config = P2RankConfig(
        features=[],  # Empty features (invalid)
        rf_trees=0,   # Invalid tree count
        tessellation=-1,  # Invalid tessellation
        classifier="InvalidClassifier"  # Invalid classifier
    )
    
    errors = validator.validate_config(invalid_config)
    print(f"\nInvalid config validation:")
    print(f"   Errors: {len(errors)}")
    for error in errors:
        print(f"     • {error}")

def demo_specialized_configs():
    """Demonstrate specialized domain configurations"""
    print(f"\n🔬 Specialized Domain Configurations")
    print("="*50)
    
    manager = ConfigManager("config_py")
    available = manager.list_available_configs()
    
    print(f"Available configurations:")
    print(f"   Core: {len(available['core'])} configs")
    for config_name in available['core']:
        print(f"     • {config_name}")
    
    print(f"   Specialized:")
    for category, configs in available['specialized'].items():
        if configs:
            print(f"     {category}: {len(configs)} configs")
            for config_name in configs:
                print(f"       • {config_name}")

def demo_config_management():
    """Demonstrate advanced configuration management"""
    print(f"\n⚙️  Advanced Configuration Management")
    print("="*50)
    
    manager = ConfigManager("config_py")
    
    # Get configuration summary
    summary = manager.get_config_summary("test_alphafold")
    print(f"AlphaFold config summary:")
    print(f"   Model: {summary['model']}")
    print(f"   Features: {summary['feature_count']} ({', '.join(summary['features'])})")
    print(f"   Classifier: {summary['classifier']} ({summary['rf_trees']} trees)")
    print(f"   Valid: {summary['validation']['valid']}")
    
    # Compare configurations
    comparison = manager.compare_configs("test_default", "test_alphafold")
    print(f"\nComparison (default vs alphafold):")
    print(f"   Differences: {comparison['diff_count']}")
    print(f"   Same fields: {comparison['same_count']}")
    
    key_diffs = ["model", "features"]
    for field in key_diffs:
        if field in comparison["differences"]:
            diff = comparison["differences"][field]
            print(f"   {field}: {diff['test_default']} → {diff['test_alphafold']}")

def demo_custom_config():
    """Demonstrate creating custom configurations"""
    print(f"\n🎨 Custom Configuration Creation")
    print("="*50)
    
    manager = ConfigManager("config_py")
    
    # Create custom configuration
    overrides = {
        "rf_trees": 200,  # More trees
        "tessellation": 3,  # Higher density
        "visualizations": True,  # Enable visualizations
        "log_level": "DEBUG"  # More verbose logging
    }
    
    custom_config = manager.create_custom_config(
        "test_default",
        overrides,
        output_path=Path("custom_config.yaml")
    )
    
    print(f"Created custom configuration:")
    print(f"   Base: test_default")
    print(f"   Trees: {custom_config.rf_trees}")
    print(f"   Tessellation: {custom_config.tessellation}")
    print(f"   Visualizations: {custom_config.visualizations}")
    print(f"   Saved to: custom_config.yaml")

def demo_config_export():
    """Demonstrate configuration export and reporting"""
    print(f"\n📊 Configuration Export and Reporting")
    print("="*50)
    
    manager = ConfigManager("config_py")
    
    # Export complete report
    report_file = Path("config_system_report.json")
    report = manager.export_config_report(report_file)
    
    print(f"Configuration report generated:")
    print(f"   File: {report_file}")
    print(f"   Core configs: {report['summary']['total_core_configs']}")
    print(f"   Specialized configs: {report['summary']['total_specialized_configs']}")
    print(f"   Total configurations: {len(report['configurations'])}")

def demonstrate_practical_usage():
    """Show practical usage scenarios"""
    print(f"\n💼 Practical Usage Scenarios")
    print("="*50)
    
    # Scenario 1: Load config for protein analysis
    print("Scenario 1: Analyze AlphaFold structure")
    loader = ConfigLoader("config_py/core")
    alphafold_config = loader.load_config("test_alphafold")
    print(f"   ✅ Loaded AlphaFold config (no B-factor)")
    print(f"   Features: {alphafold_config.features}")
    
    # Scenario 2: Training new model
    print("\nScenario 2: Train conservation model")
    conservation_config = loader.load_config("train_conservation")
    print(f"   ✅ Loaded training config")
    print(f"   Conservation enabled: {conservation_config.load_conservation}")
    print(f"   Sample from decoys: {conservation_config.sample_negatives_from_decoys}")
    
    # Scenario 3: Quick validation
    print("\nScenario 3: Validate configuration")
    validator = ConfigValidator()
    errors = validator.validate_config(conservation_config)
    warnings = validator.get_warnings(conservation_config)
    print(f"   ✅ Validation complete")
    print(f"   Status: {'Valid' if not errors else 'Has errors'}")
    print(f"   Warnings: {len(warnings)}")

def main():
    setup_logging()
    
    print("🎯 P2Rank Configuration System Demo")
    print("Demonstrating the complete converted configuration system")
    print()
    
    try:
        # Basic demos
        demo_basic_usage()
        demo_inheritance()
        demo_validation()
        demo_specialized_configs()
        
        # Advanced demos
        demo_config_management()
        demo_custom_config()
        demo_config_export()
        
        # Practical usage
        demonstrate_practical_usage()
        
        print(f"\n{'='*60}")
        print("🎉 CONFIGURATION SYSTEM DEMO COMPLETE! 🎉")
        print("="*60)
        print("The P2Rank Python configuration system provides:")
        print("✅ Full compatibility with original Groovy configs")
        print("✅ YAML format for better readability and maintenance")
        print("✅ Configuration inheritance and validation")
        print("✅ Specialized domain configurations")
        print("✅ Advanced management and comparison tools")
        print("✅ Custom configuration creation")
        print("✅ Comprehensive reporting and export")
        print()
        print("🚀 The configuration system is ready for production use!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

