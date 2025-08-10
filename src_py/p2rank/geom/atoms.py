"""
List of atoms with additional properties and operations
"""
import numpy as np
from typing import List, Dict, Optional, Iterator, Collection, Union
from abc import ABC
from .point import Atom, Point
from ..utils.kdtree import AtomKdTree


class Atoms:
    """List of atoms with additional properties"""
    
    KD_TREE_THRESHOLD = 15
    
    def __init__(self, atoms: Optional[Union[List[Atom], Collection[Atom], 'Atoms']] = None):
        """
        Initialize Atoms container.
        
        Args:
            atoms: List/collection of atoms or another Atoms object
        """
        if atoms is None:
            self.list: List[Atom] = []
        elif isinstance(atoms, Atoms):
            self.list = atoms.list
        elif isinstance(atoms, (list, tuple)):
            self.list = list(atoms)
        else:
            self.list = list(atoms)
        
        # Lazy fields
        self._index: Optional[Dict[int, Atom]] = None
        self._kd_tree: Optional[AtomKdTree] = None
        self._centroid: Optional[Point] = None
        self._center_of_mass: Optional[Point] = None
    
    @classmethod
    def copy_points(cls, *atoms: Atom) -> 'Atoms':
        """Copy atoms and fill with points"""
        result = cls()
        for atom in atoms:
            result.add(Point(atom.get_coords()))
        return result
    
    def as_list(self) -> List[Atom]:
        """Get internal list (allows casting to subtypes)"""
        return self.list
    
    def to_points(self) -> 'Atoms':
        """Convert to Atoms containing Point objects"""
        return self.copy_points(*self.list)
    
    def get_indexes(self) -> List[int]:
        """Get PDB serial numbers of all atoms"""
        return [atom.get_pdb_serial() for atom in self.list]
    
    def with_index(self) -> 'Atoms':
        """Build index if not already built"""
        if self._index is None:
            self._index = {}
            for atom in self.list:
                self._index[atom.get_pdb_serial()] = atom
        return self
    
    def with_kd_tree_conditional(self) -> 'Atoms':
        """Conditionally build KD tree based on threshold"""
        if self.count > self.KD_TREE_THRESHOLD:
            if self._kd_tree is None or len(self._kd_tree) != self.count:
                self.build_kd_tree()
        return self
    
    def with_kd_tree(self) -> 'Atoms':
        """Build KD tree if not already built"""
        if self._kd_tree is None:
            self.build_kd_tree()
        return self
    
    def build_kd_tree(self) -> 'Atoms':
        """Build KD tree for spatial queries"""
        self._kd_tree = AtomKdTree.build(self)
        return self
    
    def get_kd_tree(self) -> Optional[AtomKdTree]:
        """Get KD tree"""
        return self._kd_tree
    
    def __iter__(self) -> Iterator[Atom]:
        """Iterate over atoms"""
        return iter(self.list)
    
    def __len__(self) -> int:
        """Get number of atoms"""
        return len(self.list)
    
    @property
    def count(self) -> int:
        """Get number of atoms"""
        return len(self.list)
    
    @property
    def empty(self) -> bool:
        """Check if atoms list is empty"""
        return len(self.list) == 0
    
    def contains(self, atom: Atom) -> bool:
        """Check if atom is in collection (based on PDB serial)"""
        self.with_index()
        return atom.get_pdb_serial() in self._index
    
    def get_by_id(self, pdb_serial: int) -> Optional[Atom]:
        """Get atom by PDB serial"""
        self.with_index()
        return self._index.get(pdb_serial)
    
    def add(self, atom: Atom):
        """Add atom to collection"""
        self.list.append(atom)
        # Clear cached values
        self._index = None
        self._kd_tree = None
        self._centroid = None
        self._center_of_mass = None
    
    def add_all(self, atoms: Collection[Atom]):
        """Add all atoms from collection"""
        self.list.extend(atoms)
        # Clear cached values
        self._index = None
        self._kd_tree = None
        self._centroid = None
        self._center_of_mass = None
    
    def remove(self, atom: Atom) -> bool:
        """Remove atom from collection"""
        try:
            self.list.remove(atom)
            # Clear cached values
            self._index = None
            self._kd_tree = None
            self._centroid = None
            self._center_of_mass = None
            return True
        except ValueError:
            return False
    
    def get_centroid(self) -> Point:
        """Calculate centroid of all atoms"""
        if self._centroid is None:
            if self.empty:
                self._centroid = Point()
            else:
                coords = np.array([atom.get_coords() for atom in self.list])
                centroid_coords = np.mean(coords, axis=0)
                self._centroid = Point(centroid_coords)
        return self._centroid
    
    @property
    def centroid(self) -> Point:
        """Get centroid"""
        return self.get_centroid()
    
    def cutout_sphere(self, center: Union[Atom, Point], radius: float) -> 'Atoms':
        """Get atoms within sphere"""
        result = Atoms()
        center_coords = center.get_coords() if hasattr(center, 'get_coords') else center.coords
        center_coords = np.asarray(center_coords, dtype=float)
        
        for atom in self.list:
            atom_coords = np.asarray(atom.get_coords(), dtype=float)
            distance = np.linalg.norm(atom_coords - center_coords)
            if distance <= radius:
                result.add(atom)
        
        return result
    
    def cutout_shell(self, atoms: 'Atoms', radius: float) -> 'Atoms':
        """Get atoms within shell distance from any atom in the given set"""
        result = Atoms()
        
        for atom in self.list:
            for shell_atom in atoms:
                atom_coords = np.asarray(atom.get_coords(), dtype=float)
                shell_coords = np.asarray(shell_atom.get_coords(), dtype=float)
                distance = np.linalg.norm(atom_coords - shell_coords)
                if distance <= radius:
                    result.add(atom)
                    break
        
        return result
    
    def __str__(self) -> str:
        return f"Atoms(count={self.count})"
    
    def __repr__(self) -> str:
        return self.__str__() 