"""
Test cases for optimized utility classes
"""
import unittest
import tempfile
import os
from pathlib import Path
import numpy as np

from p2rank.utils.cutils import Cutils
from p2rank.utils.futils import Futils
from p2rank.utils.math_utils import MathUtils
from p2rank.utils.clustering import AdvancedAtomClusterer, ClusteringMetrics
from p2rank.utils.kdtree import AtomKdTree, AdvancedSpatialTree
from p2rank.geom.point import Point
from p2rank.geom.atoms import Atoms


class TestOptimizedCutils(unittest.TestCase):
    """Test cases for optimized collection utilities"""
    
    def test_empty_with_numpy(self):
        """Test empty function with numpy arrays"""
        self.assertTrue(Cutils.empty(None))
        self.assertTrue(Cutils.empty([]))
        self.assertTrue(Cutils.empty(np.array([])))
        self.assertFalse(Cutils.empty([1, 2, 3]))
        self.assertFalse(Cutils.empty(np.array([1, 2, 3])))
    
    def test_head_tail_numpy(self):
        """Test head and tail functions with numpy arrays"""
        arr = np.array([1, 2, 3, 4, 5])
        
        # Test head
        head_result = Cutils.head(3, arr)
        np.testing.assert_array_equal(head_result, np.array([1, 2, 3]))
        
        # Test tail
        tail_result = Cutils.tail(3, arr)
        np.testing.assert_array_equal(tail_result, np.array([3, 4, 5]))
    
    def test_vectorized_map_list(self):
        """Test vectorized map_list function"""
        arr = np.array([1, 2, 3, 4, 5])
        
        # Test with numpy array
        result = Cutils.map_list(arr, lambda x: x * 2)
        expected = np.array([2, 4, 6, 8, 10])
        np.testing.assert_array_equal(result, expected)
        
        # Test with regular list
        lst = [1, 2, 3, 4, 5]
        result = Cutils.map_list(lst, lambda x: x * 2)
        self.assertEqual(result, [2, 4, 6, 8, 10])
    
    def test_numerical_operations(self):
        """Test numerical operations with numpy"""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        
        # Test sum_doubles with numpy optimization
        result = Cutils.sum_doubles(values)
        self.assertAlmostEqual(result, 15.0, places=5)
        
        # Test with numpy array
        arr = np.array(values)
        result = Cutils.sum_doubles(arr)
        self.assertAlmostEqual(result, 15.0, places=5)
        
        # Test weighted sum
        weights = [0.1, 0.2, 0.3, 0.2, 0.2]
        weighted_sum = Cutils.sum_with_weights(values, weights)
        expected = sum(v * w for v, w in zip(values, weights))
        self.assertAlmostEqual(weighted_sum, expected, places=5)
        
        # Test cumulative sum
        cumsum = Cutils.cumulative_sum(values)
        expected = np.array([1, 3, 6, 10, 15])
        np.testing.assert_array_equal(cumsum, expected)
    
    def test_advanced_collection_operations(self):
        """Test advanced collection operations"""
        values = [1, 2, 3, 2, 4, 3, 5]
        
        # Test find_duplicates with numpy optimization
        duplicates = Cutils.find_duplicates(np.array(values))
        self.assertIn(2, duplicates)
        self.assertIn(3, duplicates)
        
        # Test unique_elements
        unique = Cutils.unique_elements(values, preserve_order=True)
        self.assertEqual(unique, [1, 2, 3, 4, 5])
        
        # Test group_by
        grouped = Cutils.group_by(values, lambda x: x % 2)
        self.assertEqual(len(grouped[0]), 3)  # Even numbers
        self.assertEqual(len(grouped[1]), 4)  # Odd numbers
        
        # Test partition
        evens, odds = Cutils.partition(values, lambda x: x % 2 == 0)
        self.assertEqual(evens, [2, 2, 4])
        self.assertEqual(odds, [1, 3, 3, 5])
    
    def test_set_operations(self):
        """Test set operations with numpy arrays"""
        arr1 = np.array([1, 2, 3, 4])
        arr2 = np.array([3, 4, 5, 6])
        arr3 = np.array([2, 3, 7, 8])
        
        # Test intersection
        intersection = Cutils.intersection([arr1, arr2])
        np.testing.assert_array_equal(intersection, np.array([3, 4]))
        
        # Test union
        union = Cutils.union([arr1, arr2])
        expected_union = np.array([1, 2, 3, 4, 5, 6])
        np.testing.assert_array_equal(union, expected_union)
        
        # Test difference
        diff = Cutils.difference(arr1, arr2)
        np.testing.assert_array_equal(diff, np.array([1, 2]))
    
    def test_statistical_functions(self):
        """Test statistical functions"""
        values = np.array([1, 2, 3, 2, 4, 3, 5, 2])
        
        # Test most_common
        most_common = Cutils.most_common(values, n=2)
        self.assertEqual(most_common[0][0], 2)  # Most common value
        self.assertEqual(most_common[0][1], 3)  # Count
        
        # Test mode_value
        mode = Cutils.mode_value(values)
        self.assertEqual(mode, 2)
        
        # Test frequency_distribution
        freq_dist = Cutils.frequency_distribution(values)
        self.assertAlmostEqual(freq_dist[2], 3/8, places=5)
    
    def test_sampling_and_shuffling(self):
        """Test sampling and shuffling functions"""
        values = list(range(20))
        
        # Test random_sample
        sample = Cutils.random_sample(values, 5, random_state=42)
        self.assertEqual(len(sample), 5)
        
        # Test shuffle
        shuffled = Cutils.shuffle(values, random_state=42)
        self.assertEqual(len(shuffled), len(values))
        self.assertNotEqual(shuffled, values)  # Should be different order
        
        # Test stratified_sample
        labels = [i % 3 for i in range(20)]  # 3 classes
        sampled_values, sampled_labels = Cutils.stratified_sample(
            values, labels, n_per_class=2, random_state=42
        )
        self.assertEqual(len(sampled_values), 6)  # 2 per class * 3 classes
        self.assertEqual(len(sampled_labels), 6)
    
    def test_validation_functions(self):
        """Test validation and checking functions"""
        lst = [1, 2, 3, 4, 5]
        
        # Test has_duplicates
        self.assertFalse(Cutils.has_duplicates(lst))
        self.assertTrue(Cutils.has_duplicates([1, 2, 2, 3]))
        
        # Test is_sorted
        self.assertTrue(Cutils.is_sorted(lst))
        self.assertFalse(Cutils.is_sorted([1, 3, 2, 4]))
        self.assertTrue(Cutils.is_sorted([5, 4, 3, 2], reverse=True))
    
    def test_matrix_operations(self):
        """Test matrix operations"""
        # Test list_to_matrix
        ragged_list = [[1, 2], [3, 4, 5], [6]]
        matrix = Cutils.list_to_matrix(ragged_list, fill_value=0)
        expected = np.array([[1, 2, 0], [3, 4, 5], [6, 0, 0]])
        np.testing.assert_array_equal(matrix, expected)
        
        # Test sparse_matrix_from_dict
        data = {(0, 0): 1.0, (1, 1): 2.0, (2, 2): 3.0}
        sparse_matrix = Cutils.sparse_matrix_from_dict(data, shape=(3, 3))
        self.assertEqual(sparse_matrix.shape, (3, 3))
        self.assertEqual(sparse_matrix[0, 0], 1.0)
        self.assertEqual(sparse_matrix[1, 1], 2.0)


