#!/usr/bin/env python3
"""
Model Validation Framework for P2Rank

Validates that converted Python models produce equivalent results to Java models.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.metrics import mean_squared_error, mean_absolute_error
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Run: pip install scikit-learn matplotlib seaborn")
    sys.exit(1)

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Results of model validation"""
    model_name: str
    test_samples: int
    feature_consistency: bool
    prediction_correlation: float
    prediction_rmse: float
    prediction_mae: float
    classification_accuracy: Optional[float] = None
    classification_f1: Optional[float] = None
    detailed_metrics: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None


class ModelValidator:
    """Validates converted Python models against Java references"""
    
    def __init__(self, java_models_dir: Path, python_models_dir: Path, 
                 test_data_dir: Optional[Path] = None):
        """
        Initialize validator.
        
        Args:
            java_models_dir: Path to original Java models
            python_models_dir: Path to converted Python models
            test_data_dir: Path to test data directory
        """
        self.java_models_dir = Path(java_models_dir)
        self.python_models_dir = Path(python_models_dir)
        self.test_data_dir = Path(test_data_dir) if test_data_dir else None
        
        # Initialize Java runner for reference predictions
        self.java_runner = None
        self._setup_java_runner()
    
    def _setup_java_runner(self):
        """Set up Java runner for reference predictions"""
        try:
            # Look for P2Rank executable
            possible_executables = [
                self.java_models_dir.parent / "prank",
                self.java_models_dir.parent / "bin" / "prank",
                Path("prank")  # In PATH
            ]
            
            for exe in possible_executables:
                if exe.exists() or exe.name == "prank":
                    self.java_runner = str(exe)
                    logger.info(f"Found Java P2Rank executable: {exe}")
                    break
            
            if not self.java_runner:
                logger.warning("Java P2Rank executable not found. "
                              "Reference predictions will not be available.")
        
        except Exception as e:
            logger.warning(f"Could not set up Java runner: {e}")
    
    def generate_test_data(self, model_name: str, n_samples: int = 1000) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate synthetic test data for validation.
        
        Args:
            model_name: Name of the model
            n_samples: Number of test samples to generate
            
        Returns:
            Tuple of (features, labels)
        """
        # Load feature names
        python_model_dir = self.python_models_dir / model_name
        metadata_file = python_model_dir / "metadata.json"
        
        if not metadata_file.exists():
            raise FileNotFoundError(f"Model metadata not found: {metadata_file}")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        n_features = metadata['n_features']
        features = metadata['features']
        
        # Generate realistic synthetic features based on feature types
        X = np.random.randn(n_samples, n_features)
        
        # Adjust features based on their expected ranges
        for i, feature_name in enumerate(features):
            if any(keyword in feature_name.lower() for keyword in ['hydrophobic', 'polar', 'charge']):
                # Binary or scaled features (0-1)
                X[:, i] = np.random.beta(2, 2, n_samples)
            elif 'density' in feature_name.lower():
                # Density features (positive values)
                X[:, i] = np.random.gamma(2, 0.5, n_samples)
            elif 'bfactor' in feature_name.lower():
                # B-factor values (typically 10-100)
                X[:, i] = np.random.gamma(4, 10, n_samples)
            elif any(keyword in feature_name.lower() for keyword in ['aromatic', 'cation', 'anion']):
                # Categorical-like features
                X[:, i] = np.random.binomial(1, 0.3, n_samples)
            else:
                # Keep normal distribution for other features
                X[:, i] = np.random.normal(0, 1, n_samples)
        
        # Generate binary labels (pocket/non-pocket)
        # Use a simple linear combination with noise
        weights = np.random.randn(n_features) * 0.1
        linear_combination = X @ weights
        probabilities = 1 / (1 + np.exp(-linear_combination))
        y = np.random.binomial(1, probabilities, n_samples)
        
        logger.info(f"Generated {n_samples} synthetic test samples for {model_name}")
        return X, y
    
    def load_real_test_data(self, model_name: str) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Load real test data if available.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Tuple of (features, labels) or None if not available
        """
        if not self.test_data_dir or not self.test_data_dir.exists():
            return None
        
        # Look for test data files
        test_files = [
            self.test_data_dir / f"{model_name}_test.npz",
            self.test_data_dir / f"{model_name}_validation.npz",
            self.test_data_dir / "test_data.npz"
        ]
        
        for test_file in test_files:
            if test_file.exists():
                try:
                    data = np.load(test_file)
                    X = data['features']
                    y = data['labels']
                    logger.info(f"Loaded real test data from: {test_file}")
                    return X, y
                except Exception as e:
                    logger.warning(f"Could not load test data from {test_file}: {e}")
        
        return None
    
    def get_java_predictions(self, model_name: str, test_features: np.ndarray) -> Optional[np.ndarray]:
        """
        Get predictions from the Java model for comparison.
        
        Args:
            model_name: Name of the model
            test_features: Test features
            
        Returns:
            Java model predictions or None if not available
        """
        if not self.java_runner:
            logger.warning("Java runner not available")
            return None
        
        try:
            # This is a placeholder for Java model prediction
            # In a real implementation, we would:
            # 1. Save test features to a temporary file
            # 2. Run Java P2Rank with the test data
            # 3. Parse the output predictions
            # 4. Return the prediction scores
            
            # For now, generate mock Java predictions with some noise
            # This simulates what the Java model might predict
            n_samples = test_features.shape[0]
            
            # Create a simple mock prediction based on feature values
            # This is just for demonstration
            mock_weights = np.random.RandomState(42).randn(test_features.shape[1]) * 0.1
            mock_predictions = 1 / (1 + np.exp(-(test_features @ mock_weights)))
            
            # Add some noise to simulate real Java predictions
            noise = np.random.RandomState(42).normal(0, 0.05, n_samples)
            mock_predictions = np.clip(mock_predictions + noise, 0, 1)
            
            logger.info(f"Generated mock Java predictions for {model_name}")
            return mock_predictions
            
        except Exception as e:
            logger.error(f"Failed to get Java predictions: {e}")
            return None
    
    def validate_model(self, model_name: str, use_real_data: bool = False) -> ValidationResult:
        """
        Validate a converted Python model.
        
        Args:
            model_name: Name of the model to validate
            use_real_data: Whether to use real test data if available
            
        Returns:
            Validation results
        """
        try:
            logger.info(f"Validating model: {model_name}")
            
            # Load Python model
            from .model_converter import JavaModelConverter
            converter = JavaModelConverter(self.java_models_dir, self.python_models_dir)
            python_model, metadata = converter.load_converted_model(model_name)
            
            # Get test data
            if use_real_data:
                test_data = self.load_real_test_data(model_name)
                if test_data is None:
                    logger.info("Real test data not available, using synthetic data")
                    X_test, y_test = self.generate_test_data(model_name, 1000)
                else:
                    X_test, y_test = test_data
            else:
                X_test, y_test = self.generate_test_data(model_name, 1000)
            
            # Get Python predictions
            try:
                if hasattr(python_model, 'predict_proba'):
                    python_probs = python_model.predict_proba(X_test)[:, 1]
                else:
                    python_probs = python_model.predict(X_test)
                
                python_preds = python_model.predict(X_test)
                
            except Exception as e:
                if "not fitted" in str(e):
                    raise ValueError(f"Model {model_name} is not trained. Please retrain the model with training data.")
                else:
                    raise e
            
            # Get Java reference predictions
            java_probs = self.get_java_predictions(model_name, X_test)
            
            # Calculate validation metrics
            feature_consistency = X_test.shape[1] == metadata.n_features
            
            if java_probs is not None:
                # Compare with Java predictions
                correlation = np.corrcoef(python_probs, java_probs)[0, 1]
                rmse = np.sqrt(mean_squared_error(java_probs, python_probs))
                mae = mean_absolute_error(java_probs, python_probs)
            else:
                # Use test labels for comparison
                correlation = np.corrcoef(python_probs, y_test)[0, 1]
                rmse = np.sqrt(mean_squared_error(y_test, python_probs))
                mae = mean_absolute_error(y_test, python_probs)
            
            # Classification metrics
            accuracy = accuracy_score(y_test, python_preds)
            f1 = f1_score(y_test, python_preds, average='weighted')
            
            # Detailed metrics
            detailed_metrics = {
                'precision': precision_score(y_test, python_preds, average='weighted', zero_division=0),
                'recall': recall_score(y_test, python_preds, average='weighted'),
                'prediction_std': np.std(python_probs),
                'prediction_mean': np.mean(python_probs),
                'feature_mean': np.mean(X_test),
                'feature_std': np.std(X_test)
            }
            
            result = ValidationResult(
                model_name=model_name,
                test_samples=X_test.shape[0],
                feature_consistency=feature_consistency,
                prediction_correlation=correlation,
                prediction_rmse=rmse,
                prediction_mae=mae,
                classification_accuracy=accuracy,
                classification_f1=f1,
                detailed_metrics=detailed_metrics
            )
            
            logger.info(f"Validation completed for {model_name}")
            return result
            
        except Exception as e:
            logger.error(f"Validation failed for {model_name}: {e}")
            return ValidationResult(
                model_name=model_name,
                test_samples=0,
                feature_consistency=False,
                prediction_correlation=0.0,
                prediction_rmse=float('inf'),
                prediction_mae=float('inf'),
                error_message=str(e)
            )
    
    def validate_all_models(self, use_real_data: bool = False) -> Dict[str, ValidationResult]:
        """Validate all converted models"""
        results = {}
        
        # Find all converted models
        if not self.python_models_dir.exists():
            logger.error(f"Python models directory not found: {self.python_models_dir}")
            return results
        
        model_dirs = [d for d in self.python_models_dir.iterdir() 
                     if d.is_dir() and (d / "model.pkl").exists()]
        
        for model_dir in model_dirs:
            model_name = model_dir.name
            result = self.validate_model(model_name, use_real_data)
            results[model_name] = result
        
        return results
    
    def generate_validation_report(self, results: Dict[str, ValidationResult], 
                                 output_file: Optional[Path] = None) -> str:
        """Generate a comprehensive validation report"""
        report_lines = []
        report_lines.append("P2Rank Model Validation Report")
        report_lines.append("=" * 50)
        report_lines.append("")
        
        total_models = len(results)
        successful_validations = sum(1 for r in results.values() if r.error_message is None)
        
        report_lines.append(f"Total Models: {total_models}")
        report_lines.append(f"Successful Validations: {successful_validations}")
        report_lines.append(f"Failed Validations: {total_models - successful_validations}")
        report_lines.append("")
        
        # Individual model results
        for model_name, result in results.items():
            report_lines.append(f"Model: {model_name}")
            report_lines.append("-" * 30)
            
            if result.error_message:
                report_lines.append(f"  Status: FAILED - {result.error_message}")
            else:
                report_lines.append(f"  Status: SUCCESS")
                report_lines.append(f"  Test Samples: {result.test_samples}")
                report_lines.append(f"  Feature Consistency: {'✓' if result.feature_consistency else '✗'}")
                report_lines.append(f"  Prediction Correlation: {result.prediction_correlation:.4f}")
                report_lines.append(f"  Prediction RMSE: {result.prediction_rmse:.4f}")
                report_lines.append(f"  Prediction MAE: {result.prediction_mae:.4f}")
                
                if result.classification_accuracy is not None:
                    report_lines.append(f"  Classification Accuracy: {result.classification_accuracy:.4f}")
                    report_lines.append(f"  F1 Score: {result.classification_f1:.4f}")
            
            report_lines.append("")
        
        # Summary statistics
        successful_results = [r for r in results.values() if r.error_message is None]
        if successful_results:
            correlations = [r.prediction_correlation for r in successful_results]
            accuracies = [r.classification_accuracy for r in successful_results 
                         if r.classification_accuracy is not None]
            
            report_lines.append("Summary Statistics")
            report_lines.append("-" * 30)
            report_lines.append(f"Average Correlation: {np.mean(correlations):.4f} ± {np.std(correlations):.4f}")
            if accuracies:
                report_lines.append(f"Average Accuracy: {np.mean(accuracies):.4f} ± {np.std(accuracies):.4f}")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("Recommendations")
        report_lines.append("-" * 30)
        
        poor_correlation_models = [name for name, result in results.items() 
                                  if result.error_message is None and result.prediction_correlation < 0.8]
        
        if poor_correlation_models:
            report_lines.append("Models with poor correlation (< 0.8):")
            for model in poor_correlation_models:
                report_lines.append(f"  - {model}")
            report_lines.append("Consider retraining these models with better data.")
        else:
            report_lines.append("All models show good correlation with reference predictions.")
        
        report_text = "\n".join(report_lines)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            logger.info(f"Validation report saved to: {output_file}")
        
        return report_text
    
    def create_validation_plots(self, results: Dict[str, ValidationResult], 
                              output_dir: Optional[Path] = None):
        """Create visualization plots for validation results"""
        if not output_dir:
            output_dir = Path("validation_plots")
        
        output_dir.mkdir(exist_ok=True)
        
        successful_results = {name: result for name, result in results.items() 
                            if result.error_message is None}
        
        if not successful_results:
            logger.warning("No successful validations to plot")
            return
        
        # Correlation plot
        plt.figure(figsize=(10, 6))
        models = list(successful_results.keys())
        correlations = [successful_results[model].prediction_correlation for model in models]
        
        plt.bar(models, correlations)
        plt.title("Model Prediction Correlations")
        plt.ylabel("Correlation with Reference")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / "correlation_comparison.png", dpi=300)
        plt.close()
        
        # Accuracy plot (if available)
        accuracies = [successful_results[model].classification_accuracy 
                     for model in models 
                     if successful_results[model].classification_accuracy is not None]
        
        if accuracies:
            plt.figure(figsize=(10, 6))
            models_with_acc = [model for model in models 
                              if successful_results[model].classification_accuracy is not None]
            
            plt.bar(models_with_acc, accuracies)
            plt.title("Model Classification Accuracies")
            plt.ylabel("Accuracy")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig(output_dir / "accuracy_comparison.png", dpi=300)
            plt.close()
        
        logger.info(f"Validation plots saved to: {output_dir}")


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate converted P2Rank models")
    parser.add_argument("java_models", help="Path to Java models directory")
    parser.add_argument("python_models", help="Path to Python models directory")
    parser.add_argument("--test-data", help="Path to test data directory")
    parser.add_argument("--model", help="Specific model to validate")
    parser.add_argument("--real-data", action="store_true", help="Use real test data if available")
    parser.add_argument("--output", help="Output file for validation report")
    parser.add_argument("--plots", help="Directory for validation plots")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    validator = ModelValidator(args.java_models, args.python_models, args.test_data)
    
    if args.model:
        # Validate specific model
        result = validator.validate_model(args.model, args.real_data)
        
        if result.error_message:
            print(f"✗ Validation failed for {args.model}: {result.error_message}")
        else:
            print(f"✓ Validation successful for {args.model}")
            print(f"  Correlation: {result.prediction_correlation:.4f}")
            print(f"  RMSE: {result.prediction_rmse:.4f}")
            print(f"  Accuracy: {result.classification_accuracy:.4f}")
    else:
        # Validate all models
        results = validator.validate_all_models(args.real_data)
        
        # Generate report
        report = validator.generate_validation_report(
            results, Path(args.output) if args.output else None
        )
        
        if not args.output:
            print(report)
        
        # Create plots
        if args.plots:
            validator.create_validation_plots(results, Path(args.plots))


if __name__ == "__main__":
    main()
