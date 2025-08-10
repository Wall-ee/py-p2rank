"""
Advanced KD-tree implementation for spatial operations - Optimized with scikit-learn/scipy
"""
import numpy as np
from typing import List, Optional, Union, Tuple, TYPE_CHECKING
from sklearn.neighbors import KDTree, BallTree, NearestNeighbors
from sklearn.neighbors._base import NeighborsBase
from scipy.spatial import cKDTree, distance
from scipy.spatial.distance import cdist
import warnings

if TYPE_CHECKING:
    from ..geom.atoms import Atoms
    from ..geom.point import Atom


class AdvancedSpatialTree:
    """Advanced spatial tree with multiple algorithm support"""
    
    def __init__(self, algorithm: str = 'kd_tree', metric: str = 'euclidean', 
                 leaf_size: int = 30, **kwargs):
        """
        Initialize spatial tree with specified algorithm.
        
        Args:
            algorithm: 'kd_tree', 'ball_tree', 'brute', or 'auto'
            metric: Distance metric to use
            leaf_size: Leaf size for tree algorithms
            **kwargs: Additional parameters for the tree
        """
        self.algorithm = algorithm
        self.metric = metric
        self.leaf_size = leaf_size
        self.kwargs = kwargs
        self.tree = None
        self.atoms_list = None
        self.coords = None
        
    def build(self, atoms: 'Atoms') -> 'AdvancedSpatialTree':
        """Build spatial tree from atoms"""
        if atoms.empty:
            raise ValueError("Cannot build tree from empty atoms collection")
        
        self.atoms_list = list(atoms)
        self.coords = np.array([atom.get_coords() for atom in self.atoms_list])
        
        if self.algorithm == 'kd_tree':
            if self.metric != 'euclidean':
                warnings.warn("KDTree only supports euclidean metric, switching to BallTree")
                self.algorithm = 'ball_tree'
        
        if self.algorithm == 'kd_tree':
            self.tree = KDTree(self.coords, leaf_size=self.leaf_size, **self.kwargs)
        elif self.algorithm == 'ball_tree':
            self.tree = BallTree(self.coords, leaf_size=self.leaf_size, 
                               metric=self.metric, **self.kwargs)
        elif self.algorithm == 'brute':
            self.tree = NearestNeighbors(algorithm='brute', metric=self.metric, 
                                       leaf_size=self.leaf_size, **self.kwargs)
            self.tree.fit(self.coords)
        elif self.algorithm == 'auto':
            self.tree = NearestNeighbors(algorithm='auto', metric=self.metric,
                                       leaf_size=self.leaf_size, **self.kwargs)
            self.tree.fit(self.coords)
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
        
        return self
    
    def query_radius(self, center: Union[np.ndarray, List[float]], radius: float,
                    return_distance: bool = False, sort_results: bool = False) -> Union[List['Atom'], Tuple[List['Atom'], List[float]]]:
        """
        Query atoms within radius of center point.
        
        Args:
            center: Center point coordinates  
            radius: Search radius
            return_distance: Whether to return distances
            sort_results: Whether to sort by distance
            
        Returns:
            List of atoms (and distances if requested)
        """
        if self.tree is None:
            raise ValueError("Tree not built yet")
        
        center = np.asarray(center).reshape(1, -1)
        
        if hasattr(self.tree, 'query_radius'):
            # KDTree and BallTree
            indices = self.tree.query_radius(center, r=radius, return_distance=return_distance,
                                           sort_results=sort_results)
            if return_distance:
                indices, distances = indices
                indices = np.asarray(indices[0]).astype(int)
                distances = np.asarray(distances[0]).astype(float)
            else:
                indices = np.asarray(indices[0]).astype(int)
        else:  
            # NearestNeighbors with brute/auto
            indices, distances = self.tree.radius_neighbors(center, radius=radius,
                                                          return_distance=True,
                                                          sort_results=sort_results)
            indices = np.asarray(indices[0]).astype(int)
            distances = np.asarray(distances[0]).astype(float)
            
            if not return_distance:
                distances = None
        
        atoms = [self.atoms_list[int(i)] for i in indices]
        
        if return_distance:
            return atoms, distances.tolist()
        else:
            return atoms
    
    def query(self, center: Union[np.ndarray, List[float]], k: int = 1,
              return_distance: bool = False, dualtree: bool = False) -> Union[List['Atom'], Tuple[List['Atom'], List[float]]]:
        """
        Query k nearest neighbors.
        
        Args:
            center: Center point coordinates
            k: Number of neighbors to return
            return_distance: Whether to return distances
            dualtree: Whether to use dualtree algorithm (if supported)
            
        Returns:
            List of k nearest atoms (and distances if requested)
        """
        if self.tree is None:
            raise ValueError("Tree not built yet")
        
        center = np.asarray(center).reshape(1, -1)
        k = min(k, len(self.atoms_list))
        
        if hasattr(self.tree, 'query'):
            # KDTree and BallTree
            if return_distance:
                distances, indices = self.tree.query(center, k=k, return_distance=True,
                                                   dualtree=dualtree)
            else:
                indices = self.tree.query(center, k=k, return_distance=False,
                                        dualtree=dualtree)
                distances = None
        else:
            # NearestNeighbors
            if return_distance:
                distances, indices = self.tree.kneighbors(center, n_neighbors=k,
                                                        return_distance=True)
            else:
                indices = self.tree.kneighbors(center, n_neighbors=k,
                                             return_distance=False)
                distances = None
        
        indices = indices[0]
        atoms = [self.atoms_list[i] for i in indices]
        
        if return_distance:
            distances = distances[0]
            return atoms, distances.tolist()
        else:
            return atoms
    
    def query_ball_point(self, center: Union[np.ndarray, List[float]], radius: float) -> List['Atom']:
        """Query atoms within ball (sphere) around point"""
        return self.query_radius(center, radius, return_distance=False)
    
    def query_pairs(self, r: float, output_type: str = 'ndarray') -> Union[np.ndarray, List[Tuple[int, int]]]:
        """
        Find all pairs of atoms within distance r.
        
        Args:
            r: Maximum distance
            output_type: 'ndarray' or 'list'
            
        Returns:
            Array or list of index pairs
        """
        if self.tree is None:
            raise ValueError("Tree not built yet")
        
        # For this operation, we'll use scipy's cKDTree which has query_pairs
        ckd_tree = cKDTree(self.coords)
        pairs = ckd_tree.query_pairs(r, output_type=output_type)
        
        return pairs
    
    def count_neighbors(self, center: Union[np.ndarray, List[float]], radius: float) -> int:
        """Count number of neighbors within radius"""
        neighbors = self.query_radius(center, radius)
        return len(neighbors)
    
    def sparse_distance_matrix(self, other: 'AdvancedSpatialTree', max_distance: float):
        """
        Compute sparse distance matrix between two trees.
        
        Args:
            other: Another spatial tree
            max_distance: Maximum distance to include
            
        Returns:
            Sparse distance matrix
        """
        if self.tree is None or other.tree is None:
            raise ValueError("Both trees must be built")
        
        # Use scipy's cKDTree for this operation
        tree1 = cKDTree(self.coords)
        tree2 = cKDTree(other.coords)
        
        return tree1.sparse_distance_matrix(tree2, max_distance)
    
    def kernel_density(self, bandwidth: float, kernel: str = 'gaussian') -> np.ndarray:
        """
        Compute kernel density estimation at tree points.
        
        Args:
            bandwidth: Kernel bandwidth
            kernel: Kernel type ('gaussian', 'tophat', 'epanechnikov', etc.)
            
        Returns:
            Density values at each point
        """
        from sklearn.neighbors import KernelDensity
        
        kde = KernelDensity(bandwidth=bandwidth, kernel=kernel)
        kde.fit(self.coords)
        
        log_density = kde.score_samples(self.coords)
        return np.exp(log_density)
    
    def local_outlier_factor(self, n_neighbors: int = 20) -> np.ndarray:
        """
        Compute Local Outlier Factor for anomaly detection.
        
        Args:
            n_neighbors: Number of neighbors to consider
            
        Returns:
            LOF scores for each point
        """
        from sklearn.neighbors import LocalOutlierFactor
        
        lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination='auto')
        lof.fit(self.coords)
        
        return -lof.negative_outlier_factor_
    
    def voronoi_neighbors(self, atom_idx: int) -> List[int]:
        """
        Get Voronoi neighbors of a point (approximate using Delaunay triangulation).
        
        Args:
            atom_idx: Index of the atom
            
        Returns:
            List of neighbor indices
        """
        try:
            from scipy.spatial import Delaunay
            
            # Create Delaunay triangulation
            tri = Delaunay(self.coords)
            
            # Find simplices containing the point
            neighbors = set()
            for simplex in tri.simplices:
                if atom_idx in simplex:
                    neighbors.update(simplex)
            
            # Remove the point itself
            neighbors.discard(atom_idx)
            return list(neighbors)
            
        except Exception as e:
            # Fall back to k-nearest neighbors
            warnings.warn(f"Voronoi calculation failed, using k-NN: {e}")
            _, indices = self.tree.query(self.coords[atom_idx:atom_idx+1], k=7)  # Approximate
            return indices[0][1:].tolist()  # Exclude the point itself