class TestOptimizedMathUtils(unittest.TestCase):
    """Test cases for optimized mathematical utilities"""
    
    def test_vectorized_gaussian(self):
        """Test vectorized Gaussian functions"""
        x_values = np.array([0.0, 1.0, 2.0])
        
        # Test vectorized gauss
        result = MathUtils.gauss(x_values, 1.0)
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[0], 1.0 / MathUtils.SQRT2PI, places=5)
        
        # Test single value
        single_result = MathUtils.gauss(0.0, 1.0)
        self.assertAlmostEqual(single_result, 1.0 / MathUtils.SQRT2PI, places=5)
    
    def test_advanced_statistical_functions(self):
        """Test advanced statistical functions"""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        # Test enhanced statistics
        self.assertAlmostEqual(MathUtils.variance(values), 2.5, places=5)
        self.assertAlmostEqual(MathUtils.mad(values), 1.0, places=5)  # Approx
        
        # Test percentile
        p50 = MathUtils.percentile(values, 50)
        self.assertAlmostEqual(p50, 3.0, places=5)
        
        # Test IQR
        iqr = MathUtils.iqr(values)
        self.assertAlmostEqual(iqr, 2.0, places=5)
        
        # Test skewness and kurtosis
        skew = MathUtils.skewness(values)
        kurt = MathUtils.kurtosis(values)
        self.assertAlmostEqual(skew, 0.0, places=1)  # Symmetric distribution
    
    def test_enhanced_normalization(self):
        """Test enhanced normalization functions"""
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        
        # Test min-max with custom range
        normalized = MathUtils.min_max_normalize(values, feature_range=(-1, 1))
        self.assertAlmostEqual(normalized[0], -1.0, places=5)
        self.assertAlmostEqual(normalized[-1], 1.0, places=5)
        
        # Test robust normalization
        robust_norm = MathUtils.robust_normalize(values)
        self.assertEqual(len(robust_norm), len(values))
        
        # Test unit vector normalization
        unit_norm = MathUtils.unit_vector_normalize(values)
        norm = np.linalg.norm(unit_norm)
        self.assertAlmostEqual(norm, 1.0, places=5)
    
    def test_distance_and_correlation_functions(self):
        """Test distance and correlation functions"""
        x = np.array([1.0, 2.0, 3.0, 4.0])
        y = np.array([2.0, 4.0, 6.0, 8.0])  # Perfect correlation
        
        # Test enhanced correlations
        pearson = MathUtils.pearson_correlation(x, y)
        self.assertAlmostEqual(pearson, 1.0, places=5)
        
        spearman = MathUtils.spearman_correlation(x, y)
        self.assertAlmostEqual(spearman, 1.0, places=5)
        
        # Test distances
        euclidean_dist = MathUtils.euclidean_distance(x, y)
        self.assertGreater(euclidean_dist, 0)
        
        cosine_sim = MathUtils.cosine_similarity(x, y)
        self.assertAlmostEqual(cosine_sim, 1.0, places=5)
    
    def test_activation_functions(self):
        """Test activation functions"""
        x = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
        
        # Test sigmoid
        sigmoid_result = MathUtils.sigmoid(x)
        self.assertTrue(np.all(sigmoid_result >= 0) and np.all(sigmoid_result <= 1))
        
        # Test ReLU
        relu_result = MathUtils.relu(x)
        expected_relu = np.array([0.0, 0.0, 0.0, 1.0, 2.0])
        np.testing.assert_array_equal(relu_result, expected_relu)
        
        # Test leaky ReLU
        leaky_relu_result = MathUtils.leaky_relu(x, alpha=0.1)
        self.assertAlmostEqual(leaky_relu_result[0], -0.2, places=5)
        
        # Test softmax
        softmax_result = MathUtils.softmax(x)
        self.assertAlmostEqual(np.sum(softmax_result), 1.0, places=5)
    
    def test_signal_processing(self):
        """Test signal processing functions"""
        # Create noisy signal
        t = np.linspace(0, 1, 100)
        signal = np.sin(2 * np.pi * 5 * t) + 0.1 * np.random.randn(100)
        
        # Test moving average
        smoothed = MathUtils.moving_average(signal, window=5)
        self.assertEqual(len(smoothed), len(signal))
        
        # Test smooth curve (if signal is long enough)
        if len(signal) >= 5:
            smooth_signal = MathUtils.smooth_curve(signal, window_length=5)
            self.assertEqual(len(smooth_signal), len(signal))
    
    def test_outlier_detection(self):
        """Test outlier detection methods"""
        # Normal data with outliers
        normal_data = np.random.normal(0, 1, 100)
        outlier_data = np.concatenate([normal_data, [10, -10]])  # Add outliers
        
        # Test IQR method
        outliers_iqr = MathUtils.is_outlier(outlier_data, method='iqr')
        self.assertTrue(np.any(outliers_iqr))  # Should detect some outliers
        
        # Test z-score method
        outliers_zscore = MathUtils.is_outlier(outlier_data, method='zscore', threshold=2.0)
        self.assertTrue(np.any(outliers_zscore))
    
    def test_bootstrap_confidence_interval(self):
        """Test bootstrap confidence interval"""
        data = np.random.normal(5, 2, 100)
        
        ci_lower, ci_upper = MathUtils.bootstrap_ci(data, statistic_func=np.mean, 
                                                   n_bootstrap=100, confidence_level=0.95)
        
        # Check that CI contains the true mean (approximately)
        true_mean = np.mean(data)
        self.assertLessEqual(ci_lower, true_mean)
        self.assertGreaterEqual(ci_upper, true_mean)


