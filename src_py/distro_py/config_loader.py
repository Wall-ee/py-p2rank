#!/usr/bin/env python3
"""
Configuration loader for P2Rank Python Distribution

Loads YAML configuration files with support for inheritance and parameter overrides.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Configuration file loader with YAML support and inheritance"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize config loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        if config_dir is None:
            # Default to config directory relative to this script
            self.config_dir = Path(__file__).parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self._config_cache = {}
    
    def load_config(self, config_name: str, 
                   command_line_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Load configuration from file with inheritance support.
        
        Args:
            config_name: Name of config file (with or without .yaml extension)
            command_line_params: Parameters from command line to override
            
        Returns:
            Merged configuration dictionary
        """
        # Normalize config name
        if not config_name.endswith('.yaml'):
            config_name += '.yaml'
        
        config_path = self.config_dir / config_name
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        # Load base configuration
        config = self._load_yaml_file(config_path)
        
        # Handle inheritance
        if '_extends' in config:
            parent_config_name = config.pop('_extends')
            parent_config = self.load_config(parent_config_name)
            
            # Merge parent config with current config (current takes precedence)
            merged_config = self._deep_merge(parent_config, config)
            config = merged_config
        
        # Apply command line parameter overrides
        if command_line_params:
            config = self._deep_merge(config, command_line_params)
        
        # Process special values
        config = self._process_special_values(config)
        
        return config
    
    def _load_yaml_file(self, config_path: Path) -> Dict[str, Any]:
        """Load YAML file and return as dictionary"""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file) or {}
            logger.debug(f"Loaded configuration from: {config_path}")
            return config
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file {config_path}: {e}")
        except Exception as e:
            raise IOError(f"Error reading configuration file {config_path}: {e}")
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries, with override taking precedence.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _process_special_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process special values in configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Processed configuration
        """
        processed = {}
        
        for key, value in config.items():
            if isinstance(value, dict):
                processed[key] = self._process_special_values(value)
            elif isinstance(value, str):
                processed[key] = self._process_string_value(value)
            else:
                processed[key] = value
        
        return processed
    
    def _process_string_value(self, value: str) -> Any:
        """
        Process special string values (e.g., environment variables, path expansion).
        
        Args:
            value: String value to process
            
        Returns:
            Processed value
        """
        # Environment variable substitution
        if value.startswith('${') and value.endswith('}'):
            env_var = value[2:-1]
            default_value = ""
            
            if ':' in env_var:
                env_var, default_value = env_var.split(':', 1)
            
            return os.environ.get(env_var, default_value)
        
        # Path expansion
        if value.startswith('~'):
            return os.path.expanduser(value)
        
        # Special model directory placeholder
        if '{models_dir}' in value:
            models_dir = os.environ.get('P2RANK_INSTALL_DIR', '.')
            models_dir = os.path.join(models_dir, 'models')
            return value.replace('{models_dir}', models_dir)
        
        return value
    
    def list_configs(self) -> list:
        """List available configuration files"""
        if not self.config_dir.exists():
            return []
        
        configs = []
        for file_path in self.config_dir.glob('*.yaml'):
            configs.append(file_path.stem)
        
        return sorted(configs)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration for required parameters.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_params = [
            'model',
            'features',
            'pred_protein_surface_cutoff',
            'pred_min_cluster_size',
            'classifier'
        ]
        
        missing_params = []
        
        for param in required_params:
            if param not in config:
                missing_params.append(param)
        
        if missing_params:
            logger.error(f"Missing required configuration parameters: {missing_params}")
            return False
        
        # Validate specific parameter types and ranges
        if not isinstance(config.get('features'), list):
            logger.error("'features' parameter must be a list")
            return False
        
        if config.get('threads', 1) < -1 or config.get('threads', 1) == 0:
            logger.error("'threads' parameter must be -1 (auto) or positive integer")
            return False
        
        return True


def load_default_config() -> Dict[str, Any]:
    """Load the default configuration"""
    loader = ConfigLoader()
    return loader.load_config('default')


def parse_command_line_params(args: list) -> Dict[str, Any]:
    """
    Parse command line parameters in P2Rank format.
    
    Args:
        args: List of command line arguments
        
    Returns:
        Dictionary of parsed parameters
    """
    params = {}
    i = 0
    
    while i < len(args):
        arg = args[i]
        
        # Check for parameter format: -param_name value
        if arg.startswith('-') and not arg.startswith('--'):
            param_name = arg[1:]  # Remove leading -
            
            if i + 1 < len(args) and not args[i + 1].startswith('-'):
                param_value = args[i + 1]
                
                # Try to convert to appropriate type
                try:
                    # Try integer
                    if param_value.isdigit() or (param_value.startswith('-') and param_value[1:].isdigit()):
                        param_value = int(param_value)
                    # Try float
                    elif '.' in param_value:
                        param_value = float(param_value)
                    # Try boolean
                    elif param_value.lower() in ['true', 'false']:
                        param_value = param_value.lower() == 'true'
                except ValueError:
                    pass  # Keep as string
                
                params[param_name] = param_value
                i += 2
            else:
                # Boolean flag (no value)
                params[param_name] = True
                i += 1
        else:
            i += 1
    
    return params


if __name__ == "__main__":
    # Test the config loader
    import sys
    
    logging.basicConfig(level=logging.DEBUG)
    
    loader = ConfigLoader()
    
    print("Available configurations:")
    for config_name in loader.list_configs():
        print(f"  - {config_name}")
    
    print("\nLoading default configuration...")
    config = loader.load_config('default')
    
    print(f"Model: {config['model']}")
    print(f"Features: {config['features']}")
    print(f"Threads: {config['threads']}")
    
    if len(sys.argv) > 1:
        print(f"\nLoading {sys.argv[1]} configuration...")
        try:
            config = loader.load_config(sys.argv[1])
            print(f"Model: {config['model']}")
            print(f"Features: {config['features']}")
        except Exception as e:
            print(f"Error: {e}") 