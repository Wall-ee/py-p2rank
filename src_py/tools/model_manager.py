#!/usr/bin/env python3
"""
Model Manager for P2Rank Python Implementation

Main interface for analyzing, converting, and validating P2Rank models.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tools.model_analyzer import JavaModelAnalyzer
    from tools.model_converter import JavaModelConverter
    from tools.model_validator import ModelValidator
except ImportError as e:
    print(f"Error importing tools: {e}")
    print("Make sure you're running from the correct directory")
    sys.exit(1)

logger = logging.getLogger(__name__)


class P2RankModelManager:
    """Main model management interface"""
    
    def __init__(self, java_models_dir: Path, python_models_dir: Path):
        """
        Initialize model manager.
        
        Args:
            java_models_dir: Path to original Java models
            python_models_dir: Path for converted Python models
        """
        self.java_models_dir = Path(java_models_dir)
        self.python_models_dir = Path(python_models_dir)
        
        # Initialize components
        self.analyzer = JavaModelAnalyzer(self.java_models_dir)
        self.converter = JavaModelConverter(self.java_models_dir, self.python_models_dir)
        self.validator = ModelValidator(self.java_models_dir, self.python_models_dir)
        
        # Create output directory
        self.python_models_dir.mkdir(parents=True, exist_ok=True)
    
    def analyze_models(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Analyze Java models"""
        logger.info("Starting model analysis...")
        
        if model_name:
            try:
                report = self.analyzer.generate_model_report(model_name)
                return {model_name: report}
            except Exception as e:
                logger.error(f"Failed to analyze model {model_name}: {e}")
                return {model_name: {"error": str(e)}}
        else:
            # Analyze all models
            available_models = self.analyzer.list_available_models()
            reports = {}
            
            for model in available_models:
                try:
                    reports[model] = self.analyzer.generate_model_report(model)
                    logger.info(f"✓ Analyzed model: {model}")
                except Exception as e:
                    logger.error(f"✗ Failed to analyze model {model}: {e}")
                    reports[model] = {"error": str(e)}
            
            return reports
    
    def convert_models(self, model_name: Optional[str] = None, 
                      force: bool = False) -> Dict[str, Any]:
        """Convert Java models to Python format"""
        logger.info("Starting model conversion...")
        
        if model_name:
            try:
                model, metadata = self.converter.convert_model(model_name, force_retrain=force)
                return {
                    model_name: {
                        "status": "success",
                        "features": metadata.n_features,
                        "trees": metadata.n_trees,
                        "output_dir": str(self.python_models_dir / model_name)
                    }
                }
            except Exception as e:
                logger.error(f"Failed to convert model {model_name}: {e}")
                return {model_name: {"status": "error", "error": str(e)}}
        else:
            # Convert all models
            return self.converter.convert_all_models()
    
    def validate_models(self, model_name: Optional[str] = None, 
                       use_real_data: bool = False) -> Dict[str, Any]:
        """Validate converted Python models"""
        logger.info("Starting model validation...")
        
        if model_name:
            result = self.validator.validate_model(model_name, use_real_data)
            return {model_name: result}
        else:
            return self.validator.validate_all_models(use_real_data)
    
    def full_pipeline(self, model_name: Optional[str] = None, 
                     force_convert: bool = False, 
                     validate: bool = True) -> Dict[str, Any]:
        """Run the complete model conversion pipeline"""
        logger.info("Starting full model conversion pipeline...")
        
        results = {
            "analysis": {},
            "conversion": {},
            "validation": {}
        }
        
        # Step 1: Analyze models
        try:
            results["analysis"] = self.analyze_models(model_name)
            logger.info("✓ Analysis completed")
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            results["analysis"] = {"error": str(e)}
        
        # Step 2: Convert models
        try:
            results["conversion"] = self.convert_models(model_name, force_convert)
            logger.info("✓ Conversion completed")
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            results["conversion"] = {"error": str(e)}
        
        # Step 3: Validate models (if requested)
        if validate:
            try:
                validation_results = self.validate_models(model_name)
                
                # Convert ValidationResult objects to dictionaries for JSON serialization
                serializable_results = {}
                for name, result in validation_results.items():
                    if hasattr(result, '__dict__'):
                        serializable_results[name] = result.__dict__
                    else:
                        serializable_results[name] = result
                
                results["validation"] = serializable_results
                logger.info("✓ Validation completed")
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                results["validation"] = {"error": str(e)}
        
        return results
    
    def generate_summary_report(self, results: Dict[str, Any]) -> str:
        """Generate a summary report of the pipeline results"""
        lines = []
        lines.append("P2Rank Model Conversion Pipeline Summary")
        lines.append("=" * 50)
        lines.append("")
        
        # Analysis summary
        if "analysis" in results and results["analysis"]:
            analysis = results["analysis"]
            if "error" in analysis:
                lines.append(f"Analysis: FAILED - {analysis['error']}")
            else:
                analyzed_models = len([k for k in analysis.keys() if "error" not in analysis[k]])
                total_models = len(analysis)
                lines.append(f"Analysis: {analyzed_models}/{total_models} models analyzed successfully")
        
        # Conversion summary
        if "conversion" in results and results["conversion"]:
            conversion = results["conversion"]
            if "error" in conversion:
                lines.append(f"Conversion: FAILED - {conversion['error']}")
            else:
                converted_models = len([k for k, v in conversion.items() 
                                      if isinstance(v, dict) and v.get("status") == "success"])
                total_models = len(conversion)
                lines.append(f"Conversion: {converted_models}/{total_models} models converted successfully")
        
        # Validation summary
        if "validation" in results and results["validation"]:
            validation = results["validation"]
            if "error" in validation:
                lines.append(f"Validation: FAILED - {validation['error']}")
            else:
                validated_models = len([k for k, v in validation.items() 
                                      if isinstance(v, dict) and not v.get("error_message")])
                total_models = len(validation)
                lines.append(f"Validation: {validated_models}/{total_models} models validated successfully")
                
                # Average metrics
                if validated_models > 0:
                    correlations = []
                    accuracies = []
                    
                    for k, v in validation.items():
                        if isinstance(v, dict) and not v.get("error_message"):
                            if "prediction_correlation" in v:
                                correlations.append(v["prediction_correlation"])
                            if "classification_accuracy" in v and v["classification_accuracy"]:
                                accuracies.append(v["classification_accuracy"])
                    
                    if correlations:
                        lines.append(f"Average Correlation: {sum(correlations)/len(correlations):.3f}")
                    if accuracies:
                        lines.append(f"Average Accuracy: {sum(accuracies)/len(accuracies):.3f}")
        
        lines.append("")
        
        # Detailed results
        if "conversion" in results and results["conversion"]:
            lines.append("Model Details:")
            lines.append("-" * 30)
            
            for model_name, result in results["conversion"].items():
                if isinstance(result, dict):
                    if result.get("status") == "success":
                        lines.append(f"✓ {model_name}: {result.get('features', 'N/A')} features, "
                                   f"{result.get('trees', 'N/A')} trees")
                    else:
                        lines.append(f"✗ {model_name}: {result.get('error', 'Unknown error')}")
        
        return "\n".join(lines)
    
    def list_models(self) -> Dict[str, Any]:
        """List available Java and converted Python models"""
        java_models = self.analyzer.list_available_models()
        
        python_models = []
        if self.python_models_dir.exists():
            python_models = [d.name for d in self.python_models_dir.iterdir() 
                           if d.is_dir() and (d / "model.pkl").exists()]
        
        return {
            "java_models": java_models,
            "python_models": python_models,
            "conversion_needed": list(set(java_models) - set(python_models))
        }
    
    def install_converted_models(self, distro_dir: Path):
        """Install converted models into the distribution package"""
        distro_models_dir = distro_dir / "models"
        distro_models_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy converted models to distro
        installed = []
        failed = []
        
        for model_dir in self.python_models_dir.iterdir():
            if model_dir.is_dir() and (model_dir / "model.pkl").exists():
                try:
                    import shutil
                    target_dir = distro_models_dir / model_dir.name
                    
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    
                    shutil.copytree(model_dir, target_dir)
                    installed.append(model_dir.name)
                    logger.info(f"Installed model: {model_dir.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to install model {model_dir.name}: {e}")
                    failed.append(model_dir.name)
        
        return {
            "installed": installed,
            "failed": failed,
            "distro_models_dir": str(distro_models_dir)
        }


