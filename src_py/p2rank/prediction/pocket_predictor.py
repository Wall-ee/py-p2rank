"""
Pocket Predictor - core of P2RANK algorithm

Calculates pockets from list of SAS points with ligandability scores.
"""
import logging
from typing import List, Optional
import numpy as np

from ..domain.protein import Protein
from ..domain.pocket import Pocket, PrankPocket
from ..domain.labeled_point import LabeledPoint
from ..geom.atoms import Atoms
from ..geom.point import Point, Atom
from ..utils.clustering import AtomClusterer
from ..program.params import Params


logger = logging.getLogger(__name__)


class PointScoreCalculator:
    """Calculator for point scores and transformations"""
    
    def transform_score(self, score: float) -> float:
        """Transform raw score (placeholder implementation)"""
        return score


class ScoreTransformer:
    """Score transformation utilities"""
    
    def __init__(self, transform_type: str = "identity"):
        self.transform_type = transform_type
    
    def transform_score(self, score: float) -> float:
        """Transform score based on type"""
        if self.transform_type == "identity":
            return score
        # Add other transformation types as needed
        return score
    
    @classmethod
    def load(cls, transformer_path: Optional[str]) -> Optional['ScoreTransformer']:
        """Load score transformer from path"""
        if transformer_path is None:
            return None
        # Placeholder implementation
        return cls()


