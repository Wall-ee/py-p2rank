"""
Global parameters for P2Rank program

This file contains all configurable parameters for the P2Rank algorithm.
"""
import os
import multiprocessing
from typing import Optional


class Params:
    """
    Holds all global parameters of the program.
    
    This class is the main source of parameter description/documentation.
    """
    
    # Singleton pattern
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize parameters with default values"""
        
        # === Runtime Parameters ===
        
        # Dataset and output directories
        self.dataset_base_dir: Optional[str] = None
        self.output_base_dir: Optional[str] = None
        
        # Model settings
        self.model: str = "default"  # Location of pre-trained serialized model
        
        # Random seed
        self.seed: int = 42
        
        # Parallel execution
        self.parallel: bool = True
        self.threads: int = multiprocessing.cpu_count() + 1
        self.r_threads: int = 2
        self.r_generate_plots: bool = True
        self.r_plot_stddevs: bool = False
        self.crossval_threads: int = 1
        
        # Logging
        self.log_level: str = "INFO"
        self.log_to_console: bool = True
        self.log_to_file: bool = True
        self.zip_log_file: bool = False
        self.stdout_timestamp: str = ""
        
        # === Model Parameters ===
        
        # Prediction parameters
        self.pred_protein_surface_cutoff: float = 4.5
        self.pred_min_cluster_size: int = 3
        self.pred_clustering_dist: float = 5.0
        self.pred_point_threshold: float = 0.5
        self.extended_pocket_cutoff: float = 0.0
        
        # Scoring parameters
        self.balance_density: bool = False
        self.balance_density_radius: float = 2.0
        self.score_point_limit: int = 0
        self.score_pockets_by: str = "default"  # "default", "conservation", "combi"
        
        # Surface and tessellation
        self.tessellation: str = "connolly"
        self.train_tessellation: str = "connolly"
        self.train_negatives_tessellation: str = "connolly"
        self.solvent_radius: float = 1.4
        self.probe_radius: float = 1.4
        
        # Feature extraction
        self.neighbourhood_radius: float = 8.0
        self.atom_table_features: bool = True
        self.extra_features: bool = True
        self.feat_atom_types: bool = True
        
        # Machine learning
        self.classifier: str = "FastRandomForest"
        self.rf_trees: int = 100
        self.rf_depth: int = 20
        self.rf_features: int = 0  # 0 = sqrt(n_features)
        
        # Training
        self.train_protein_limit: int = 0
        self.train_positives_limit: int = 0
        self.train_negatives_limit: int = 0
        self.positive_sample_ratio: float = 1.0
        self.negative_sample_ratio: float = 1.0
        
        # Prediction settings
        self.predict_residues: bool = False
        self.ligand_derived_point_labeling: bool = True
        
        # Score transformers
        self.zscoretp_transformer: Optional[str] = None
        self.probatp_transformer: Optional[str] = None
        
        # Conservation
        self.conservation_dir: Optional[str] = None
        self.pdb_to_uniprot_dir: Optional[str] = None
        
        # Visualization
        self.visualizations: bool = True
        self.vis_copy_proteins: bool = True
        
        # Performance
        self.cache_datasets: bool = True
        self.clear_sec_caches: bool = False
        self.delete_models: bool = False
        
        # Debugging
        self.log_cases: bool = False
        self.debug_mode: bool = False
        self.fail_fast: bool = False
        
        # Install directory (set at runtime)
        self.install_dir: Optional[str] = None
    
    @classmethod
    def get_instance(cls) -> 'Params':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def update_from_dict(self, config_dict: dict):
        """Update parameters from dictionary"""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def update_from_command_line(self, args: dict):
        """Update parameters from command line arguments"""
        for key, value in args.items():
            if hasattr(self, key):
                # Handle type conversion based on existing parameter type
                current_value = getattr(self, key)
                if isinstance(current_value, bool):
                    setattr(self, key, str(value).lower() in ('true', '1', 'yes', 'on'))
                elif isinstance(current_value, int):
                    setattr(self, key, int(value))
                elif isinstance(current_value, float):
                    setattr(self, key, float(value))
                else:
                    setattr(self, key, value)
    
    def validate(self):
        """Validate parameter values"""
        if self.threads < 1:
            self.threads = 1
        
        if self.pred_clustering_dist <= 0:
            raise ValueError("pred_clustering_dist must be positive")
        
        if self.pred_min_cluster_size < 1:
            raise ValueError("pred_min_cluster_size must be at least 1")
    
    def __str__(self) -> str:
        """String representation of parameters"""
        return f"Params(model={self.model}, threads={self.threads}, seed={self.seed})"
    
    def __repr__(self) -> str:
        return self.__str__()


# Global instance
PARAMS = Params.get_instance() 