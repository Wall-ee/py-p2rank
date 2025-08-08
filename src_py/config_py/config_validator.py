"""
P2Rank Configuration Validator

Validates P2Rank configurations for common errors and consistency issues.
"""

from typing import List, Dict, Any
import logging

from .config_loader import P2RankConfig

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validates P2Rank configurations"""
    
    def __init__(self):
        self.valid_classifiers = ["RandomForest", "FasterForest", "FastRandomForest"]
        self.valid_features = [
            "chem", "volsite", "protrusion", "bfactor", "conservation",
            "pmass", "cr1pos", "ss_atomic", "ss_sas", "ss_cloud"
        ]
        self.valid_weight_functions = ["INV", "LINEAR", "GAUSS", "CONST"]
        self.valid_log_levels = ["TRACE", "DEBUG", "INFO", "WARN", "ERROR"]
    
    def validate_config(self, config: P2RankConfig) -> List[str]:
        """
        Validate a P2Rank configuration
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate basic requirements
        errors.extend(self._validate_basic_requirements(config))
        
        # Validate features
        errors.extend(self._validate_features(config))
        
        # Validate classifier settings
        errors.extend(self._validate_classifier(config))
        
        # Validate numeric ranges
        errors.extend(self._validate_numeric_ranges(config))
        
        # Validate dependencies
        errors.extend(self._validate_dependencies(config))
        
        # Validate consistency
        errors.extend(self._validate_consistency(config))
        
        return errors
    
    def _validate_basic_requirements(self, config: P2RankConfig) -> List[str]:
        """Validate basic configuration requirements"""
        errors = []
        
        # Features cannot be empty
        if not config.features:
            errors.append("Features list cannot be empty")
        
        # Model name should be specified
        if not config.model or not config.model.strip():
            errors.append("Model name cannot be empty")
        
        return errors
    
    def _validate_features(self, config: P2RankConfig) -> List[str]:
        """Validate feature configuration"""
        errors = []
        
        # Check for unknown features
        unknown_features = [f for f in config.features if f not in self.valid_features]
        if unknown_features:
            errors.append(f"Unknown features: {unknown_features}")
        
        # Validate feature-specific requirements
        if "conservation" in config.features and not config.load_conservation:
            errors.append("Conservation feature requires load_conservation=true")
        
        # Check for conflicting features
        if "bfactor" in config.features and config.model == "alphafold":
            logger.warning("B-factor feature typically not used with AlphaFold structures")
        
        return errors
    
    def _validate_classifier(self, config: P2RankConfig) -> List[str]:
        """Validate classifier configuration"""
        errors = []
        
        # Validate classifier type
        if config.classifier not in self.valid_classifiers:
            errors.append(f"Invalid classifier '{config.classifier}'. "
                         f"Valid options: {self.valid_classifiers}")
        
        # Validate Random Forest parameters
        if config.rf_trees <= 0:
            errors.append("rf_trees must be positive")
        
        if config.rf_trees > 1000:
            logger.warning(f"Large number of trees ({config.rf_trees}) may be slow")
        
        if config.rf_depth < 0:
            errors.append("rf_depth cannot be negative (0=unlimited)")
        
        if config.rf_bagsize <= 0:
            errors.append("rf_bagsize must be positive")
        
        return errors
    
    def _validate_numeric_ranges(self, config: P2RankConfig) -> List[str]:
        """Validate numeric parameter ranges"""
        errors = []
        
        # Distance parameters must be positive
        distance_params = [
            ("positive_point_ligand_distance", config.positive_point_ligand_distance),
            ("neutral_points_margin", config.neutral_points_margin),
            ("neighbourhood_radius", config.neighbourhood_radius),
            ("protrusion_radius", config.protrusion_radius),
            ("solvent_radius", config.solvent_radius),
            ("surface_additional_cutoff", config.surface_additional_cutoff)
        ]
        
        for name, value in distance_params:
            if value <= 0:
                errors.append(f"{name} must be positive")
        
        # Tessellation must be positive
        if config.tessellation <= 0:
            errors.append("tessellation must be positive")
        
        # Sampling multiplier should be reasonable
        if config.sampling_multiplier <= 0:
            errors.append("sampling_multiplier must be positive")
        
        # Point score power should be reasonable
        if config.point_score_pow <= 0:
            errors.append("point_score_pow must be positive")
        
        # Thread count validation
        if config.threads < 0:
            errors.append("threads cannot be negative")
        
        if config.crossval_threads <= 0:
            errors.append("crossval_threads must be positive")
        
        # Loop count validation
        if config.loop <= 0:
            errors.append("loop must be positive")
        
        return errors
    
    def _validate_dependencies(self, config: P2RankConfig) -> List[str]:
        """Validate parameter dependencies"""
        errors = []
        
        # Tessellation dependencies
        if config.train_tessellation < 0:
            errors.append("train_tessellation cannot be negative")
        
        if config.train_tessellation_negatives < 0:
            errors.append("train_tessellation_negatives cannot be negative")
        
        # Weight function validation
        if config.weight_function not in self.valid_weight_functions:
            errors.append(f"Invalid weight_function '{config.weight_function}'. "
                         f"Valid options: {self.valid_weight_functions}")
        
        # Log level validation
        if config.log_level not in self.valid_log_levels:
            errors.append(f"Invalid log_level '{config.log_level}'. "
                         f"Valid options: {self.valid_log_levels}")
        
        return errors
    
    def _validate_consistency(self, config: P2RankConfig) -> List[str]:
        """Validate configuration consistency"""
        errors = []
        
        # Prediction threshold should be reasonable
        if not (0 <= config.pred_point_threshold <= 1):
            errors.append("pred_point_threshold should be between 0 and 1")
        
        # Neutral margin should be larger than positive distance
        if config.neutral_points_margin <= config.positive_point_ligand_distance:
            errors.append("neutral_points_margin should be larger than positive_point_ligand_distance")
        
        # Minimum cluster size should be reasonable
        if config.pred_min_cluster_size < 1:
            errors.append("pred_min_cluster_size must be at least 1")
        
        # Training instance limits
        if config.max_train_instances < 0:
            errors.append("max_train_instances cannot be negative")
        
        if config.train_pockets < 0:
            errors.append("train_pockets cannot be negative")
        
        return errors
    
    def validate_config_dict(self, config_dict: Dict[str, Any]) -> List[str]:
        """Validate configuration dictionary before creating P2RankConfig"""
        errors = []
        
        # Check for required fields
        if 'features' not in config_dict:
            errors.append("Missing required field: features")
        
        # Check for unknown fields
        valid_fields = set(P2RankConfig.__dataclass_fields__.keys())
        unknown_fields = set(config_dict.keys()) - valid_fields - {'_extends', '_description'}
        if unknown_fields:
            logger.warning(f"Unknown configuration fields: {unknown_fields}")
        
        return errors
    
    def get_warnings(self, config: P2RankConfig) -> List[str]:
        """Get configuration warnings (non-critical issues)"""
        warnings = []
        
        # Performance warnings
        if config.rf_trees > 500:
            warnings.append(f"Large number of trees ({config.rf_trees}) may impact performance")
        
        if config.tessellation > 3:
            warnings.append(f"High tessellation ({config.tessellation}) increases computation time")
        
        # Feature combination warnings
        if "bfactor" in config.features and config.model.startswith("alphafold"):
            warnings.append("B-factor feature may not be meaningful for AlphaFold structures")
        
        # Cache warnings
        if config.cache_datasets and config.loop > 1:
            warnings.append("Dataset caching with multiple loops may consume significant memory")
        
        return warnings

