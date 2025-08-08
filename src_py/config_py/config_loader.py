"""
P2Rank Configuration Loader

Loads and manages P2Rank configurations in YAML format with inheritance support.
"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


@dataclass
class P2RankConfig:
    """P2Rank configuration data class with all parameters"""
    
    # === Path Configuration ===
    dataset_base_dir: str = "../../p2rank-datasets"
    output_base_dir: str = "../../p2rank-results"
    
    # === Model Configuration ===
    model: str = "default"
    features: List[str] = field(default_factory=lambda: ["chem", "volsite", "protrusion", "bfactor"])
    
    # === Classifier Configuration ===
    classifier: str = "RandomForest"
    rf_trees: int = 100
    rf_depth: int = 12
    rf_features: int = 0  # 0=default(sqrt)
    rf_bagsize: int = 100
    rf_threads: int = 0  # 0=use threads param
    rf_flatten: bool = False
    rf_batch_prediction: bool = False
    rf_flatten_as_legacy: bool = False
    
    # === Feature Configuration ===
    atom_table_features: List[str] = field(default_factory=list)
    residue_table_features: List[str] = field(default_factory=list)
    feat_aa_properties: List[str] = field(default_factory=list)
    atom_table_feat_pow: int = 2
    atom_table_feat_keep_sgn: bool = False
    average_feat_vectors: bool = False
    avg_weighted: bool = False
    avg_pow: int = 1
    
    # === Distance and Threshold Parameters ===
    positive_point_ligand_distance: float = 2.5
    neutral_points_margin: float = 5.5
    neighbourhood_radius: float = 8.0
    protrusion_radius: float = 10.0
    solvent_radius: float = 1.6
    surface_additional_cutoff: float = 1.8
    extended_pocket_cutoff: float = 3.0
    
    # === Tessellation and Sampling ===
    tessellation: int = 2
    train_tessellation: int = 0  # 0=use tessellation
    train_tessellation_negatives: int = 0
    sampling_multiplier: float = 3.0
    
    # === Training Parameters ===
    train_pockets: int = 0  # 0=all
    max_train_instances: int = 0  # 0=unlimited
    balance_class_weights: bool = False
    target_class_weight_ratio: float = 1.0
    target_class_ratio: float = 1.0
    subsample: bool = False
    sample_negatives_from_decoys: bool = False
    
    # === Prediction Parameters ===
    predictions: bool = True
    predict_residues: bool = False
    pred_point_threshold: float = 0.4
    pred_min_cluster_size: int = 3
    point_score_pow: float = 2.0
    strict_inner_points: bool = False
    ligand_derived_point_labeling: bool = True
    
    # === Weight Function Parameters ===
    weight_power: float = 2.0
    weight_sigma: float = 2.2
    weight_dist_param: float = 4.5
    weight_function: str = "INV"
    
    # === Execution Parameters ===
    threads: int = field(default_factory=lambda: os.cpu_count() or 1)
    loop: int = 1
    seed: int = 42
    crossval_threads: int = 1
    
    # === Output and Logging ===
    visualizations: bool = False
    vis_generate_proteins: bool = True
    vis_highlight_ligands: bool = False
    output_only_stats: bool = False
    log_cases: bool = False
    log_to_console: bool = True
    log_to_file: bool = False
    log_level: str = "INFO"
    zip_log_file: bool = False
    out_prefix_date: bool = True
    
    # === Cache and Performance ===
    cache_datasets: bool = False
    clear_prim_caches: bool = True
    clear_sec_caches: bool = True
    delete_models: bool = False
    delete_vectors: bool = False
    
    # === Error Handling ===
    fail_fast: bool = False
    
    # === Statistics ===
    stats_collect_predictions: bool = False
    classifier_train_stats: bool = False
    feature_importances: bool = False
    selected_stats: List[str] = field(default_factory=list)
    eval_tolerances: List[int] = field(default_factory=lambda: [0, 1, 2, 4, 10, 99])
    
    # === Advanced Features ===
    load_conservation: bool = False
    conservation_files_pattern: str = ""
    
    # === Score Transformers ===
    zscoretp_transformer: str = ""
    probatp_transformer: str = ""
    zscoretp_res_transformer: str = ""
    probatp_res_transformer: str = ""
    
    # === Specialized Features ===
    feat_pmass_radius: float = 7.0
    ss_cloud_radius: float = 6.0
    
    # === Loop Control ===
    ploop_delete_runs: bool = False
    ploop_zip_runs: bool = False


class ConfigLoader:
    """Loads P2Rank configurations from YAML files with inheritance support"""
    
    def __init__(self, config_dir: Union[str, Path]):
        """
        Initialize config loader
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        
    def load_config(self, config_name: str) -> P2RankConfig:
        """
        Load a configuration by name
        
        Args:
            config_name: Name of configuration (without .yaml extension)
            
        Returns:
            P2RankConfig instance
        """
        logger.info(f"Loading configuration: {config_name}")
        
        config_data = self._load_config_data(config_name)
        
        # Remove metadata fields
        for key in list(config_data.keys()):
            if key.startswith('_'):
                del config_data[key]
        
        try:
            return P2RankConfig(**config_data)
        except TypeError as e:
            logger.error(f"Error creating config for {config_name}: {e}")
            # Create config with known valid fields only
            valid_fields = {k: v for k, v in config_data.items() 
                          if k in P2RankConfig.__dataclass_fields__}
            return P2RankConfig(**valid_fields)
    
    def _load_config_data(self, config_name: str) -> Dict[str, Any]:
        """Load raw configuration data with inheritance resolution"""
        
        if config_name in self._config_cache:
            return self._config_cache[config_name].copy()
        
        config_file = self.config_dir / f"{config_name}.yaml"
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        
        # Handle inheritance
        if '_extends' in config_data:
            parent_name = config_data['_extends']
            logger.debug(f"Configuration {config_name} extends {parent_name}")
            
            parent_data = self._load_config_data(parent_name)
            # Merge parent config with current config
            merged_data = self._merge_configs(parent_data, config_data)
            config_data = merged_data
        
        # Resolve variable substitutions
        config_data = self._resolve_variables(config_data)
        
        # Cache the resolved config
        self._config_cache[config_name] = config_data.copy()
        
        return config_data
    
    def _merge_configs(self, parent: Dict[str, Any], child: Dict[str, Any]) -> Dict[str, Any]:
        """Merge child configuration into parent configuration"""
        merged = parent.copy()
        
        for key, value in child.items():
            if key.startswith('_'):
                # Skip metadata fields in merging
                merged[key] = value
            elif isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # Recursively merge dictionaries
                merged[key] = self._merge_configs(merged[key], value)
            elif isinstance(value, list) and key in merged and isinstance(merged[key], list):
                # For lists, child completely replaces parent (no merging)
                merged[key] = value
            else:
                # Simple override
                merged[key] = value
        
        return merged
    
    def _resolve_variables(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve variable substitutions in configuration"""
        resolved = {}
        
        for key, value in config_data.items():
            if isinstance(value, str):
                # Simple variable substitution
                resolved[key] = self._substitute_string(value, config_data)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_variables(value)
            elif isinstance(value, list):
                resolved[key] = [
                    self._substitute_string(item, config_data) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                resolved[key] = value
        
        return resolved
    
    def _substitute_string(self, text: str, context: Dict[str, Any]) -> str:
        """Substitute variables in string"""
        if '{' not in text:
            return text
        
        # Replace {variable} patterns
        import re
        def replace_var(match):
            var_name = match.group(1)
            if var_name in context:
                return str(context[var_name])
            elif var_name == 'version':
                return 'python'  # Default version
            elif var_name == 'models_dir':
                return 'models'  # Default models directory
            else:
                logger.warning(f"Unknown variable: {var_name}")
                return match.group(0)  # Return unchanged
        
        return re.sub(r'\{([^}]+)\}', replace_var, text)
    
    def list_configs(self) -> List[str]:
        """List all available configuration names"""
        config_files = list(self.config_dir.glob("*.yaml"))
        return [f.stem for f in config_files]
    
    def validate_config(self, config: P2RankConfig) -> List[str]:
        """
        Validate configuration for common issues
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate features
        if not config.features:
            errors.append("Features list cannot be empty")
        
        # Validate numeric ranges
        if config.rf_trees <= 0:
            errors.append("rf_trees must be positive")
        
        if config.tessellation <= 0:
            errors.append("tessellation must be positive")
        
        if config.neighbourhood_radius <= 0:
            errors.append("neighbourhood_radius must be positive")
        
        if config.positive_point_ligand_distance <= 0:
            errors.append("positive_point_ligand_distance must be positive")
        
        # Validate classifier
        valid_classifiers = ["RandomForest", "FasterForest", "FastRandomForest"]
        if config.classifier not in valid_classifiers:
            errors.append(f"classifier must be one of: {valid_classifiers}")
        
        return errors


def load_default_config() -> P2RankConfig:
    """Load the default P2Rank configuration"""
    return P2RankConfig()


def create_config_from_dict(config_dict: Dict[str, Any]) -> P2RankConfig:
    """Create P2RankConfig from dictionary"""
    # Filter out unknown fields
    valid_fields = {k: v for k, v in config_dict.items() 
                    if k in P2RankConfig.__dataclass_fields__}
    return P2RankConfig(**valid_fields)

