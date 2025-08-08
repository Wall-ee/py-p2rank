"""
Protein domain object - encapsulates protein structure with ligands
"""
from typing import List, Dict, Optional, Any
import numpy as np
from ..geom.atoms import Atoms
from ..geom.point import Atom


class Ligands:
    """Container for ligand molecules"""
    
    def __init__(self):
        self.ligands: List[Any] = []  # List of Ligand objects
    
    def add(self, ligand: Any):
        """Add ligand to collection"""
        self.ligands.append(ligand)
    
    @property
    def count(self) -> int:
        """Get number of ligands"""
        return len(self.ligands)
    
    @property
    def empty(self) -> bool:
        """Check if no ligands present"""
        return len(self.ligands) == 0


class LoaderParams:
    """Parameters for loading protein structures"""
    
    def __init__(self):
        self.ignore_ligands_switch: bool = False


class Surface:
    """Represents molecular surface (SAS - Solvent Accessible Surface)"""
    
    def __init__(self, points: Optional[Atoms] = None):
        self.points: Atoms = points if points is not None else Atoms()
    
    @property
    def count(self) -> int:
        """Get number of surface points"""
        return self.points.count


class ResidueChain:
    """Represents a chain of residues"""
    
    def __init__(self, chain_id: str):
        self.chain_id = chain_id
        self.residues: List[Any] = []  # List of Residue objects


class Protein:
    """
    Encapsulates protein structure with ligands.
    Core domain object representing a protein with all associated data.
    """
    
    def __init__(self):
        # Basic identification
        self.name: str = ""
        self.file_name: str = ""
        self.short_file_name: str = ""
        self.structure: Optional[Any] = None  # Protein structure object
        
        # Loader parameters
        self.loader_params: Optional[LoaderParams] = None
        
        # Full structure reference (when structure was reduced to single chain)
        self.full_structure: Optional[Any] = None
        
        # Atoms collections
        self.all_atoms: Atoms = Atoms()  # all atoms of structure indexed by id
        self.protein_atoms: Atoms = Atoms()  # protein heavy atoms from chains
        self.exposed_atoms: Atoms = Atoms()  # solvent exposed atoms
        
        # Surfaces
        self.accessible_surface: Optional[Surface] = None  # SAS points
        self.train_surface: Optional[Surface] = None  # surface for sampling training points
        self.train_negatives_surface: Optional[Surface] = None  # surface for sampling negative training points
        
        # Structure type
        self.apo_structure: bool = False
        
        # Ligands
        self.ligands: Ligands = Ligands()  # ligands from structure (HOLO) or paired HOLO
        self.apo_ligands: Optional[Ligands] = None  # original ligands if this is APO structure
        
        # Peptides
        self.peptides: List[ResidueChain] = []
        
        # Residue data (lazy initialization)
        self._residue_chains: Optional[List[ResidueChain]] = None
        self._residue_chains_by_author_id: Optional[Dict[str, ResidueChain]] = None
        self._residues: Optional[Any] = None  # Residues object
        self._exposed_residues: Optional[Any] = None  # Exposed residues
        
        # Secondary data cache
        self.secondary_data: Dict[str, Any] = {}
        
        # Conservation score
        self.conservation_score: Optional[Any] = None
    
    @property
    def residue_chains(self) -> List[ResidueChain]:
        """Get residue chains (lazy initialization)"""
        if self._residue_chains is None:
            self._residue_chains = self._build_residue_chains()
        return self._residue_chains
    
    @property
    def residue_chains_by_author_id(self) -> Dict[str, ResidueChain]:
        """Get residue chains indexed by author ID"""
        if self._residue_chains_by_author_id is None:
            self._residue_chains_by_author_id = {}
            for chain in self.residue_chains:
                self._residue_chains_by_author_id[chain.chain_id] = chain
        return self._residue_chains_by_author_id
    
    @property
    def residues(self) -> Any:
        """Get all residues"""
        if self._residues is None:
            self._residues = self._build_residues()
        return self._residues
    
    @property
    def exposed_residues(self) -> Any:
        """Get exposed residues"""
        if self._exposed_residues is None:
            self._exposed_residues = self._build_exposed_residues()
        return self._exposed_residues
    
    def _build_residue_chains(self) -> List[ResidueChain]:
        """Build residue chains from structure"""
        # This would need BioPython structure parsing
        # For now, return empty list
        return []
    
    def _build_residues(self) -> Any:
        """Build residues collection"""
        # This would combine all residues from all chains
        return None
    
    def _build_exposed_residues(self) -> Any:
        """Build exposed residues collection"""
        # This would filter residues based on solvent exposure
        return None
    
    def has_ligands(self) -> bool:
        """Check if protein has ligands"""
        return not self.ligands.empty
    
    def get_centroid(self) -> Optional[Atom]:
        """Get protein centroid"""
        if self.protein_atoms.empty:
            return None
        return self.protein_atoms.centroid
    
    def clear_secondary_data(self):
        """Clear secondary data cache"""
        self.secondary_data.clear()
    
    def set_secondary_data(self, key: str, value: Any):
        """Set secondary data"""
        self.secondary_data[key] = value
    
    def get_secondary_data(self, key: str) -> Optional[Any]:
        """Get secondary data"""
        return self.secondary_data.get(key)
    
    def __str__(self) -> str:
        return f"Protein(name={self.name}, atoms={self.protein_atoms.count}, ligands={self.ligands.count})"
    
    def __repr__(self) -> str:
        return self.__str__() 