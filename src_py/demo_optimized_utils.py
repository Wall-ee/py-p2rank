#!/usr/bin/env python3
"""
Demo script for optimized P2Rank utils package
Showcases the power of numpy, scipy, and scikit-learn integration
"""

import numpy as np
import matplotlib.pyplot as plt
from p2rank.utils.math_utils import MathUtils
from p2rank.utils.cutils import Cutils
from p2rank.utils.clustering import AdvancedAtomClusterer, compare_clustering_algorithms
from p2rank.utils.kdtree import AtomKdTree, AdvancedSpatialTree, spatial_clustering_analysis
from p2rank.geom.point import Point
from p2rank.geom.atoms import Atoms


def demo_math_utils():
    """Demonstrate enhanced mathematical utilities"""
    print("=== Mathematical Utils Demo ===")
    
    # Generate sample data
    np.random.seed(42)
    data = np.random.normal(5, 2, 1000)
    
    # Basic statistics with numpy optimization
    print(f"Mean: {MathUtils.mean(data):.3f}")
    print(f"Median: {MathUtils.median(data):.3f}")
    print(f"Standard deviation: {MathUtils.stddev(data):.3f}")
    print(f"Variance: {MathUtils.variance(data):.3f}")
    print(f"IQR: {MathUtils.iqr(data):.3f}")
    print(f"Skewness: {MathUtils.skewness(data):.3f}")
    print(f"Kurtosis: {MathUtils.kurtosis(data):.3f}")
    
    # Advanced normalization
    normalized_minmax = MathUtils.min_max_normalize(data[:10])
    normalized_zscore = MathUtils.z_score_normalize(data[:10])
    normalized_robust = MathUtils.robust_normalize(data[:10])
    
    print(f"\nNormalization comparison (first 10 values):")
    print(f"Original: {data[:10]}")
    print(f"Min-Max: {normalized_minmax}")
    print(f"Z-Score: {normalized_zscore}")
    print(f"Robust: {normalized_robust}")
    
    # Outlier detection
    outliers = MathUtils.is_outlier(data, method='iqr')
    print(f"\nOutliers detected (IQR method): {np.sum(outliers)} out of {len(data)}")
    
    # Bootstrap confidence interval
    ci_lower, ci_upper = MathUtils.bootstrap_ci(data, n_bootstrap=1000)
    print(f"95% Bootstrap CI for mean: [{ci_lower:.3f}, {ci_upper:.3f}]")
    
    # Vectorized Gaussian
    x_vals = np.linspace(-3, 3, 100)
    gauss_vals = MathUtils.gauss(x_vals, sigma=1.0)
    print(f"Vectorized Gaussian computed for {len(x_vals)} points")


def demo_collection_utils():
    """Demonstrate enhanced collection utilities"""
    print("\n=== Collection Utils Demo ===")
    
    # Generate sample data
    data = np.random.randint(1, 10, 1000)
    
    # Advanced statistics with numpy
    most_common = Cutils.most_common(data, n=3)
    print(f"Most common values: {most_common}")
    
    frequency_dist = Cutils.frequency_distribution(data)
    print(f"Frequency distribution (first 5): {dict(list(frequency_dist.items())[:5])}")
    
    # Set operations with numpy
    array1 = np.array([1, 2, 3, 4, 5])
    array2 = np.array([4, 5, 6, 7, 8])
    
    intersection = Cutils.intersection([array1, array2])
    union = Cutils.union([array1, array2])
    difference = Cutils.difference(array1, array2)
    
    print(f"\nSet operations:")
    print(f"Array 1: {array1}")
    print(f"Array 2: {array2}")
    print(f"Intersection: {intersection}")
    print(f"Union: {union}")
    print(f"Difference: {difference}")
    
    # Sampling and shuffling
    sample = Cutils.random_sample(list(range(100)), 10, random_state=42)
    print(f"Random sample (10 from 100): {sample}")
    
    # Stratified sampling
    values = list(range(20))
    labels = [i % 3 for i in range(20)]  # 3 classes
    sampled_values, sampled_labels = Cutils.stratified_sample(
        values, labels, n_per_class=2, random_state=42
    )
    print(f"Stratified sample: values={sampled_values}, labels={sampled_labels}")


