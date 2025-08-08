#!/usr/bin/env python3
"""
Fix Model Conversion Script

This script demonstrates the fixed model conversion process that automatically
generates training data for models and ensures they are properly trained.
"""

import sys
from pathlib import Path
import logging

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def test_single_model_conversion(java_models_dir, python_models_dir, model_name="default"):
    """Test conversion of a single model with the fix"""
    print(f"\n🔧 Testing fixed conversion for model: {model_name}")
    print("="*60)
    
    try:
        from tools.model_converter import JavaModelConverter
        from tools.model_validator import ModelValidator
        
        # Initialize converter
        converter = JavaModelConverter(java_models_dir, python_models_dir)
        
        # Force reconversion with the fix
        print(f"🔄 Converting model {model_name} (forced reconversion)...")
        model, metadata = converter.convert_model(model_name, force_retrain=True)
        
        print(f"✅ Conversion successful!")
        print(f"   Model type: {type(model).__name__}")
        print(f"   Features: {metadata.n_features}")
        print(f"   Trees: {metadata.n_trees}")
        print(f"   Conversion method: {metadata.notes}")
        
        # Test if model can predict
        print(f"🧪 Testing model prediction capability...")
        import numpy as np
        
        # Create test data
        test_features = np.random.randn(10, metadata.n_features)
        
        # Test prediction
        predictions = model.predict(test_features)
        probabilities = model.predict_proba(test_features)
        
        print(f"   Predictions shape: {predictions.shape}")
        print(f"   Probabilities shape: {probabilities.shape}")
        print(f"   Sample predictions: {predictions[:3]}")
        print(f"   Sample probabilities: {probabilities[:3, 1]}")
        
        # Now test validation
        print(f"🔬 Testing model validation...")
        validator = ModelValidator(java_models_dir, python_models_dir)
        result = validator.validate_model(model_name)
        
        if result.error_message:
            print(f"   ❌ Validation failed: {result.error_message}")
            return False
        else:
            print(f"   ✅ Validation successful!")
            print(f"      Test samples: {result.test_samples}")
            print(f"      Feature consistency: {'✓' if result.feature_consistency else '✗'}")
            print(f"      Prediction correlation: {result.prediction_correlation:.4f}")
            print(f"      Classification accuracy: {result.classification_accuracy:.4f}")
            return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_models_conversion(java_models_dir, python_models_dir):
    """Test conversion of all models with the fix"""
    print(f"\n🚀 Testing fixed conversion for all models")
    print("="*60)
    
    try:
        from tools.model_manager import P2RankModelManager
        
        # Initialize manager
        manager = P2RankModelManager(java_models_dir, python_models_dir)
        
        # Run pipeline with forced reconversion
        print("🔄 Running full pipeline with forced reconversion...")
        results = manager.full_pipeline(force_convert=True, validate=True)
        
        # Generate summary
        summary = manager.generate_summary_report(results)
        print("\n📋 Pipeline Results:")
        print("-" * 40)
        print(summary)
        
        # Count successes
        conversion_results = results.get("conversion", {})
        validation_results = results.get("validation", {})
        
        successful_conversions = len([k for k, v in conversion_results.items() 
                                    if isinstance(v, dict) and v.get("status") == "success"])
        
        successful_validations = len([k for k, v in validation_results.items() 
                                    if isinstance(v, dict) and not v.get("error_message")])
        
        total_models = len(conversion_results)
        
        print(f"\n📊 Summary Statistics:")
        print(f"   Total models: {total_models}")
        print(f"   Successful conversions: {successful_conversions}/{total_models}")
        print(f"   Successful validations: {successful_validations}/{total_models}")
        
        if successful_conversions == total_models and successful_validations == total_models:
            print(f"🎉 All models converted and validated successfully!")
            return True
        else:
            print(f"⚠️ Some models failed conversion or validation.")
            return False
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test fixed model conversion")
    parser.add_argument("java_models", help="Path to Java models directory", 
                       default="../distro/models", nargs='?')
    parser.add_argument("python_models", help="Path for converted Python models",
                       default="converted_models", nargs='?')
    parser.add_argument("--model", help="Test specific model only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        setup_logging()
    
    # Check paths
    java_models_dir = Path(args.java_models)
    python_models_dir = Path(args.python_models)
    
    if not java_models_dir.exists():
        print(f"❌ Java models directory not found: {java_models_dir}")
        sys.exit(1)
    
    # Create output directory
    python_models_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔧 P2Rank Model Conversion Fix Test")
    print(f"📁 Java models: {java_models_dir}")
    print(f"📁 Python models: {python_models_dir}")
    
    success = True
    
    if args.model:
        # Test specific model
        success = test_single_model_conversion(java_models_dir, python_models_dir, args.model)
    else:
        # Test all models
        success = test_all_models_conversion(java_models_dir, python_models_dir)
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 Fix verification successful! All models converted and validated.")
        print("\n💡 The model conversion issue has been resolved:")
        print("   ✅ Models are now automatically trained with synthetic data")
        print("   ✅ Validation works correctly")
        print("   ✅ Models are ready for use in P2Rank Python")
        print(f"\n📁 Converted models are available in: {python_models_dir}")
    else:
        print("❌ Fix verification failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