def main():
    """Main command-line interface"""
    parser = argparse.ArgumentParser(
        description="P2Rank Model Manager - Analyze, convert, and validate models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze all Java models
  python model_manager.py analyze /path/to/distro/models python_models/
  
  # Convert specific model
  python model_manager.py convert /path/to/distro/models python_models/ --model default
  
  # Run full pipeline
  python model_manager.py pipeline /path/to/distro/models python_models/
  
  # Validate converted models
  python model_manager.py validate /path/to/distro/models python_models/
        """
    )
    
    parser.add_argument("command", choices=["analyze", "convert", "validate", "pipeline", "list", "install"],
                       help="Command to execute")
    parser.add_argument("java_models", help="Path to Java models directory")
    parser.add_argument("python_models", help="Path for Python models directory")
    
    parser.add_argument("--model", help="Specific model name to process")
    parser.add_argument("--force", action="store_true", help="Force reconversion of existing models")
    parser.add_argument("--real-data", action="store_true", help="Use real test data for validation")
    parser.add_argument("--output", help="Output file for results (JSON format)")
    parser.add_argument("--distro", help="Distribution directory for installing models")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize manager
    manager = P2RankModelManager(args.java_models, args.python_models)
    
    # Execute command
    results = None
    
    try:
        if args.command == "analyze":
            results = manager.analyze_models(args.model)
            
        elif args.command == "convert":
            results = manager.convert_models(args.model, args.force)
            
        elif args.command == "validate":
            results = manager.validate_models(args.model, args.real_data)
            # Convert ValidationResult objects to dicts
            serializable_results = {}
            for name, result in results.items():
                if hasattr(result, '__dict__'):
                    serializable_results[name] = result.__dict__
                else:
                    serializable_results[name] = result
            results = serializable_results
            
        elif args.command == "pipeline":
            results = manager.full_pipeline(args.model, args.force, validate=True)
            
        elif args.command == "list":
            results = manager.list_models()
            
        elif args.command == "install":
            if not args.distro:
                print("Error: --distro argument required for install command")
                sys.exit(1)
            results = manager.install_converted_models(Path(args.distro))
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"Results saved to: {args.output}")
        else:
            if args.command == "pipeline":
                # Generate summary report for pipeline
                summary = manager.generate_summary_report(results)
                print(summary)
            else:
                print(json.dumps(results, indent=2, default=str))
    
    except Exception as e:
        logger.error(f"Command failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
