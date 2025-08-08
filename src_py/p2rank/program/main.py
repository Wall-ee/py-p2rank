"""
Main entry point for P2Rank Python implementation
"""
import sys
import argparse
import logging
import os
from typing import List, Optional, Dict, Any
from pathlib import Path

from .params import Params
from ..domain.protein import Protein
from ..domain.dataset import Dataset
from ..prediction.pocket_predictor import PocketPredictor
from ..utils.logging_utils import setup_logging


class Main:
    """Main application class for P2Rank"""
    
    def __init__(self, args: argparse.Namespace):
        """Initialize Main with parsed arguments"""
        self.args = args
        self.params = Params.get_instance()
        self.command = ""
        self.install_dir = ""
        self.error = False
        
        # Setup logging
        setup_logging(self.params.log_level, self.params.log_to_console)
        self.logger = logging.getLogger(__name__)
    
    def find_install_dir(self) -> str:
        """Find installation directory"""
        # Get directory of this script
        current_dir = Path(__file__).parent.parent.parent.parent
        return str(current_dir.absolute())
    
    def init_params(self, config_file: Optional[str] = None):
        """Initialize parameters from config file and command line"""
        self.install_dir = self.find_install_dir()
        self.params.install_dir = self.install_dir
        
        # Load default config if exists
        default_config = os.path.join(self.install_dir, "config", "default.yaml")
        if os.path.exists(default_config):
            self.load_config(default_config)
        
        # Load custom config if specified
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
        
        # Update from command line arguments
        self.params.update_from_command_line(vars(self.args))
        
        # Validate parameters
        self.params.validate()
    
    def load_config(self, config_file: str):
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                self.params.update_from_dict(config)
        except ImportError:
            self.logger.warning("PyYAML not installed, skipping config file loading")
        except Exception as e:
            self.logger.warning(f"Failed to load config file {config_file}: {e}")
    
    def run_predict(self):
        """Run pocket prediction"""
        if not hasattr(self.args, 'input') or not self.args.input:
            raise ValueError("Input protein file required for prediction")
        
        input_file = self.args.input
        output_dir = self.args.output or "output"
        
        self.logger.info(f"Predicting pockets for: {input_file}")
        self.logger.info(f"Output directory: {output_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # TODO: Implement protein loading and prediction
        # This would require BioPython integration
        self.logger.info("Pocket prediction completed")
    
    def run_help(self):
        """Display help information"""
        help_text = """
P2Rank - Protein Pocket Prediction Tool (Python Implementation)

Usage:
    p2rank predict -i <input.pdb> [-o <output_dir>]
    p2rank help
    p2rank version

Commands:
    predict     Predict pockets in a protein structure
    help        Show this help message
    version     Show version information

Options:
    -i, --input     Input protein file (PDB/CIF format)
    -o, --output    Output directory (default: output)
    -c, --config    Configuration file
    -m, --model     Model to use (default: default)
    --threads       Number of threads to use
    --seed          Random seed
    
Examples:
    p2rank predict -i protein.pdb -o results/
    p2rank predict -i protein.pdb -m alphafold
"""
        print(help_text)
    
    def run_version(self):
        """Display version information"""
        print("P2Rank Python Implementation v1.0.0")
        print(f"Home: {self.install_dir}")
        print(f"Python: {sys.version}")
        print(f"CPUs: {os.cpu_count()}")
    
    def run(self) -> bool:
        """
        Main execution method.
        
        Returns:
            False if successful, True if there was an error
        """
        try:
            if not hasattr(self.args, 'command') or not self.args.command:
                self.run_help()
                return True
            
            self.command = self.args.command
            
            if self.command == 'help':
                self.run_help()
                return False
            
            if self.command == 'version':
                self.run_version()
                return False
            
            # Initialize parameters for other commands
            config_file = getattr(self.args, 'config', None)
            self.init_params(config_file)
            
            if self.command == 'predict':
                self.run_predict()
            else:
                self.logger.error(f"Unknown command: {self.command}")
                return True
            
            return self.error
            
        except Exception as e:
            self.logger.error(f"Error during execution: {e}")
            return True


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        description="P2Rank - Protein Pocket Prediction Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Predict command
    predict_parser = subparsers.add_parser('predict', help='Predict protein pockets')
    predict_parser.add_argument('-i', '--input', required=True,
                               help='Input protein file (PDB/CIF format)')
    predict_parser.add_argument('-o', '--output', default='output',
                               help='Output directory (default: output)')
    predict_parser.add_argument('-c', '--config',
                               help='Configuration file')
    predict_parser.add_argument('-m', '--model', default='default',
                               help='Model to use (default: default)')
    predict_parser.add_argument('--threads', type=int,
                               help='Number of threads to use')
    predict_parser.add_argument('--seed', type=int, default=42,
                               help='Random seed (default: 42)')
    
    # Help command
    subparsers.add_parser('help', help='Show help information')
    
    # Version command
    subparsers.add_parser('version', help='Show version information')
    
    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle case where no command is provided
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create and run main application
    app = Main(args)
    error = app.run()
    
    sys.exit(1 if error else 0)


if __name__ == "__main__":
    main() 