def demo_spatial_tree():
    """Demonstrate advanced spatial tree functionality"""
    print("\n=== Spatial Tree Demo ===")
    
    # Generate 3D point cloud data
    np.random.seed(42)
    
    # Create two clusters
    cluster1 = np.random.normal([0, 0, 0], 1, (50, 3))
    cluster2 = np.random.normal([10, 10, 10], 1, (50, 3))
    all_coords = np.vstack([cluster1, cluster2])
    
    # Create atoms
    atoms = Atoms([Point(x, y, z) for x, y, z in all_coords])
    
    # Build different types of trees and benchmark
    print("Building and benchmarking different tree algorithms...")
    
    algorithms = ['kd_tree', 'ball_tree', 'brute']
    query_point = [0, 0, 0]
    
    for algorithm in algorithms:
        try:
            tree = AtomKdTree.build(atoms, algorithm=algorithm)
            
            # Test different query types
            nearest = tree.query(query_point, k=5)
            radius_neighbors = tree.query_radius(query_point, radius=3.0)
            
            print(f"{algorithm.upper()}:")
            print(f"  - Found {len(nearest)} nearest neighbors")
            print(f"  - Found {len(radius_neighbors)} neighbors within radius 3.0")
            
            # Get tree statistics
            stats = tree.get_tree_stats()
            print(f"  - Memory usage: {stats['memory_usage_mb']:.2f} MB")
            
        except Exception as e:
            print(f"{algorithm} failed: {e}")
    
    # Spatial clustering analysis
    print("\nSpatial clustering analysis:")
    analysis = spatial_clustering_analysis(atoms, radius=3.0)
    print(f"Total atoms: {analysis['total_atoms']}")
    print(f"Mean neighbors per atom: {analysis['density_stats']['mean_neighbors']:.2f}")
    print(f"Isolated atoms: {analysis['isolated_atoms']}")
    print(f"Dense atoms: {analysis['dense_atoms']}")


def demo_advanced_clustering():
    """Demonstrate advanced clustering algorithms"""
    print("\n=== Advanced Clustering Demo ===")
    
    # Generate clustered data
    np.random.seed(42)
    
    # Create 3 distinct clusters in 3D space
    cluster1 = np.random.normal([0, 0, 0], 0.5, (30, 3))
    cluster2 = np.random.normal([5, 5, 0], 0.5, (30, 3))
    cluster3 = np.random.normal([0, 5, 5], 0.5, (30, 3))
    
    all_coords = np.vstack([cluster1, cluster2, cluster3])
    atoms = Atoms([Point(x, y, z) for x, y, z in all_coords])
    
    # Compare different clustering algorithms
    algorithms = ['dbscan', 'kmeans', 'agglomerative', 'spectral']
    
    print("Comparing clustering algorithms:")
    
    for algorithm in algorithms:
        try:
            if algorithm == 'dbscan':
                clusterer = AdvancedAtomClusterer(algorithm, eps=1.0, min_samples=3)
            else:
                clusterer = AdvancedAtomClusterer(algorithm, n_clusters=3)
            
            clusters = clusterer.cluster_atoms(atoms)
            
            # Evaluate clustering
            coords = np.array([atom.get_coords() for atom in atoms])
            metrics = clusterer.evaluate_clustering(coords)
            
            print(f"{algorithm.upper()}:")
            print(f"  - Number of clusters: {len(clusters)}")
            print(f"  - Silhouette score: {metrics['silhouette_score']:.3f}")
            print(f"  - Calinski-Harabasz score: {metrics['calinski_harabasz_score']:.3f}")
            print(f"  - Davies-Bouldin score: {metrics['davies_bouldin_score']:.3f}")
            
        except Exception as e:
            print(f"{algorithm} failed: {e}")


def demo_advanced_features():
    """Demonstrate additional advanced features"""
    print("\n=== Advanced Features Demo ===")
    
    # Create sample atoms for advanced analysis
    np.random.seed(42)
    coords = np.random.uniform(-10, 10, (100, 3))
    atoms = Atoms([Point(x, y, z) for x, y, z in coords])
    
    # Advanced spatial tree with different metrics
    tree = AdvancedSpatialTree(algorithm='ball_tree', metric='manhattan')
    tree.build(atoms)
    
    print("Advanced spatial tree features:")
    
    # Query pairs within distance
    pairs = tree.query_pairs(r=5.0, output_type='ndarray')
    print(f"Found {len(pairs)} atom pairs within distance 5.0")
    
    # Kernel density estimation
    try:
        densities = tree.kernel_density(bandwidth=2.0)
        print(f"Computed kernel density for {len(densities)} points")
        print(f"Density range: [{np.min(densities):.3f}, {np.max(densities):.3f}]")
    except Exception as e:
        print(f"Kernel density estimation failed: {e}")
    
    # Local outlier factor
    try:
        lof_scores = tree.local_outlier_factor(n_neighbors=10)
        outliers = np.sum(lof_scores > 1.5)
        print(f"Detected {outliers} potential outliers using LOF")
    except Exception as e:
        print(f"LOF computation failed: {e}")
    
    # Demonstrate functional programming helpers
    print("\nFunctional programming helpers:")
    
    # Compose functions
    square = lambda x: x ** 2
    add_one = lambda x: x + 1
    composed = Cutils.compose(square, add_one)
    result = composed(5)  # Should be (5+1)^2 = 36
    print(f"Composed function result: {result}")
    
    # Curry function
    multiply = lambda x, y: x * y
    double = Cutils.curry(multiply, 2)
    print(f"Curried function result: {double(5)}")  # Should be 10