class AtomKdTree:
    """Optimized KD-tree wrapper for atom operations (backward compatibility)"""
    
    def __init__(self, atoms_coords: np.ndarray, atoms_list: List['Atom'], 
                 algorithm: str = 'kd_tree', **kwargs):
        """Initialize with coordinates and atom list"""
        self.atoms_coords = atoms_coords
        self.atoms_list = atoms_list
        self.spatial_tree = AdvancedSpatialTree(algorithm=algorithm, **kwargs)
        
        # Create dummy atoms object for compatibility
        class DummyAtoms:
            def __init__(self, atoms_list):
                self.list = atoms_list
                self.empty = len(atoms_list) == 0
            
            def __iter__(self):
                return iter(self.list)
            
            def __len__(self):
                return len(self.list)
        
        dummy_atoms = DummyAtoms(atoms_list)
        self.spatial_tree.build(dummy_atoms)
    
    @classmethod
    def build(cls, atoms: 'Atoms', algorithm: str = 'kd_tree', **kwargs) -> 'AtomKdTree':
        """Build KD-tree from atoms collection"""
        if atoms.empty:
            raise ValueError("Cannot build KD-tree from empty atoms collection")
        
        atoms_list = list(atoms)
        atoms_coords = np.array([atom.get_coords() for atom in atoms_list])
        
        return cls(atoms_coords, atoms_list, algorithm=algorithm, **kwargs)
    
    def __len__(self) -> int:
        """Get number of atoms in tree"""
        return len(self.atoms_list)
    
    def size(self) -> int:
        """Get size of tree"""
        return len(self.atoms_list)
    
    def query_radius(self, center: Union[np.ndarray, List[float]], radius: float) -> List['Atom']:
        """Query atoms within radius"""
        return self.spatial_tree.query_radius(center, radius)
    
    def query(self, center: Union[np.ndarray, List[float]], k: int = 1) -> List['Atom']:
        """Query k nearest neighbors"""
        return self.spatial_tree.query(center, k)
    
    def query_with_distances(self, center: Union[np.ndarray, List[float]], 
                           k: int = 1) -> Tuple[List['Atom'], List[float]]:
        """Query k nearest neighbors with distances"""
        return self.spatial_tree.query(center, k, return_distance=True)
    
    def query_radius_with_distances(self, center: Union[np.ndarray, List[float]], 
                                  radius: float) -> Tuple[List['Atom'], List[float]]:
        """Query atoms within radius with distances"""
        return self.spatial_tree.query_radius(center, radius, return_distance=True)
    
    # Additional convenience methods
    def nearest_neighbor(self, center: Union[np.ndarray, List[float]]) -> 'Atom':
        """Get single nearest neighbor"""
        neighbors = self.query(center, k=1)
        return neighbors[0] if neighbors else None
    
    def count_neighbors_in_radius(self, center: Union[np.ndarray, List[float]], radius: float) -> int:
        """Count neighbors within radius"""
        return self.spatial_tree.count_neighbors(center, radius)
    
    def distance_to_nearest(self, center: Union[np.ndarray, List[float]]) -> float:
        """Get distance to nearest atom"""
        atoms, distances = self.query_with_distances(center, k=1)
        return distances[0] if distances else float('inf')
    
    def batch_query(self, centers: np.ndarray, k: int = 1, 
                   return_distance: bool = False) -> Union[List[List['Atom']], Tuple[List[List['Atom']], List[List[float]]]]:
        """
        Query multiple centers at once for better performance.
        
        Args:
            centers: Array of shape (n_queries, n_features)
            k: Number of neighbors per query
            return_distance: Whether to return distances
            
        Returns:
            List of neighbor lists (and distances if requested)
        """
        results = []
        distances_list = [] if return_distance else None
        
        for center in centers:
            if return_distance:
                atoms, distances = self.query_with_distances(center, k)
                results.append(atoms)
                distances_list.append(distances)
            else:
                atoms = self.query(center, k)
                results.append(atoms)
        
        if return_distance:
            return results, distances_list
        else:
            return results
    
    def range_query(self, center: Union[np.ndarray, List[float]], 
                   min_radius: float, max_radius: float) -> List['Atom']:
        """
        Query atoms within a range of distances (annular region).
        
        Args:
            center: Center point
            min_radius: Minimum distance
            max_radius: Maximum distance
            
        Returns:
            List of atoms in the annular region
        """
        all_neighbors = self.query_radius(center, max_radius)
        
        if min_radius <= 0:
            return all_neighbors
        
        # Filter out atoms too close
        center = np.asarray(center)
        filtered = []
        
        for atom in all_neighbors:
            atom_coords = np.asarray(atom.get_coords())
            distance = np.linalg.norm(atom_coords - center)
            if distance >= min_radius:
                filtered.append(atom)
        
        return filtered
    
    def get_tree_stats(self) -> dict:
        """Get statistics about the tree"""
        return {
            'n_atoms': len(self.atoms_list),
            'dimensions': self.atoms_coords.shape[1] if self.atoms_coords.size > 0 else 0,
            'algorithm': self.spatial_tree.algorithm,
            'metric': self.spatial_tree.metric,
            'leaf_size': self.spatial_tree.leaf_size,
            'coords_shape': self.atoms_coords.shape,
            'coords_dtype': self.atoms_coords.dtype,
            'memory_usage_mb': self.atoms_coords.nbytes / (1024 * 1024)
        }


