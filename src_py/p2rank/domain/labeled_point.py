"""
Labeled point for training and prediction
"""
from typing import Optional
from ..geom.point import Atom, Point


class LabeledPoint:
    """
    Point with ligandability labels and scores used for training and prediction.
    """
    
    def __init__(self, point: Atom, observed: bool = False, predicted: bool = False, score: float = 0.0):
        """
        Initialize labeled point.
        
        Args:
            point: The 3D point/atom
            observed: True if this point is observed to be ligandable (training label)
            predicted: True if predicted to be ligandable
            score: Ligandability score
        """
        self.point: Atom = point
        self.observed: bool = observed
        self.predicted: bool = predicted
        self.score: float = score
        self.transformed_score: float = score
        
        # Pocket assignment
        self.pocket: int = 0  # pocket number this point belongs to (0 = no pocket)
    
    def get_coords(self):
        """Get coordinates from the underlying point"""
        return self.point.get_coords()
    
    def get_pdb_serial(self) -> int:
        """Get PDB serial from underlying point"""
        return self.point.get_pdb_serial()
    
    def get_element(self) -> str:
        """Get element from underlying point"""
        return self.point.get_element()
    
    def __str__(self) -> str:
        return f"LabeledPoint(score={self.score:.3f}, predicted={self.predicted}, observed={self.observed})"
    
    def __repr__(self) -> str:
        return self.__str__() 