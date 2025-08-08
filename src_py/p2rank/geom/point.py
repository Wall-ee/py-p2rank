"""
Lightweight implementation of 3D point with no properties.
"""
import numpy as np
from typing import List, Union, Optional
from abc import ABC, abstractmethod


class Atom(ABC):
    """Abstract base class for atom-like objects"""
    
    @abstractmethod
    def get_coords(self) -> np.ndarray:
        """Get 3D coordinates"""
        pass
    
    @abstractmethod
    def get_pdb_serial(self) -> int:
        """Get PDB serial number"""
        pass
    
    @abstractmethod
    def get_element(self) -> str:
        """Get element symbol"""
        pass


class Point(Atom):
    """Lightweight implementation of Atom representing just 3D point with no properties."""
    
    def __init__(self, x: Union[float, np.ndarray, List[float]] = 0.0, 
                 y: Optional[float] = None, z: Optional[float] = None):
        """
        Initialize point with coordinates.
        
        Args:
            x: Either x-coordinate (if y,z provided) or array of [x,y,z] coordinates
            y: y-coordinate (optional if x is array)
            z: z-coordinate (optional if x is array)
        """
        if isinstance(x, (list, np.ndarray)) and y is None and z is None:
            self.coords = np.array(x, dtype=np.float64)
        elif y is not None and z is not None:
            self.coords = np.array([x, y, z], dtype=np.float64)
        else:
            self.coords = np.zeros(3, dtype=np.float64)
    
    def copy(self) -> 'Point':
        """Create a copy of this point"""
        return Point(self.coords.copy())
    
    def get_coords(self) -> np.ndarray:
        """Get 3D coordinates as numpy array"""
        return self.coords
    
    def get_element(self) -> str:
        """Get element symbol (default C for points)"""
        return "C"
    
    def get_pdb_serial(self) -> int:
        """Get PDB serial number (default 0 for points)"""
        return 0
    
    def dist(self, other: 'Atom') -> float:
        """Calculate distance to another atom/point"""
        other_coords = other.get_coords()
        diff = self.coords - other_coords
        return np.sqrt(np.sum(diff * diff))
    
    def set_xyz(self, x: float, y: float, z: float):
        """Set coordinates"""
        self.coords[0] = x
        self.coords[1] = y
        self.coords[2] = z
    
    @property
    def x(self) -> float:
        """X coordinate"""
        return self.coords[0]
    
    @property
    def y(self) -> float:
        """Y coordinate"""
        return self.coords[1]
    
    @property
    def z(self) -> float:
        """Z coordinate"""
        return self.coords[2]
    
    @classmethod  
    def of(cls, x: float, y: float, z: float) -> 'Point':
        """Create point with coordinates"""
        return cls(x, y, z)
    
    @classmethod
    def copy_of(cls, atom: Atom) -> 'Point':
        """Create point from atom coordinates"""
        return cls(atom.get_coords().copy())
    
    def __str__(self) -> str:
        return f"Point({self.x:.3f}, {self.y:.3f}, {self.z:.3f})"
    
    def __repr__(self) -> str:
        return self.__str__() 