# Utility functions for spatial analysis
def compute_distance_matrix(atoms1: 'Atoms', atoms2: 'Atoms' = None, 
                           metric: str = 'euclidean') -> np.ndarray:
    """
    Compute pairwise distance matrix between atoms.
    
    Args:
        atoms1: First set of atoms
        atoms2: Second set of atoms (if None, compute self-distances)
        metric: Distance metric
        
    Returns:
        Distance matrix
    """
    coords1 = np.array([atom.get_coords() for atom in atoms1])
    
    if atoms2 is None:
        return cdist(coords1, coords1, metric=metric)
    else:
        coords2 = np.array([atom.get_coords() for atom in atoms2])
        return cdist(coords1, coords2, metric=metric)


def find_optimal_tree_algorithm(atoms: 'Atoms', test_queries: int = 100) -> str:
    """
    Find optimal tree algorithm for given data through benchmarking.
    
    Args:
        atoms: Atoms to build tree for
        test_queries: Number of test queries for benchmarking
        
    Returns:
        Name of optimal algorithm
    """
    if atoms.empty or len(atoms) < 10:
        return 'brute'
    
    import time
    
    algorithms = ['kd_tree', 'ball_tree', 'brute']
    coords = np.array([atom.get_coords() for atom in atoms])
    
    # Generate random query points
    np.random.seed(42)
    query_points = np.random.uniform(
        coords.min(axis=0), coords.max(axis=0), 
        size=(test_queries, coords.shape[1])
    )
    
    best_algorithm = 'kd_tree'
    best_time = float('inf')
    
    for algorithm in algorithms:
        try:
            start_time = time.time()
            
            # Build tree
            tree = AtomKdTree.build(atoms, algorithm=algorithm)
            
            # Perform test queries
            for query_point in query_points:
                tree.query(query_point, k=5)
            
            total_time = time.time() - start_time
            
            if total_time < best_time:
                best_time = total_time
                best_algorithm = algorithm
                
        except Exception as e:
            print(f"Algorithm {algorithm} failed: {e}")
            continue
    
    return best_algorithm


