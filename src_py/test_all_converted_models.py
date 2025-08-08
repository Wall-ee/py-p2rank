#!/usr/bin/env python3
"""
Test All Converted Models

Test all converted P2Rank models to ensure they work correctly.
"""

import sys
import json
import numpy as np
from pathlib import Path
import joblib
import logging

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def test_model_prediction(model_path: Path) -> dict:
    """Test a single model's prediction capability"""
    model_name = model_path.name
    
    try:
        # Load metadata
        metadata_file = model_path / "metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Load model
        model_file = model_path / "model.pkl"
        model = joblib.load(model_file)
        
        # Generate test data
        n_features = metadata['n_features']
        n_samples = 100
        
        # Create realistic test features
        np.random.seed(42)
        X_test = np.random.randn(n_samples, n_features)
        
        # Adjust features based on feature names
        features = metadata.get('features', [])
        for i, feature_name in enumerate(features):
            if i >= n_features:
                break
            feature_lower = feature_name.lower()
            
            if any(keyword in feature_lower for keyword in ['hydrophobic', 'polar']):
                X_test[:, i] = np.abs(X_test[:, i])  # Positive values
            elif 'bfactor' in feature_lower:
                X_test[:, i] = np.abs(X_test[:, i]) * 50 + 20  # B-factor range
        
        # Test predictions
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)
        
        # Calculate statistics
        pred_stats = {
            "unique_predictions": len(np.unique(predictions)),
            "positive_rate": float(np.mean(predictions)),
            "prob_range": [float(probabilities.min()), float(probabilities.max())],
            "prob_mean": float(np.mean(probabilities[:, 1])),
            "prob_std": float(np.std(probabilities[:, 1]))
        }
        
        return {
            "model_name": model_name,
            "status": "SUCCESS",
            "n_features": n_features,
            "n_trees": metadata.get('n_trees', 0),
            "test_samples": n_samples,
            "prediction_stats": pred_stats,
            "can_predict": True,
            "error": None
        }
        
    except Exception as e:
        return {
            "model_name": model_name,
            "status": "FAILED", 
            "error": str(e),
            "can_predict": False
        }

def test_all_models(models_dir: Path) -> dict:
    """Test all converted models"""
    results = {}
    total_models = 0
    successful_models = 0
    
    print("🧪 Testing All Converted P2Rank Models")
    print("="*60)
    
    for model_path in models_dir.iterdir():
        if model_path.is_dir() and (model_path / "model.pkl").exists():
            total_models += 1
            print(f"\n📋 Testing model: {model_path.name}")
            
            result = test_model_prediction(model_path)
            results[model_path.name] = result
            
            if result["status"] == "SUCCESS":
                successful_models += 1
                print(f"   ✅ SUCCESS")
                print(f"      Features: {result['n_features']}")
                print(f"      Trees: {result['n_trees']}")
                print(f"      Test samples: {result['test_samples']}")
                print(f"      Positive rate: {result['prediction_stats']['positive_rate']:.3f}")
                print(f"      Prob mean: {result['prediction_stats']['prob_mean']:.3f}")
            else:
                print(f"   ❌ FAILED: {result['error']}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Total models tested: {total_models}")
    print(f"Successful models: {successful_models}")
    print(f"Failed models: {total_models - successful_models}")
    print(f"Success rate: {successful_models/total_models*100:.1f}%")
    
    # Detailed summary
    if successful_models > 0:
        print(f"\n✅ SUCCESSFUL MODELS:")
        for name, result in results.items():
            if result["status"] == "SUCCESS":
                print(f"   • {name:25} - {result['n_features']:2d} features, {result['n_trees']:3d} trees")
    
    if successful_models < total_models:
        print(f"\n❌ FAILED MODELS:")
        for name, result in results.items():
            if result["status"] == "FAILED":
                print(f"   • {name:25} - {result['error']}")
    
    return {
        "total_models": total_models,
        "successful_models": successful_models,
        "success_rate": successful_models/total_models if total_models > 0 else 0,
        "individual_results": results
    }

def main():
    setup_logging()
    
    models_dir = Path("converted_models_final")
    
    if not models_dir.exists():
        print(f"❌ Models directory not found: {models_dir}")
        sys.exit(1)
    
    # Test all models
    results = test_all_models(models_dir)
    
    # Save detailed results
    results_file = "all_models_test_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    # Final status
    if results["success_rate"] == 1.0:
        print(f"\n🎉 ALL MODELS CONVERTED SUCCESSFULLY! 🎉")
        print(f"All {results['total_models']} P2Rank models are now available in Python format!")
    else:
        print(f"\n⚠️  PARTIAL SUCCESS")
        print(f"{results['successful_models']}/{results['total_models']} models converted successfully")

if __name__ == "__main__":
    main()
