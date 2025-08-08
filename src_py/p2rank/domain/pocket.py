"""
Pocket domain object
"""
from abc import ABC
from typing import List, Optional, Dict, Any
import numpy as np
from ..geom.atoms import Atoms
from ..geom.point import Atom


class PocketStats:
    """Pocket statistics"""
    
    def __init__(self):
        self.pocket_score: float = 0.0
        self.real_volume_approx: float = 0.0


class AuxInfo:
    """Auxiliary information for pockets"""
    
    def __init__(self):
        self.sample_points: int = 0
        self.raw_new_score: float = 0.0
        self.z_score_tp: float = 0.0
        self.proba_tp: float = 0.0


class Pocket(ABC):
    """Abstract base class for protein pockets"""
    
    def __init__(self):
        self.name: str = "pocket"
        self.surface_atoms: Atoms = Atoms()
        self.centroid: Optional[Atom] = None
        self.sas_points: Optional[Atoms] = None
        self.labeled_points: Optional[List[Any]] = None  # List of LabeledPoint
        
        # Ranking
        self.rank: int = 0  # original rank, starting with 1
        self.new_rank: int = 0  # rank after rescoring
        
        # Scoring
        self.score: float = float('nan')
        self.new_score: float = float('nan')
        
        # Additional data
        self.stats: PocketStats = PocketStats()
        self.aux_info: AuxInfo = AuxInfo()
        self.cache: Dict[str, Any] = {}
        
        # Private fields
        self._residues: Optional[List[Any]] = None  # List of Residue objects
    
    def get_sas_points(self) -> Optional[Atoms]:
        """Get SAS points defined by the pocket"""
        return self.sas_points
    
    def get_centroid(self) -> Optional[Atom]:
        """Get pocket centroid"""
        return self.centroid
    
    def set_centroid(self, centroid: Atom):
        """Set pocket centroid"""
        self.centroid = centroid
    
    def get_residues(self) -> List[Any]:
        """Get residues associated with this pocket"""
        if self._residues is None:
            if self.surface_atoms is None or self.surface_atoms.empty:
                self._residues = []
            else:
                # This would need to be implemented when we have Residue class
                # self._residues = self.surface_atoms.distinct_groups_sorted.collect { new Residue(it) }
                self._residues = []
        return self._residues
    
    @property
    def residues(self) -> List[Any]:
        """Get residues property"""
        return self.get_residues()
    
    def __str__(self) -> str:
        return f"pocket rank:{self.rank} surfaceAtoms:{self.surface_atoms.count}"
    
    def __repr__(self) -> str:
        return self.__str__()


class PrankPocket(Pocket):
    """P2Rank specific pocket implementation"""
    
    def __init__(self, centroid: Atom, score: float, sas_points: Atoms, labeled_points: List[Any]):
        """
        Initialize PrankPocket.
        
        Args:
            centroid: Pocket centroid
            score: Pocket score
            sas_points: SAS points belonging to pocket
            labeled_points: Labeled points used for scoring
        """
        super().__init__()
        self.centroid = centroid
        self.score = score
        self.new_score = score
        self.sas_points = sas_points
        self.labeled_points = labeled_points 