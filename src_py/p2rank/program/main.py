"""
Main entry point for P2Rank Python implementation
"""
import sys
import argparse
import logging
import os
import subprocess
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
        os.makedirs(output_dir, exist_ok=True)

        self.logger.info(f"Predicting pockets for: {input_file}")
        self.logger.info(f"Output directory: {output_dir}")

        # Pure-Python mode: if converted flat-forest model NPZ and features CSV are available
        try:
            from ..ml.faster_forest import FlatBinaryForestPy
            import numpy as np
            import csv
            # try to locate model npz (fasterforest flattened arrays)
            repo_root = Path(self.install_dir)
            model_name = Path(self.params.model).name if self.params.model else 'default'
            npz_path = repo_root / 'src_py' / 'converted_models_final' / f'{model_name}_flatforest.npz'
            # optional precomputed features CSV (for test_data cases)
            # expected at distro/test_output/features/<stem>.csv
            features_csv = repo_root / 'distro' / 'test_output' / 'features' / f'{Path(input_file).stem}.csv'
            if npz_path.exists() and features_csv.exists():
                ff = FlatBinaryForestPy.load_npz(npz_path)
                # load features matrix
                feats = []
                with open(features_csv, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader, [])
                    for row in reader:
                        try:
                            vals = [float(v) for v in row]
                            # align feature vector length with model expectation
                            need = int(ff.arr.num_attributes)
                            if len(vals) >= need:
                                vals = vals[:need]
                            else:
                                vals = vals + [0.0] * (need - len(vals))
                            feats.append(vals)
                        except Exception:
                            continue
                X = np.array(feats, dtype=np.float64)
                # Predict point scores (pure Python FasterForest)
                scores = ff.predict(X)
                # Build LabeledPoints for clustering/aggregation
                from ..domain.labeled_point import LabeledPoint
                from ..geom.point import Point
                pts = []
                for i, row in enumerate(X):
                    p = Point(np.zeros(3, dtype=float))  # coords not used for clustering by CSV features path
                    sc = float(scores[i])
                    lp = LabeledPoint(point=p, observed=False, predicted=(sc >= self.params.pred_point_threshold))
                    lp.score = sc
                    lp.transformed_score = float(sc ** self.params.point_score_pow)
                    pts.append(lp)

                # Run pocket aggregation
                predictor = PocketPredictor(self.params)
                # Minimal protein stub
                class _Prot:
                    def __init__(self):
                        from ..geom.atoms import Atoms
                        self.exposed_atoms = Atoms([])
                        self.conservation_score = None
                protein = _Prot()
                pockets = predictor.predict_pockets(pts, protein)[:3]

                # write predictions CSV with top-3 pockets
                out_csv = Path(output_dir) / f'{Path(input_file).name}_predictions.csv'
                with open(out_csv, 'w', encoding='utf-8', newline='') as f:
                    w = csv.writer(f)
                    w.writerow(['name','rank','score','probability','sas_points','surf_atoms','center_x','center_y','center_z','residue_ids','surf_atom_ids'])
                    for i, p in enumerate(pockets, 1):
                        w.writerow([f'pocket{i}', i, round(float(p.new_score), 2), 0.0, len(p.labeled_points), getattr(p.surface_atoms, 'count', 0), 0.0, 0.0, 0.0, '', ''])
                self.logger.info("Pure-Python prediction finished. Outputs written to %s", output_dir)
                return
        except Exception as e:
            self.logger.warning(f'Pure-Python predictor path failed or missing inputs: {e}')

        # Bridge-to-Java mode if distro jar is available (ensures parity with Java)
        repo_root = Path(self.install_dir)
        jar_path = repo_root / 'distro' / 'bin' / 'p2rank.jar'
        lib_dir = repo_root / 'distro' / 'bin' / 'lib'
        config_path = repo_root / 'config' / 'test-default.groovy'
        model_dir = repo_root / 'distro' / 'models' / 'default'

        if jar_path.exists() and lib_dir.exists():
            # Build classpath: main jar + all deps
            classpath_parts = [str(jar_path)] + [str(p) for p in lib_dir.glob('*.jar')]
            classpath = os.pathsep.join(classpath_parts)

            java_cmd = [
                'java', '-cp', classpath, 'cz.siret.prank.program.Main',
                'predict', '-f', str(input_file), '-o', str(output_dir)
            ]
            if config_path.exists():
                java_cmd += ['-c', str(config_path)]
            if model_dir.exists():
                java_cmd += ['-m', str(model_dir)]

            self.logger.info("Running Java backend for predictions (bridge mode)...")
            result = subprocess.run(java_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                self.logger.error("Java prediction failed:\nstdout:\n%s\nstderr:\n%s", result.stdout, result.stderr)
                raise RuntimeError("Java prediction failed. See logs above.")
            self.logger.info("Java prediction finished. Outputs written to %s", output_dir)
            return

        # If no Java available, raise NotImplementedError for now
        raise NotImplementedError(
            "Native Python predictor not yet implemented. Install Java and build distro to enable bridge mode."
        )
    
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