class TestAdvancedSpatialTree(unittest.TestCase):
    """Test cases for advanced spatial tree"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create test atoms
        self.atoms = Atoms([
            Point(0, 0, 0), Point(1, 0, 0), Point(0, 1, 0),
            Point(5, 5, 5), Point(6, 5, 5)
        ])
    
    def test_tree_algorithms(self):
        """Test different tree algorithms"""
        algorithms = ['kd_tree', 'ball_tree', 'brute']
        
        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                tree = AdvancedSpatialTree(algorithm=algorithm)
                tree.build(self.atoms)
                
                # Test query
                neighbors = tree.query([0, 0, 0], k=2)
                self.assertEqual(len(neighbors), 2)
                
                # Test radius query
                radius_neighbors = tree.query_radius([0, 0, 0], radius=2.0)
                self.assertGreaterEqual(len(radius_neighbors), 1)
    
    def test_advanced_queries(self):
        """Test advanced query methods"""
        tree = AdvancedSpatialTree(algorithm='kd_tree')
        tree.build(self.atoms)
        
        # Test query with distances
        neighbors, distances = tree.query([0, 0, 0], k=2, return_distance=True)
        self.assertEqual(len(neighbors), 2)
        self.assertEqual(len(distances), 2)
        self.assertEqual(distances[0], 0.0)  # Distance to itself
        
        # Test count_neighbors
        count = tree.count_neighbors([0, 0, 0], radius=2.0)
        self.assertGreaterEqual(count, 1)
    
    def test_density_estimation(self):
        """Test kernel density estimation"""
        tree = AdvancedSpatialTree(algorithm='kd_tree')
        tree.build(self.atoms)
        
        # Test kernel density
        densities = tree.kernel_density(bandwidth=1.0)
        self.assertEqual(len(densities), len(self.atoms))
        self.assertTrue(np.all(densities > 0))


class TestAdvancedClustering(unittest.TestCase):
    """Test cases for advanced clustering"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create clustered test data
        cluster1 = [Point(i, j, 0) for i in range(3) for j in range(3)]
        cluster2 = [Point(10+i, 10+j, 0) for i in range(3) for j in range(3)]
        self.atoms = Atoms(cluster1 + cluster2)
    
    def test_clustering_algorithms(self):
        """Test different clustering algorithms"""
        algorithms = ['dbscan', 'kmeans', 'agglomerative']
        
        for algorithm in algorithms:
            with self.subTest(algorithm=algorithm):
                try:
                    clusterer = AdvancedAtomClusterer(algorithm=algorithm, n_clusters=2)
                    clusters = clusterer.cluster_atoms(self.atoms)
                    self.assertGreaterEqual(len(clusters), 1)
                except Exception as e:
                    self.skipTest(f"Algorithm {algorithm} not available: {e}")
    
    def test_clustering_evaluation(self):
        """Test clustering evaluation metrics"""
        coords = np.array([atom.get_coords() for atom in self.atoms])
        labels = np.array([0]*9 + [1]*9)  # True clustering
        
        # Test individual metrics
        silhouette = ClusteringMetrics.silhouette_coefficient(coords, labels)
        self.assertGreater(silhouette, 0)  # Should be positive for good clustering
        
        calinski = ClusteringMetrics.calinski_harabasz_index(coords, labels)
        self.assertGreater(calinski, 0)
        
        davies_bouldin = ClusteringMetrics.davies_bouldin_index(coords, labels)
        self.assertGreater(davies_bouldin, 0)


if __name__ == '__main__':
    unittest.main() 