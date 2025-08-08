"""
P2Rank Configuration Manager

Provides high-level tools for managing P2Rank configurations.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import logging

from .config_loader import ConfigLoader, P2RankConfig
from .config_validator import ConfigValidator

logger = logging.getLogger(__name__)


class ConfigManager:
    """High-level configuration management for P2Rank"""
    
    def __init__(self, config_root: Union[str, Path]):
        """
        Initialize configuration manager
        
        Args:
            config_root: Root directory containing configuration files
        """
        self.config_root = Path(config_root)
        self.core_dir = self.config_root / "core"
        self.specialized_dir = self.config_root / "specialized"
        
        self.loader = ConfigLoader(self.core_dir)
        self.validator = ConfigValidator()
    
    def list_available_configs(self) -> Dict[str, List[str]]:
        """List all available configurations by category"""
        configs = {
            "core": [],
            "specialized": {
                "ions": [],
                "lig": [],
                "dna": [],
                "pept": []
            }
        }
        
        # Core configurations
        if self.core_dir.exists():
            configs["core"] = [f.stem for f in self.core_dir.glob("*.yaml")]
        
        # Specialized configurations
        for category in ["ions", "lig", "dna", "pept"]:
            category_dir = self.specialized_dir / category
            if category_dir.exists():
                configs["specialized"][category] = [f.stem for f in category_dir.glob("*.yaml")]
        
        return configs
    
    def get_config(self, config_name: str, category: str = "core") -> P2RankConfig:
        """
        Get a configuration by name and category
        
        Args:
            config_name: Name of configuration
            category: Category (core, ions, lig, dna, pept)
            
        Returns:
            P2RankConfig instance
        """
        if category == "core":
            loader = ConfigLoader(self.core_dir)
        else:
            specialized_path = self.specialized_dir / category
            if not specialized_path.exists():
                raise ValueError(f"Unknown specialized category: {category}")
            loader = ConfigLoader(specialized_path)
        
        return loader.load_config(config_name)
    
    def validate_config(self, config: P2RankConfig) -> Dict[str, Any]:
        """
        Validate a configuration and return detailed results
        
        Args:
            config: Configuration to validate
            
        Returns:
            Validation results dictionary
        """
        errors = self.validator.validate_config(config)
        warnings = self.validator.get_warnings(config)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings)
        }
    
    def create_custom_config(self, 
                           base_config: str,
                           overrides: Dict[str, Any],
                           output_path: Optional[Path] = None,
                           category: str = "core") -> P2RankConfig:
        """
        Create a custom configuration based on existing config with overrides
        
        Args:
            base_config: Name of base configuration
            overrides: Dictionary of parameter overrides
            output_path: Optional path to save the custom config
            category: Category of base config
            
        Returns:
            P2RankConfig instance
        """
        # Load base configuration
        base = self.get_config(base_config, category)
        
        # Apply overrides
        base_dict = base.__dict__.copy()
        base_dict.update(overrides)
        
        # Create new config
        custom_config = P2RankConfig(**base_dict)
        
        # Validate
        validation = self.validate_config(custom_config)
        if not validation["valid"]:
            logger.warning(f"Custom config has {validation['error_count']} validation errors")
            for error in validation["errors"]:
                logger.warning(f"  - {error}")
        
        # Save if path provided
        if output_path:
            self.save_config_as_yaml(custom_config, output_path, base_config, overrides)
        
        return custom_config
    
    def save_config_as_yaml(self, 
                          config: P2RankConfig,
                          output_path: Path,
                          base_config: Optional[str] = None,
                          overrides: Optional[Dict[str, Any]] = None):
        """Save configuration as YAML file"""
        import yaml
        
        # Prepare YAML data
        yaml_data = {}
        
        # Add metadata
        if base_config:
            yaml_data["_extends"] = base_config
        yaml_data["_description"] = f"Custom configuration generated from {base_config or 'base'}"
        
        # Add either overrides or full config
        if overrides:
            yaml_data.update(overrides)
        else:
            # Convert config to dict, excluding default values
            config_dict = config.__dict__
            yaml_data.update(config_dict)
        
        # Save to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to: {output_path}")
    
    def compare_configs(self, config1: str, config2: str, 
                       category1: str = "core", category2: str = "core") -> Dict[str, Any]:
        """
        Compare two configurations
        
        Args:
            config1: First config name
            config2: Second config name
            category1: Category of first config
            category2: Category of second config
            
        Returns:
            Comparison results
        """
        cfg1 = self.get_config(config1, category1)
        cfg2 = self.get_config(config2, category2)
        
        differences = {}
        same_fields = {}
        
        # Compare all fields
        all_fields = set(cfg1.__dict__.keys()) | set(cfg2.__dict__.keys())
        
        for field in all_fields:
            val1 = getattr(cfg1, field, None)
            val2 = getattr(cfg2, field, None)
            
            if val1 != val2:
                differences[field] = {
                    config1: val1,
                    config2: val2
                }
            else:
                same_fields[field] = val1
        
        return {
            "differences": differences,
            "same_fields": same_fields,
            "diff_count": len(differences),
            "same_count": len(same_fields)
        }
    
    def get_config_summary(self, config_name: str, category: str = "core") -> Dict[str, Any]:
        """Get a summary of a configuration"""
        config = self.get_config(config_name, category)
        validation = self.validate_config(config)
        
        return {
            "name": config_name,
            "category": category,
            "model": config.model,
            "features": config.features,
            "feature_count": len(config.features),
            "classifier": config.classifier,
            "rf_trees": config.rf_trees,
            "rf_depth": config.rf_depth,
            "tessellation": config.tessellation,
            "validation": validation
        }
    
    def export_config_report(self, output_file: Path):
        """Export a complete report of all configurations"""
        available_configs = self.list_available_configs()
        report = {
            "timestamp": str(Path().absolute()),
            "summary": {
                "total_core_configs": len(available_configs["core"]),
                "total_specialized_configs": sum(len(configs) for configs in available_configs["specialized"].values())
            },
            "configurations": {}
        }
        
        # Process core configs
        for config_name in available_configs["core"]:
            try:
                summary = self.get_config_summary(config_name, "core")
                report["configurations"][f"core.{config_name}"] = summary
            except Exception as e:
                logger.error(f"Error processing core config {config_name}: {e}")
        
        # Process specialized configs
        for category, config_list in available_configs["specialized"].items():
            for config_name in config_list:
                try:
                    summary = self.get_config_summary(config_name, category)
                    report["configurations"][f"{category}.{config_name}"] = summary
                except Exception as e:
                    logger.error(f"Error processing {category} config {config_name}: {e}")
        
        # Save report
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Configuration report exported to: {output_file}")
        return report
    
    def migrate_from_distro(self, distro_config_dir: Path, backup: bool = True):
        """
        Migrate configurations from P2Rank distribution format
        
        Args:
            distro_config_dir: Path to distro/config directory
            backup: Whether to backup existing configs
        """
        if not distro_config_dir.exists():
            raise FileNotFoundError(f"Distribution config directory not found: {distro_config_dir}")
        
        if backup and self.config_root.exists():
            backup_dir = self.config_root.parent / f"{self.config_root.name}_backup"
            shutil.copytree(self.config_root, backup_dir, dirs_exist_ok=True)
            logger.info(f"Backup created at: {backup_dir}")
        
        # Create target directories
        self.core_dir.mkdir(parents=True, exist_ok=True)
        self.specialized_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy existing YAML configs from distro
        yaml_files = list(distro_config_dir.glob("*.yaml"))
        for yaml_file in yaml_files:
            target_path = self.core_dir / yaml_file.name
            shutil.copy2(yaml_file, target_path)
            logger.info(f"Migrated: {yaml_file.name}")
        
        logger.info(f"Migration completed. Migrated {len(yaml_files)} configurations.")


def create_default_manager() -> ConfigManager:
    """Create a ConfigManager with default paths"""
    config_root = Path(__file__).parent
    return ConfigManager(config_root)