class PocketPredictor:
    """
    Calculates pockets from list of SAS points with ligandability scores.
    Core of P2RANK algorithm.
    """
    
    def __init__(self, params: Optional[Params] = None):
        """Initialize pocket predictor with parameters"""
        self.params = params or Params()
        self.point_score_calculator = PointScoreCalculator()
        
        # Algorithm parameters
        self.POCKET_PROT_SURFACE_CUTOFF = self.params.pred_protein_surface_cutoff
        self.MIN_CLUSTER_SIZE = self.params.pred_min_cluster_size
        self.EXTENDED_POCKET_CUTOFF = self.params.extended_pocket_cutoff
        self.CLUSTERING_DIST = self.params.pred_clustering_dist
        self.POINT_THRESHOLD = self.params.pred_point_threshold
        self.BALANCE_POINT_DENSITY = self.params.balance_density
        self.BALANCE_RADIUS = self.params.balance_density_radius
        self.SCORE_POINT_LIMIT = self.params.score_point_limit
    
    def _score_point(self, point: LabeledPoint, surface_points: Atoms) -> float:
        """
        Score a single point.
        
        Args:
            point: The labeled point to score
            surface_points: All surface points for density balancing
            
        Returns:
            Calculated score for the point
        """
        score = point.transformed_score
        
        if self.BALANCE_POINT_DENSITY:
            # Count nearby points for density balancing
            nearby_points = surface_points.cutout_sphere(point, self.BALANCE_RADIUS)
            pts = nearby_points.count
            if pts > 0:
                score = score / pts
        
        return score
    
    def _admit_point(self, point: LabeledPoint) -> bool:
        """
        Determine if a point should be considered ligandable.
        
        Args:
            point: The labeled point to check
            
        Returns:
            True if point is predicted to be ligandable
        """
        return point.predicted
    
    def _pocket_score(self, pocket_points: Atoms, all_sas_points: Atoms, 
                     protein: Protein, pocket_surface_atoms: Atoms) -> float:
        """
        Calculate score for a pocket.
        
        Args:
            pocket_points: Points belonging to the pocket
            all_sas_points: All SAS points for scoring
            protein: The protein structure
            pocket_surface_atoms: Surface atoms near the pocket
            
        Returns:
            Calculated pocket score
        """
        score = 0.0
        
        try:
            # Convert to labeled points
            sas_points = []
            for atom in pocket_points:
                if isinstance(atom, LabeledPoint):
                    sas_points.append(atom)
            
            # Score each point
            for point in sas_points:
                point.score = self._score_point(point, all_sas_points)
            
            # Sort by score (descending)
            sas_points.sort(key=lambda p: p.score, reverse=True)
            
            # Limit scoring points if specified
            scoring_points = sas_points
            if self.SCORE_POINT_LIMIT > 0:
                scoring_points = sas_points[:self.SCORE_POINT_LIMIT]
            
            # Sum scores
            score = sum(point.score for point in scoring_points)
            
            # Apply conservation scoring if available
            if (self.params.score_pockets_by == "conservation" or 
                self.params.score_pockets_by == "combi"):
                conservation_score = protein.conservation_score
                if conservation_score is not None:
                    # Calculate average conservation (placeholder implementation)
                    avg_conservation = 1.0  # This would need proper implementation
                    
                    if self.params.score_pockets_by == "conservation":
                        score = avg_conservation
                    else:  # combi
                        score *= avg_conservation
        
        except Exception as e:
            logger.warning(f"Could not score pockets using [{self.params.score_pockets_by}]: {e}")
        
        return score
    
    def predict_pockets(self, all_labeled_points: List[LabeledPoint], 
                       protein: Protein) -> List[Pocket]:
        """
        Predict pockets from labeled points.
        
        Args:
            all_labeled_points: List of points with predicted ligandability
            protein: The protein structure
            
        Returns:
            List of predicted pockets, sorted by score
        """
        # Create atoms collection with KD tree
        labeled_points = Atoms(all_labeled_points).with_kd_tree()
        
        # Filter ligandable points
        ligandable_points = [point for point in all_labeled_points 
                           if self._admit_point(point)]
        
        # Cluster ligandable points
        clusterer = AtomClusterer()
        clusters = clusterer.cluster_atoms(Atoms(ligandable_points), self.CLUSTERING_DIST)
        
        # Filter clusters by minimum size
        filtered_clusters = [cluster for cluster in clusters 
                           if cluster.count >= self.MIN_CLUSTER_SIZE]
        
        logger.info("PREDICTING POCKETS.... ====================================")
        logger.info(f"SAS POINTS: {labeled_points.count}")
        logger.info(f"LIGANDABLE POINTS: {len(ligandable_points)}")
        logger.info(f"CLUSTERS: {len(clusters)}")
        logger.info(f"FILTERED CLUSTERS: {len(filtered_clusters)}")
        
        # Load score transformers
        zscore_tp_transformer = ScoreTransformer.load(self.params.zscoretp_transformer)
        proba_tp_transformer = ScoreTransformer.load(self.params.probatp_transformer)
        
        # Create pockets from clusters
        pockets = []
        for cluster_points in filtered_clusters:
            # Determine pocket points (with extension if specified)
            pocket_points = cluster_points
            if self.EXTENDED_POCKET_CUTOFF > 0:
                extended_pocket_points = labeled_points.cutout_shell(
                    cluster_points, self.EXTENDED_POCKET_CUTOFF)
                pocket_points = extended_pocket_points
            
            # Find surface atoms near pocket
            pocket_surface_atoms = protein.exposed_atoms.cutout_shell(
                pocket_points, self.POCKET_PROT_SURFACE_CUTOFF)
            
            # Calculate pocket score
            score = self._pocket_score(pocket_points, labeled_points, 
                                     protein, pocket_surface_atoms)
            
            # Create SAS points collection
            pocket_sas_points = Atoms([point.point for point in pocket_points.list 
                                     if isinstance(point, LabeledPoint)])
            
            # Create pocket
            pocket = PrankPocket(
                centroid=cluster_points.centroid,
                score=score,
                sas_points=pocket_sas_points,
                labeled_points=pocket_points.as_list()
            )
            
            pocket.surface_atoms = pocket_surface_atoms
            pocket.aux_info.sample_points = cluster_points.count
            pocket.cache["count"] = cluster_points.count
            
            # Apply score transformations
            if zscore_tp_transformer is not None:
                pocket.aux_info.z_score_tp = zscore_tp_transformer.transform_score(score)
            if proba_tp_transformer is not None:
                pocket.aux_info.proba_tp = proba_tp_transformer.transform_score(score)
            
            pockets.append(pocket)
        
        # Sort pockets by score (descending)
        pockets.sort(key=lambda p: p.new_score, reverse=True)
        
        # Assign ranks and update labeled points
        for i, pocket in enumerate(pockets, 1):
            # Update labeled points with pocket assignment
            for lp in pocket.labeled_points:
                if isinstance(lp, LabeledPoint):
                    lp.pocket = i
            
            pocket.name = f"pocket{i}"
            pocket.rank = i
            
            count = pocket.cache.get("count", 0)
            score_val = pocket.new_score
            surf_atoms = pocket.surface_atoms.count
            
            logger.info(f"pocket{i:2d} -  surf_atoms: {surf_atoms:3d}   "
                       f"points: {count:3d}   score: {score_val:6.1f}")
        
        return pockets 