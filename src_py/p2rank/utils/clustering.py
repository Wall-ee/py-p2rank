"""
Advanced clustering algorithms for spatial data - Optimized with scikit-learn
"""
import numpy as np
from typing import List, Callable, Optional, Dict, Union, Tuple
from sklearn.cluster import (
    DBSCAN, KMeans, AgglomerativeClustering, SpectralClustering,
    OPTICS, MeanShift, Birch, GaussianMixture
)
from sklearn.mixture import BayesianGaussianMixture
from sklearn.metrics import (
    silhouette_score, calinski_harabasz_score, davies_bouldin_score,
    adjusted_rand_score, normalized_mutual_info_score
)
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
from scipy.cluster.hierarchy import dendrogram, linkage, fcluster
from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
from ..geom.atoms import Atoms
from ..geom.point import Atom


class ClusteringMetrics:
    """Clustering evaluation metrics"""
    
    @staticmethod
    def silhouette_coefficient(X: np.ndarray, labels: np.ndarray) -> float:
        """Calculate silhouette coefficient"""
        if len(np.unique(labels)) < 2:
            return 0.0
        return silhouette_score(X, labels)
    
    @staticmethod
    def calinski_harabasz_index(X: np.ndarray, labels: np.ndarray) -> float:
        """Calculate Calinski-Harabasz index (higher is better)"""
        if len(np.unique(labels)) < 2:
            return 0.0
        return calinski_harabasz_score(X, labels)
    
    @staticmethod
    def davies_bouldin_index(X: np.ndarray, labels: np.ndarray) -> float:
        """Calculate Davies-Bouldin index (lower is better)"""
        if len(np.unique(labels)) < 2:
            return float('inf')
        return davies_bouldin_score(X, labels)
    
    @staticmethod
    def inertia(X: np.ndarray, labels: np.ndarray) -> float:
        """Calculate within-cluster sum of squares"""
        centers = []
        for label in np.unique(labels):
            cluster_points = X[labels == label]
            centers.append(np.mean(cluster_points, axis=0))
        
        inertia = 0.0
        for i, label in enumerate(labels):
            inertia += np.sum((X[i] - centers[label]) ** 2)
        
        return inertia
    
    @staticmethod
    def adjusted_rand_index(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
        """Calculate Adjusted Rand Index"""
        return adjusted_rand_score(labels_true, labels_pred)
    
    @staticmethod
    def normalized_mutual_information(labels_true: np.ndarray, labels_pred: np.ndarray) -> float:
        """Calculate Normalized Mutual Information"""
        return normalized_mutual_info_score(labels_true, labels_pred)


class OptimalClusterFinder:
    """Find optimal number of clusters using various methods"""
    
    @staticmethod
    def elbow_method(X: np.ndarray, max_k: int = 10, algorithm: str = 'kmeans') -> Tuple[int, np.ndarray]:
        """Find optimal k using elbow method"""
        inertias = []
        k_range = range(1, max_k + 1)
        
        for k in k_range:
            if algorithm == 'kmeans':
                clusterer = KMeans(n_clusters=k, random_state=42, n_init=10)
                clusterer.fit(X)
                inertias.append(clusterer.inertia_)
            else:
                # For other algorithms, calculate inertia manually
                if algorithm == 'agglomerative':
                    clusterer = AgglomerativeClustering(n_clusters=k)
                elif algorithm == 'spectral':
                    clusterer = SpectralClustering(n_clusters=k, random_state=42)
                else:
                    raise ValueError(f"Unsupported algorithm for elbow method: {algorithm}")
                
                labels = clusterer.fit_predict(X)
                inertia = ClusteringMetrics.inertia(X, labels)
                inertias.append(inertia)
        
        # Find elbow using second derivative
        inertias = np.array(inertias)
        if len(inertias) > 2:
            second_derivative = np.diff(inertias, 2)
            optimal_k = np.argmax(second_derivative) + 2  # +2 due to diff operations
        else:
            optimal_k = 2
        
        return optimal_k, inertias
    
    @staticmethod
    def silhouette_method(X: np.ndarray, max_k: int = 10, algorithm: str = 'kmeans') -> Tuple[int, np.ndarray]:
        """Find optimal k using silhouette analysis"""
        silhouette_scores = []
        k_range = range(2, max_k + 1)
        
        for k in k_range:
            if algorithm == 'kmeans':
                clusterer = KMeans(n_clusters=k, random_state=42, n_init=10)
            elif algorithm == 'agglomerative':
                clusterer = AgglomerativeClustering(n_clusters=k)
            elif algorithm == 'spectral':
                clusterer = SpectralClustering(n_clusters=k, random_state=42)
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")
            
            labels = clusterer.fit_predict(X)
            score = ClusteringMetrics.silhouette_coefficient(X, labels)
            silhouette_scores.append(score)
        
        silhouette_scores = np.array(silhouette_scores)
        optimal_k = k_range[np.argmax(silhouette_scores)]
        
        return optimal_k, silhouette_scores
    
    @staticmethod
    def gap_statistic(X: np.ndarray, max_k: int = 10, n_refs: int = 10, algorithm: str = 'kmeans') -> Tuple[int, np.ndarray]:
        """Find optimal k using gap statistic"""
        gaps = []
        results_df = []
        
        for k in range(1, max_k + 1):
            # Cluster original data
            if algorithm == 'kmeans':
                clusterer = KMeans(n_clusters=k, random_state=42, n_init=10)
                clusterer.fit(X)
                original_inertia = clusterer.inertia_
            else:
                if algorithm == 'agglomerative':
                    clusterer = AgglomerativeClustering(n_clusters=k)
                elif algorithm == 'spectral':
                    clusterer = SpectralClustering(n_clusters=k, random_state=42)
                else:
                    raise ValueError(f"Unsupported algorithm: {algorithm}")
                
                labels = clusterer.fit_predict(X)
                original_inertia = ClusteringMetrics.inertia(X, labels)
            
            # Generate reference datasets and cluster them
            ref_inertias = []
            for _ in range(n_refs):
                # Generate random reference data
                random_data = np.random.random_sample(size=X.shape)
                
                if algorithm == 'kmeans':
                    ref_clusterer = KMeans(n_clusters=k, random_state=42, n_init=10)
                    ref_clusterer.fit(random_data)
                    ref_inertias.append(ref_clusterer.inertia_)
                else:
                    if algorithm == 'agglomerative':
                        ref_clusterer = AgglomerativeClustering(n_clusters=k)
                    elif algorithm == 'spectral':
                        ref_clusterer = SpectralClustering(n_clusters=k, random_state=42)
                    
                    ref_labels = ref_clusterer.fit_predict(random_data)
                    ref_inertia = ClusteringMetrics.inertia(random_data, ref_labels)
                    ref_inertias.append(ref_inertia)
            
            # Calculate gap
            gap = np.log(np.mean(ref_inertias)) - np.log(original_inertia)
            gaps.append(gap)
        
        gaps = np.array(gaps)
        # Find first local maximum
        optimal_k = np.argmax(gaps) + 1
        
        return optimal_k, gaps


class HierarchicalClustering:
    """Advanced hierarchical clustering with scipy"""
    
    @staticmethod
    def cluster_with_linkage(X: np.ndarray, method: str = 'ward', 
                           criterion: str = 'distance', threshold: float = 0.5) -> np.ndarray:
        """Hierarchical clustering with various linkage methods"""
        # Calculate linkage matrix
        if method == 'ward':
            linkage_matrix = linkage(X, method='ward')
        else:
            # For other methods, use precomputed distance matrix
            distances = pdist(X, metric='euclidean')
            linkage_matrix = linkage(distances, method=method)
        
        # Form clusters
        clusters = fcluster(linkage_matrix, threshold, criterion=criterion)
        return clusters
    
    @staticmethod
    def plot_dendrogram(X: np.ndarray, method: str = 'ward', figsize: Tuple[int, int] = (12, 8)):
        """Plot dendrogram for hierarchical clustering"""
        if method == 'ward':
            linkage_matrix = linkage(X, method='ward')
        else:
            distances = pdist(X, metric='euclidean')
            linkage_matrix = linkage(distances, method=method)
        
        plt.figure(figsize=figsize)
        dendrogram(linkage_matrix)
        plt.title(f'Hierarchical Clustering Dendrogram ({method})')
        plt.xlabel('Sample Index')
        plt.ylabel('Distance')
        plt.show()


class AdvancedAtomClusterer:
    """Advanced clustering with multiple algorithms and optimization"""
    
    def __init__(self, algorithm: str = 'dbscan', **kwargs):
        """
        Initialize clusterer with specified algorithm.
        
        Args:
            algorithm: Clustering algorithm ('dbscan', 'kmeans', 'agglomerative', 
                      'spectral', 'optics', 'meanshift', 'birch', 'gmm')
            **kwargs: Algorithm-specific parameters
        """
        self.algorithm = algorithm
        self.params = kwargs
        self.clusterer = None
        self.scaler = StandardScaler()
        self.labels_ = None
        self.cluster_centers_ = None
    
    def _get_clusterer(self):
        """Get clusterer instance based on algorithm"""
        if self.algorithm == 'dbscan':
            return DBSCAN(eps=self.params.get('eps', 0.5), 
                         min_samples=self.params.get('min_samples', 5))
        
        elif self.algorithm == 'kmeans':
            return KMeans(n_clusters=self.params.get('n_clusters', 8),
                         random_state=42, n_init=10)
        
        elif self.algorithm == 'agglomerative':
            return AgglomerativeClustering(
                n_clusters=self.params.get('n_clusters', 8),
                linkage=self.params.get('linkage', 'ward'))
        
        elif self.algorithm == 'spectral':
            return SpectralClustering(
                n_clusters=self.params.get('n_clusters', 8),
                random_state=42,
                affinity=self.params.get('affinity', 'rbf'))
        
        elif self.algorithm == 'optics':
            return OPTICS(min_samples=self.params.get('min_samples', 5),
                         max_eps=self.params.get('max_eps', np.inf))
        
        elif self.algorithm == 'meanshift':
            return MeanShift(bandwidth=self.params.get('bandwidth', None))
        
        elif self.algorithm == 'birch':
            return Birch(n_clusters=self.params.get('n_clusters', 8),
                        threshold=self.params.get('threshold', 0.5))
        
        elif self.algorithm == 'gmm':
            return GaussianMixture(
                n_components=self.params.get('n_components', 8),
                random_state=42)
        
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")
    
    def fit_predict(self, X: np.ndarray, normalize: bool = True) -> np.ndarray:
        """Fit clusterer and predict labels"""
        if normalize:
            X = self.scaler.fit_transform(X)
        
        self.clusterer = self._get_clusterer()
        
        if self.algorithm == 'gmm':
            self.labels_ = self.clusterer.fit_predict(X)
            self.cluster_centers_ = self.clusterer.means_
        else:
            self.labels_ = self.clusterer.fit_predict(X)
            
            # Calculate cluster centers for algorithms that don't provide them
            if hasattr(self.clusterer, 'cluster_centers_'):
                self.cluster_centers_ = self.clusterer.cluster_centers_
            else:
                self._calculate_cluster_centers(X)
        
        return self.labels_
    
    def _calculate_cluster_centers(self, X: np.ndarray):
        """Calculate cluster centers manually"""
        unique_labels = np.unique(self.labels_)
        self.cluster_centers_ = []
        
        for label in unique_labels:
            if label == -1:  # Noise points in DBSCAN/OPTICS
                continue
            cluster_points = X[self.labels_ == label]
            center = np.mean(cluster_points, axis=0)
            self.cluster_centers_.append(center)
        
        self.cluster_centers_ = np.array(self.cluster_centers_)
    
    def cluster_atoms(self, atoms: Atoms, normalize: bool = True) -> List[Atoms]:
        """
        Cluster atoms using the specified algorithm.
        
        Args:
            atoms: Atoms to cluster
            normalize: Whether to normalize coordinates
            
        Returns:
            List of Atoms objects, each representing a cluster
        """
        if atoms.empty:
            return []
        
        # Extract coordinates
        coords = np.array([atom.get_coords() for atom in atoms.list])
        
        # Perform clustering
        labels = self.fit_predict(coords, normalize=normalize)
        
        # Group atoms by cluster labels
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:  # Noise points
                clusters[f"noise_{i}"] = [atoms.list[i]]
            else:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(atoms.list[i])
        
        return [Atoms(cluster) for cluster in clusters.values()]
    
    def evaluate_clustering(self, X: np.ndarray) -> Dict[str, float]:
        """Evaluate clustering quality using multiple metrics"""
        if self.labels_ is None:
            raise ValueError("Must fit clusterer first")
        
        metrics = {}
        
        # Skip evaluation for single cluster or all noise
        unique_labels = np.unique(self.labels_)
        if len(unique_labels) < 2 or (len(unique_labels) == 1 and unique_labels[0] == -1):
            return {'silhouette_score': 0.0, 'calinski_harabasz_score': 0.0, 
                   'davies_bouldin_score': float('inf'), 'n_clusters': len(unique_labels)}
        
        try:
            metrics['silhouette_score'] = ClusteringMetrics.silhouette_coefficient(X, self.labels_)
            metrics['calinski_harabasz_score'] = ClusteringMetrics.calinski_harabasz_index(X, self.labels_)
            metrics['davies_bouldin_score'] = ClusteringMetrics.davies_bouldin_index(X, self.labels_)
        except Exception as e:
            print(f"Warning: Could not calculate some metrics: {e}")
            metrics['silhouette_score'] = 0.0
            metrics['calinski_harabasz_score'] = 0.0
            metrics['davies_bouldin_score'] = float('inf')
        
        metrics['n_clusters'] = len(unique_labels) - (1 if -1 in unique_labels else 0)
        metrics['n_noise_points'] = np.sum(self.labels_ == -1)
        
        return metrics
    
    def find_optimal_parameters(self, X: np.ndarray, param_grid: Dict) -> Dict:
        """Find optimal parameters using grid search with silhouette score"""
        best_score = -1
        best_params = None
        best_labels = None
        
        # Generate parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        from itertools import product
        for param_combination in product(*param_values):
            params = dict(zip(param_names, param_combination))
            
            # Create clusterer with these parameters
            temp_clusterer = AdvancedAtomClusterer(self.algorithm, **params)
            
            try:
                labels = temp_clusterer.fit_predict(X)
                
                # Evaluate clustering
                if len(np.unique(labels)) > 1:
                    score = ClusteringMetrics.silhouette_coefficient(X, labels)
                    
                    if score > best_score:
                        best_score = score
                        best_params = params
                        best_labels = labels
            except Exception as e:
                print(f"Warning: Parameter combination {params} failed: {e}")
                continue
        
        # Update clusterer with best parameters
        if best_params:
            self.params.update(best_params)
            self.labels_ = best_labels
        
        return {'best_params': best_params, 'best_score': best_score}


# Legacy classes for backward compatibility
class SingleLinkageClustering:
    """Optimized single linkage clustering implementation"""
    
    @staticmethod
    def cluster(points: List[Atom], min_distance: float) -> List[List[Atom]]:
        """
        Cluster atoms using optimized single linkage clustering.
        
        Args:
            points: List of atoms to cluster
            min_distance: Minimum distance between clusters
            
        Returns:
            List of clusters, each cluster is a list of atoms
        """
        if not points:
            return []
        
        # Extract coordinates for efficient distance computation
        coords = np.array([point.get_coords() for point in points])
        
        # Use scipy's hierarchical clustering for better performance
        distances = pdist(coords, metric='euclidean')
        linkage_matrix = linkage(distances, method='single')
        
        # Form flat clusters
        cluster_labels = fcluster(linkage_matrix, min_distance, criterion='distance')
        
        # Group points by cluster labels
        clusters = {}
        for i, label in enumerate(cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(points[i])
        
        return list(clusters.values())


class AtomClusterer:
    """Improved atom clusterer with multiple algorithm support"""
    
    def __init__(self, algorithm: str = 'single_linkage'):
        """
        Initialize with clustering algorithm.
        
        Args:
            algorithm: 'single_linkage', 'dbscan', or 'advanced'
        """
        self.algorithm = algorithm
        if algorithm == 'single_linkage':
            self.clustering_algo = SingleLinkageClustering()
        elif algorithm == 'dbscan':
            self.clustering_algo = None  # Will use DbscanAtomClusterer
        else:
            self.clustering_algo = AdvancedAtomClusterer(algorithm)
    
    def cluster_atoms(self, atoms: Atoms, min_distance: float, **kwargs) -> List[Atoms]:
        """
        Cluster atoms by distance.
        
        Args:
            atoms: Atoms to cluster
            min_distance: Minimum distance between clusters
            **kwargs: Additional parameters for clustering algorithms
            
        Returns:
            List of Atoms objects, each representing a cluster
        """
        if atoms.empty:
            return []
        
        if self.algorithm == 'single_linkage':
            clusters = self.clustering_algo.cluster(atoms.list, min_distance)
            return [Atoms(cluster) for cluster in clusters]
        elif self.algorithm == 'dbscan':
            clusterer = DbscanAtomClusterer()
            return clusterer.cluster_atoms(atoms, min_distance, kwargs.get('min_samples', 1))
        else:
            # Use advanced clusterer
            return self.clustering_algo.cluster_atoms(atoms, **kwargs)


class DbscanAtomClusterer:
    """Optimized DBSCAN-based atom clustering"""
    
    def cluster_atoms(self, atoms: Atoms, min_distance: float, min_samples: int = 1) -> List[Atoms]:
        """
        Cluster atoms using DBSCAN with optimizations.
        
        Args:
            atoms: Atoms to cluster
            min_distance: Maximum distance between points in the same cluster
            min_samples: Minimum number of samples per cluster
            
        Returns:
            List of Atoms objects, each representing a cluster
        """
        if atoms.empty:
            return []
        
        # Extract coordinates
        coords = np.array([atom.get_coords() for atom in atoms.list])
        
        # Perform DBSCAN clustering with optimized parameters
        dbscan = DBSCAN(eps=min_distance, min_samples=min_samples, algorithm='kd_tree')
        labels = dbscan.fit_predict(coords)
        
        # Group atoms by cluster labels
        clusters = {}
        for i, label in enumerate(labels):
            if label == -1:  # Noise points, create individual clusters
                clusters[f"noise_{i}"] = [atoms.list[i]]
            else:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(atoms.list[i])
        
        return [Atoms(cluster) for cluster in clusters.values()]


# Utility functions for clustering analysis
def compare_clustering_algorithms(X: np.ndarray, algorithms: List[str] = None, 
                                normalize: bool = True) -> Dict[str, Dict]:
    """Compare different clustering algorithms on the same dataset"""
    if algorithms is None:
        algorithms = ['dbscan', 'kmeans', 'agglomerative', 'spectral']
    
    results = {}
    
    for algorithm in algorithms:
        try:
            clusterer = AdvancedAtomClusterer(algorithm)
            labels = clusterer.fit_predict(X, normalize=normalize)
            metrics = clusterer.evaluate_clustering(X)
            
            results[algorithm] = {
                'labels': labels,
                'metrics': metrics,
                'clusterer': clusterer
            }
        except Exception as e:
            print(f"Algorithm {algorithm} failed: {e}")
            results[algorithm] = {'error': str(e)}
    
    return results


def plot_clustering_comparison(X: np.ndarray, results: Dict[str, Dict], 
                             figsize: Tuple[int, int] = (15, 10)):
    """Plot clustering results for comparison"""
    n_algorithms = len([r for r in results.values() if 'labels' in r])
    
    if n_algorithms == 0:
        print("No successful clustering results to plot")
        return
    
    fig, axes = plt.subplots(2, (n_algorithms + 1) // 2, figsize=figsize)
    if n_algorithms == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for i, (algorithm, result) in enumerate(results.items()):
        if 'labels' in result:
            ax = axes[i]
            labels = result['labels']
            
            # Plot 2D projection if data is higher dimensional
            if X.shape[1] > 2:
                # Use first two dimensions for visualization
                scatter = ax.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', alpha=0.7)
            else:
                scatter = ax.scatter(X[:, 0], X[:, 1], c=labels, cmap='viridis', alpha=0.7)
            
            ax.set_title(f'{algorithm.upper()}\n'
                        f'Silhouette: {result["metrics"]["silhouette_score"]:.3f}\n'
                        f'Clusters: {result["metrics"]["n_clusters"]}')
            ax.set_xlabel('Feature 1')
            ax.set_ylabel('Feature 2')
    
    plt.tight_layout()
    plt.show() 