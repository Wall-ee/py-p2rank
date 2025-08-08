#!/usr/bin/env python3
"""
Java Model Analyzer for P2Rank

Analyzes Java model files to understand their structure and extract metadata.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import zstandard as zstd
import logging

logger = logging.getLogger(__name__)


class JavaModelAnalyzer:
    """Analyzes Java model files from P2Rank"""
    
    def __init__(self, models_dir: Path):
        """
        Initialize analyzer.
        
        Args:
            models_dir: Path to the models directory
        """
        self.models_dir = Path(models_dir)
        self.supported_models = [
            'default', 'alphafold', 'conservation_hmm', 
            'alphafold_conservation_hmm', 'default_rescore',
            'rescore_2024', 'rescore_conservation'
        ]
    
    def list_available_models(self) -> List[str]:
        """List all available models in the directory"""
        models = []
        for model_name in self.supported_models:
            model_path = self.models_dir / model_name
            if model_path.exists() and (model_path / "model.zst").exists():
                models.append(model_name)
        return models
    
    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get basic information about a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary with model information
        """
        model_path = self.models_dir / model_name
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")
        
        model_file = model_path / "model.zst"
        features_file = model_path / "features.txt"
        
        info = {
            "name": model_name,
            "path": str(model_path),
            "model_file": str(model_file) if model_file.exists() else None,
            "features_file": str(features_file) if features_file.exists() else None,
            "model_size_mb": round(model_file.stat().st_size / (1024*1024), 2) if model_file.exists() else 0,
            "features": self.load_features(model_name) if features_file.exists() else [],
            "score_transforms": self._get_score_transforms(model_name)
        }
        
        return info
    
    def load_features(self, model_name: str) -> List[str]:
        """
        Load feature list from features.txt.
        
        Args:
            model_name: Name of the model
            
        Returns:
            List of feature names
        """
        features_file = self.models_dir / model_name / "features.txt"
        
        if not features_file.exists():
            logger.warning(f"Features file not found: {features_file}")
            return []
        
        features = []
        with open(features_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    features.append(line)
        
        return features
    
    def _get_score_transforms(self, model_name: str) -> Dict[str, str]:
        """Get score transformation files for a model"""
        transforms = {}
        
        # Check for model-specific transforms
        transform_dir = self.models_dir / "_score_transform"
        if transform_dir.exists():
            # Look for transforms with model name prefix
            for transform_file in transform_dir.glob(f"{model_name}_*.json"):
                transform_type = transform_file.stem.replace(f"{model_name}_", "")
                transforms[transform_type] = str(transform_file)
        
        return transforms
    
    def decompress_model(self, model_name: str, output_file: Optional[Path] = None) -> Path:
        """
        Decompress the zstd model file.
        
        Args:
            model_name: Name of the model
            output_file: Output file path (optional)
            
        Returns:
            Path to decompressed file
        """
        model_file = self.models_dir / model_name / "model.zst"
        
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")
        
        if output_file is None:
            output_file = model_file.parent / "model.bin"
        
        try:
            with open(model_file, 'rb') as compressed:
                dctx = zstd.ZstdDecompressor()
                with open(output_file, 'wb') as decompressed:
                    dctx.copy_stream(compressed, decompressed)
            
            logger.info(f"Decompressed model saved to: {output_file}")
            return output_file
            
        except Exception as e:
            logger.error(f"Failed to decompress model: {e}")
            raise
    
    def analyze_java_serialized_data(self, model_name: str) -> Dict[str, Any]:
        """
        Analyze Java serialized model data (basic analysis).
        
        Args:
            model_name: Name of the model
            
        Returns:
            Analysis results
        """
        # First decompress the model
        try:
            decompressed_file = self.decompress_model(model_name)
        except Exception as e:
            logger.error(f"Could not decompress model {model_name}: {e}")
            return {"error": str(e)}
        
        # Basic binary analysis
        with open(decompressed_file, 'rb') as f:
            # Read first few bytes to check Java serialization magic
            magic = f.read(4)
            if magic[:2] == b'\xac\xed':  # Java serialization magic number
                analysis = {
                    "format": "Java Serialization",
                    "magic": magic.hex(),
                    "file_size": decompressed_file.stat().st_size,
                    "estimated_type": "Random Forest Model"
                }
            else:
                analysis = {
                    "format": "Unknown",
                    "magic": magic.hex(),
                    "file_size": decompressed_file.stat().st_size,
                    "error": "Not a Java serialized object"
                }
        
        # Clean up temporary file
        decompressed_file.unlink()
        
        return analysis
    
    def generate_model_report(self, model_name: str) -> Dict[str, Any]:
        """
        Generate a comprehensive report for a model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Comprehensive model report
        """
        report = {
            "model_info": self.get_model_info(model_name),
            "java_analysis": self.analyze_java_serialized_data(model_name),
            "feature_analysis": self._analyze_features(model_name)
        }
        
        return report
    
    def _analyze_features(self, model_name: str) -> Dict[str, Any]:
        """Analyze the features used in the model"""
        features = self.load_features(model_name)
        
        # Group features by category
        feature_groups = {}
        for feature in features:
            if '.' in feature:
                group, name = feature.split('.', 1)
                if group not in feature_groups:
                    feature_groups[group] = []
                feature_groups[group].append(name)
            else:
                if 'ungrouped' not in feature_groups:
                    feature_groups['ungrouped'] = []
                feature_groups['ungrouped'].append(feature)
        
        return {
            "total_features": len(features),
            "feature_groups": feature_groups,
            "features": features
        }


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze P2Rank Java models")
    parser.add_argument("models_dir", help="Path to models directory")
    parser.add_argument("--model", help="Specific model to analyze")
    parser.add_argument("--list", action="store_true", help="List available models")
    parser.add_argument("--output", help="Output file for report (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    analyzer = JavaModelAnalyzer(args.models_dir)
    
    if args.list:
        models = analyzer.list_available_models()
        print("Available models:")
        for model in models:
            print(f"  - {model}")
        return
    
    if args.model:
        try:
            report = analyzer.generate_model_report(args.model)
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(report, f, indent=2)
                print(f"Report saved to: {args.output}")
            else:
                print(json.dumps(report, indent=2))
                
        except Exception as e:
            logger.error(f"Error analyzing model {args.model}: {e}")
            sys.exit(1)
    else:
        # Analyze all models
        models = analyzer.list_available_models()
        all_reports = {}
        
        for model in models:
            try:
                all_reports[model] = analyzer.generate_model_report(model)
                print(f"✓ Analyzed model: {model}")
            except Exception as e:
                logger.error(f"✗ Failed to analyze model {model}: {e}")
                all_reports[model] = {"error": str(e)}
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(all_reports, f, indent=2)
            print(f"All reports saved to: {args.output}")
        else:
            print(json.dumps(all_reports, indent=2))


if __name__ == "__main__":
    main()