def spatial_clustering_analysis(atoms: 'Atoms', radius: float = 5.0) -> dict:
    """
    Perform spatial clustering analysis on atoms.
    
    Args:
        atoms: Atoms to analyze
        radius: Radius for neighborhood analysis
        
    Returns:
        Dictionary with clustering statistics
    """
    if atoms.empty:
        return {'error': 'Empty atoms collection'}
    
    tree = AtomKdTree.build(atoms)
    coords = np.array([atom.get_coords() for atom in atoms])
    
    # Calculate neighborhood sizes
    neighborhood_sizes = []
    for i, atom in enumerate(atoms):
        neighbors = tree.query_radius(atom.get_coords(), radius)
        neighborhood_sizes.append(len(neighbors) - 1)  # Exclude self
    
    neighborhood_sizes = np.array(neighborhood_sizes)
    
    # Calculate density statistics
    density_stats = {
        'mean_neighbors': float(np.mean(neighborhood_sizes)),
        'std_neighbors': float(np.std(neighborhood_sizes)),
        'min_neighbors': int(np.min(neighborhood_sizes)),
        'max_neighbors': int(np.max(neighborhood_sizes)),
        'median_neighbors': float(np.median(neighborhood_sizes))
    }
    
    # Find isolated atoms (few neighbors)
    isolated_threshold = max(1, int(np.percentile(neighborhood_sizes, 10)))
    isolated_atoms = np.sum(neighborhood_sizes <= isolated_threshold)
    
    # Find dense regions (many neighbors)  
    dense_threshold = int(np.percentile(neighborhood_sizes, 90))
    dense_atoms = np.sum(neighborhood_sizes >= dense_threshold)
    
    return {
        'total_atoms': len(atoms),
        'radius': radius,
        'density_stats': density_stats,
        'isolated_atoms': int(isolated_atoms),
        'dense_atoms': int(dense_atoms),
        'isolation_threshold': isolated_threshold,
        'density_threshold': dense_threshold,
        'neighborhood_histogram': np.histogram(neighborhood_sizes, bins=10)[0].tolist()
    } 