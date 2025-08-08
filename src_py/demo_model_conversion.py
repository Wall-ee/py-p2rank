#!/usr/bin/env python3
"""
Demo Script for P2Rank Model Conversion

This script demonstrates how to analyze, convert, and validate P2Rank Java models
to Python scikit-learn format.
"""

import os
import sys
from pathlib import Path
import logging

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging(verbose=False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def demo_model_analysis(java_models_dir):
    """Demonstrate model analysis functionality"""
    print("\n" + "="*60)
    print("1. JAVA MODEL ANALYSIS DEMO")
    print("="*60)
    
    try:
        from tools.model_analyzer import JavaModelAnalyzer
        
        analyzer = JavaModelAnalyzer(java_models_dir)
        
        # List available models
        print("\n📋 Available Java Models:")
        models = analyzer.list_available_models()
        for i, model in enumerate(models, 1):
            print(f"  {i}. {model}")
        
        if not models:
            print("  No Java models found in the specified directory.")
            return False
        
        # Analyze first model in detail
        model_name = models[0]
        print(f"\n🔍 Analyzing model: {model_name}")
        
        model_info = analyzer.get_model_info(model_name)
        print(f"  📁 Model file: {model_info['model_file']}")
        print(f"  📊 Size: {model_info['model_size_mb']} MB")
        print(f"  🧬 Features: {len(model_info['features'])}")
        
        # Show feature groups
        features = model_info['features']
        feature_groups = {}
        for feature in features:
            if '.' in feature:
                group = feature.split('.')[0]
                feature_groups[group] = feature_groups.get(group, 0) + 1
        
        print(f"  📈 Feature groups:")
        for group, count in feature_groups.items():
            print(f"     - {group}: {count} features")
        
        return True
        
    except Exception as e:
        print(f"❌ Analysis demo failed: {e}")
        return False

def demo_model_conversion(java_models_dir, python_models_dir):
    """Demonstrate model conversion functionality"""
    print("\n" + "="*60)
    print("2. MODEL CONVERSION DEMO")
    print("="*60)
    
    try:
        from tools.model_converter import JavaModelConverter
        from tools.model_analyzer import JavaModelAnalyzer
        
        analyzer = JavaModelAnalyzer(java_models_dir)
        converter = JavaModelConverter(java_models_dir, python_models_dir)
        
        models = analyzer.list_available_models()
        if not models:
            print("❌ No Java models available for conversion.")
            return False
        
        # Convert first available model
        model_name = models[0]
        print(f"\n🔄 Converting model: {model_name}")
        
        # Create synthetic training data for demonstration
        print("  📊 Generating synthetic training data...")
        import numpy as np
        from sklearn.datasets import make_classification
        
        # Load feature information
        features = analyzer.load_features(model_name)
        n_features = len(features)
        
        # Generate synthetic data
        X, y = make_classification(
            n_samples=10000,
            n_features=n_features,
            n_informative=min(10, n_features//2),
            n_redundant=min(5, n_features//4),
            n_clusters_per_class=1,
            random_state=42
        )
        
        print(f"     Training samples: {X.shape[0]}")
        print(f"     Features: {X.shape[1]}")
        print(f"     Classes: {len(np.unique(y))}")
        
        # Convert model
        print("  🏗️  Converting model structure...")
        model, metadata = converter.convert_model(model_name, X, y)
        
        print(f"  ✅ Conversion successful!")
        print(f"     Model type: {type(model).__name__}")
        print(f"     Trees: {metadata.n_trees}")
        print(f"     Features: {metadata.n_features}")
        print(f"     Output directory: {python_models_dir / model_name}")
        
        # Test prediction
        print("  🧪 Testing model prediction...")
        X_test = X[:100]  # Use first 100 samples for testing
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)
        
        print(f"     Predictions shape: {predictions.shape}")
        print(f"     Probabilities shape: {probabilities.shape}")
        print(f"     Sample predictions: {predictions[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversion demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_model_validation(java_models_dir, python_models_dir):
    """Demonstrate model validation functionality"""
    print("\n" + "="*60)
    print("3. MODEL VALIDATION DEMO")
    print("="*60)
    
    try:
        from tools.model_validator import ModelValidator
        
        validator = ModelValidator(java_models_dir, python_models_dir)
        
        # Check for converted models
        if not python_models_dir.exists():
            print("❌ No Python models directory found. Run conversion first.")
            return False
        
        converted_models = [d.name for d in python_models_dir.iterdir() 
                          if d.is_dir() and (d / "model.pkl").exists()]
        
        if not converted_models:
            print("❌ No converted models found. Run conversion first.")
            return False
        
        model_name = converted_models[0]
        print(f"\n🔬 Validating model: {model_name}")
        
        # Run validation
        print("  📊 Generating test data...")
        result = validator.validate_model(model_name, use_real_data=False)
        
        if result.error_message:
            print(f"  ❌ Validation failed: {result.error_message}")
            return False
        
        print("  ✅ Validation successful!")
        print(f"     Test samples: {result.test_samples}")
        print(f"     Feature consistency: {'✓' if result.feature_consistency else '✗'}")
        print(f"     Prediction correlation: {result.prediction_correlation:.4f}")
        print(f"     Prediction RMSE: {result.prediction_rmse:.4f}")
        print(f"     Classification accuracy: {result.classification_accuracy:.4f}")
        print(f"     F1 Score: {result.classification_f1:.4f}")
        
        # Interpretation
        if result.prediction_correlation > 0.8:
            print("  📈 Excellent correlation with reference predictions!")
        elif result.prediction_correlation > 0.6:
            print("  📊 Good correlation with reference predictions.")
        else:
            print("  ⚠️  Low correlation - model may need retraining.")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_full_pipeline(java_models_dir, python_models_dir):
    """Demonstrate the complete model conversion pipeline"""
    print("\n" + "="*60)
    print("4. FULL PIPELINE DEMO")
    print("="*60)
    
    try:
        from tools.model_manager import P2RankModelManager
        
        manager = P2RankModelManager(java_models_dir, python_models_dir)
        
        print("\n🚀 Running complete conversion pipeline...")
        
        # Run pipeline for a single model
        available_models = manager.analyzer.list_available_models()
        if not available_models:
            print("❌ No Java models available.")
            return False
        
        model_name = available_models[0]
        print(f"   Target model: {model_name}")
        
        results = manager.full_pipeline(model_name, force_convert=True, validate=True)
        
        # Generate summary
        summary = manager.generate_summary_report(results)
        print("\n📋 Pipeline Summary:")
        print("-" * 40)
        print(summary)
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main demo function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="P2Rank Model Conversion Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This demo script shows how to:
1. Analyze Java P2Rank models
2. Convert them to Python scikit-learn format
3. Validate the converted models
4. Run the complete conversion pipeline

Examples:
  # Run full demo
  python demo_model_conversion.py ../distro/models converted_models/
  
  # Run specific demos
  python demo_model_conversion.py ../distro/models converted_models/ --demo analysis
  python demo_model_conversion.py ../distro/models converted_models/ --demo conversion
        """
    )
    
    parser.add_argument("java_models", help="Path to Java models directory")
    parser.add_argument("python_models", help="Path for converted Python models")
    parser.add_argument("--demo", choices=["analysis", "conversion", "validation", "pipeline"],
                       help="Run specific demo (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Check paths
    java_models_dir = Path(args.java_models)
    python_models_dir = Path(args.python_models)
    
    if not java_models_dir.exists():
        print(f"❌ Java models directory not found: {java_models_dir}")
        sys.exit(1)
    
    # Create output directory
    python_models_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎉 P2Rank Model Conversion Demo")
    print(f"📁 Java models: {java_models_dir}")
    print(f"📁 Python models: {python_models_dir}")
    
    # Run demos
    success_count = 0
    total_demos = 0
    
    if args.demo is None or args.demo == "analysis":
        total_demos += 1
        if demo_model_analysis(java_models_dir):
            success_count += 1
    
    if args.demo is None or args.demo == "conversion":
        total_demos += 1
        if demo_model_conversion(java_models_dir, python_models_dir):
            success_count += 1
    
    if args.demo is None or args.demo == "validation":
        total_demos += 1
        if demo_model_validation(java_models_dir, python_models_dir):
            success_count += 1
    
    if args.demo is None or args.demo == "pipeline":
        total_demos += 1
        if demo_full_pipeline(java_models_dir, python_models_dir):
            success_count += 1
    
    # Summary
    print("\n" + "="*60)
    print("DEMO SUMMARY")
    print("="*60)
    print(f"Completed: {success_count}/{total_demos} demos")
    
    if success_count == total_demos:
        print("🎉 All demos completed successfully!")
        print("\n📚 Next steps:")
        print("1. Check the converted models in:", python_models_dir)
        print("2. Integrate models into your P2Rank Python application")
        print("3. Use the model_manager.py tool for production conversions")
    else:
        print(f"⚠️  {total_demos - success_count} demo(s) failed.")
        print("Check the error messages above and ensure all dependencies are installed.")
    
    print(f"\n💡 For more options, run: python tools/model_manager.py --help")

if __name__ == "__main__":
    main()