def create_visualization():
    """Create some visualizations to demonstrate capabilities"""
    print("\n=== Creating Visualizations ===")
    
    try:
        # Generate sample data
        np.random.seed(42)
        x = np.linspace(-3, 3, 100)
        
        # Create subplot figure
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        
        # 1. Vectorized Gaussian functions
        gauss1 = MathUtils.gauss(x, sigma=0.5)
        gauss2 = MathUtils.gauss(x, sigma=1.0)
        gauss3 = MathUtils.gauss(x, sigma=1.5)
        
        ax1.plot(x, gauss1, label='σ=0.5')
        ax1.plot(x, gauss2, label='σ=1.0')
        ax1.plot(x, gauss3, label='σ=1.5')
        ax1.set_title('Vectorized Gaussian Functions')
        ax1.legend()
        ax1.grid(True)
        
        # 2. Activation functions
        sigmoid_vals = MathUtils.sigmoid(x)
        tanh_vals = MathUtils.tanh(x)
        relu_vals = MathUtils.relu(x)
        
        ax2.plot(x, sigmoid_vals, label='Sigmoid')
        ax2.plot(x, tanh_vals, label='Tanh')
        ax2.plot(x, relu_vals, label='ReLU')
        ax2.set_title('Activation Functions')
        ax2.legend()
        ax2.grid(True)
        
        # 3. Statistical distribution
        data = np.random.normal(0, 1, 1000)
        ax3.hist(data, bins=30, alpha=0.7, density=True, label='Histogram')
        
        # Overlay theoretical normal distribution
        x_norm = np.linspace(-4, 4, 100)
        y_norm = MathUtils.gauss(x_norm, sigma=1.0)
        ax3.plot(x_norm, y_norm, 'r-', linewidth=2, label='Theoretical')
        ax3.set_title('Statistical Distribution Analysis')
        ax3.legend()
        ax3.grid(True)
        
        # 4. Clustering visualization (2D projection)
        cluster1 = np.random.normal([0, 0], 0.5, (50, 2))
        cluster2 = np.random.normal([3, 3], 0.5, (50, 2))
        cluster3 = np.random.normal([0, 3], 0.5, (50, 2))
        
        all_points = np.vstack([cluster1, cluster2, cluster3])
        colors = ['red'] * 50 + ['blue'] * 50 + ['green'] * 50
        
        ax4.scatter(all_points[:, 0], all_points[:, 1], c=colors, alpha=0.6)
        ax4.set_title('Clustering Example (3 clusters)')
        ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig('p2rank_utils_demo.png', dpi=150, bbox_inches='tight')
        print("Visualization saved as 'p2rank_utils_demo.png'")
        
    except Exception as e:
        print(f"Visualization creation failed: {e}")
        print("This might be due to missing display or matplotlib backend issues")


def main():
    """Run all demonstrations"""
    print("P2Rank Optimized Utils Package Demo")
    print("=" * 50)
    print("This demo showcases the enhanced capabilities using NumPy, SciPy, and scikit-learn")
    
    try:
        demo_math_utils()
        demo_collection_utils()
        demo_spatial_tree()
        demo_advanced_clustering()
        demo_advanced_features()
        create_visualization()
        
        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("The utils package now includes:")
        print("✓ Vectorized mathematical operations")
        print("✓ Advanced statistical functions")
        print("✓ Multiple clustering algorithms")
        print("✓ Optimized spatial data structures")
        print("✓ Scientific computing integration")
        print("✓ Performance optimizations")
        
    except Exception as e:
        print(f"\nDemo failed with error: {e}")
        print("Please ensure all dependencies are installed:")
        print("pip install -r requirements.txt")


if __name__ == "__main__":
    main() 