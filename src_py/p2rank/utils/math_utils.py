"""
Mathematical utilities for P2Rank - Optimized with NumPy/SciPy
"""
import math
import random
from typing import List, Union, Optional, Tuple
import numpy as np
from scipy import stats, spatial, optimize, special
from scipy.stats import gaussian_kde
from scipy.signal import savgol_filter
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.metrics import pairwise_distances


class MathUtils:
    """Mathematical utility functions - optimized with scientific computing libraries"""
    
    SQRT2PI = np.sqrt(2 * np.pi)
    EPS = np.finfo(float).eps  # Machine epsilon
    
    # ===== Gaussian and Distribution Functions =====
    
    @staticmethod
    def gauss(x: Union[float, np.ndarray], sigma: float) -> Union[float, np.ndarray]:
        """Vectorized Gaussian function with sigma parameter"""
        x = np.asarray(x)
        return (1.0 / (sigma * MathUtils.SQRT2PI)) * np.exp(-0.5 * (x / sigma) ** 2)
    
    @staticmethod
    def gauss_params(x: Union[float, np.ndarray], a: float, c: float) -> Union[float, np.ndarray]:
        """Vectorized Gaussian function with a and c parameters"""
        x = np.asarray(x)
        return a * np.exp(-(x * x) / (2 * c * c))
    
    @staticmethod
    def gauss_norm(x: Union[float, np.ndarray], sigma: float) -> Union[float, np.ndarray]:
        """Normalized Gaussian function"""
        return MathUtils.gauss(x, sigma) / MathUtils.gauss(0, sigma)
    
    @staticmethod
    def multivariate_gaussian(x: np.ndarray, mean: np.ndarray, cov: np.ndarray) -> float:
        """Multivariate Gaussian probability density"""
        return stats.multivariate_normal.pdf(x, mean, cov)
    
    @staticmethod
    def gaussian_kernel_density(data: np.ndarray, points: np.ndarray) -> np.ndarray:
        """Gaussian kernel density estimation"""
        kde = gaussian_kde(data.T)
        return kde(points.T)
    
    # ===== Random Number Generation =====
    
    @staticmethod
    def random_int(low: int = -2147483648, high: int = 2147483647) -> int:
        """Generate random integer with numpy's improved RNG"""
        return np.random.randint(low, high + 1)
    
    @staticmethod
    def random_seed(seed: int):
        """Set random seed for reproducibility"""
        np.random.seed(seed)
        random.seed(seed)
    
    @staticmethod
    def random_choice(arr: np.ndarray, size: int = 1, p: Optional[np.ndarray] = None) -> np.ndarray:
        """Random choice with optional probabilities"""
        return np.random.choice(arr, size=size, p=p)
    
    # ===== Statistical Functions =====
    
    @staticmethod
    def mean(values: Union[List[float], np.ndarray]) -> float:
        """Calculate mean using numpy (handles NaN values)"""
        values = np.asarray(values)
        return np.nanmean(values) if values.size > 0 else 0.0
    
    @staticmethod
    def median(values: Union[List[float], np.ndarray]) -> float:
        """Calculate median using numpy"""
        values = np.asarray(values)
        return np.nanmedian(values) if values.size > 0 else 0.0
    
    @staticmethod
    def stddev(values: Union[List[float], np.ndarray], ddof: int = 1) -> float:
        """Calculate standard deviation using numpy"""
        values = np.asarray(values)
        return np.nanstd(values, ddof=ddof) if values.size > 1 else 0.0
    
    @staticmethod
    def variance(values: Union[List[float], np.ndarray], ddof: int = 1) -> float:
        """Calculate variance using numpy"""
        values = np.asarray(values)
        return np.nanvar(values, ddof=ddof) if values.size > 1 else 0.0
    
    @staticmethod
    def mad(values: Union[List[float], np.ndarray]) -> float:
        """Median Absolute Deviation"""
        values = np.asarray(values)
        return stats.median_abs_deviation(values, nan_policy='omit')
    
    @staticmethod
    def percentile(values: Union[List[float], np.ndarray], q: Union[float, List[float]]) -> Union[float, np.ndarray]:
        """Calculate percentiles"""
        values = np.asarray(values)
        return np.nanpercentile(values, q)
    
    @staticmethod
    def iqr(values: Union[List[float], np.ndarray]) -> float:
        """Interquartile Range"""
        return stats.iqr(values, nan_policy='omit')
    
    @staticmethod
    def skewness(values: Union[List[float], np.ndarray]) -> float:
        """Calculate skewness"""
        values = np.asarray(values)
        return stats.skew(values, nan_policy='omit')
    
    @staticmethod
    def kurtosis(values: Union[List[float], np.ndarray]) -> float:
        """Calculate kurtosis"""
        values = np.asarray(values)
        return stats.kurtosis(values, nan_policy='omit')
    
    # ===== Normalization Functions =====
    
    @staticmethod
    def min_max_normalize(values: Union[List[float], np.ndarray], 
                         feature_range: Tuple[float, float] = (0, 1)) -> np.ndarray:
        """Min-max normalization using sklearn"""
        values = np.asarray(values).reshape(-1, 1)
        if values.size == 0:
            return np.array([])
        
        scaler = MinMaxScaler(feature_range=feature_range)
        return scaler.fit_transform(values).flatten()
    
    @staticmethod
    def z_score_normalize(values: Union[List[float], np.ndarray]) -> np.ndarray:
        """Z-score normalization using sklearn"""
        values = np.asarray(values).reshape(-1, 1)
        if values.size == 0:
            return np.array([])
        
        scaler = StandardScaler()
        return scaler.fit_transform(values).flatten()
    
    @staticmethod
    def robust_normalize(values: Union[List[float], np.ndarray]) -> np.ndarray:
        """Robust normalization using median and MAD"""
        values = np.asarray(values).reshape(-1, 1)
        if values.size == 0:
            return np.array([])
        
        scaler = RobustScaler()
        return scaler.fit_transform(values).flatten()
    
    @staticmethod
    def unit_vector_normalize(values: Union[List[float], np.ndarray]) -> np.ndarray:
        """Normalize to unit vector"""
        values = np.asarray(values)
        norm = np.linalg.norm(values)
        return values / norm if norm > MathUtils.EPS else values
    
    # ===== Correlation and Distance Functions =====
    
    @staticmethod
    def pearson_correlation(x: Union[List[float], np.ndarray], 
                          y: Union[List[float], np.ndarray]) -> float:
        """Pearson correlation using scipy"""
        x, y = np.asarray(x), np.asarray(y)
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        corr, _ = stats.pearsonr(x, y)
        return corr if not np.isnan(corr) else 0.0
    
    @staticmethod
    def spearman_correlation(x: Union[List[float], np.ndarray], 
                           y: Union[List[float], np.ndarray]) -> float:
        """Spearman rank correlation"""
        x, y = np.asarray(x), np.asarray(y)
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        corr, _ = stats.spearmanr(x, y)
        return corr if not np.isnan(corr) else 0.0
    
    @staticmethod
    def correlation_matrix(data: np.ndarray) -> np.ndarray:
        """Calculate correlation matrix"""
        return np.corrcoef(data, rowvar=False)
    
    @staticmethod
    def euclidean_distance(x: np.ndarray, y: np.ndarray) -> float:
        """Euclidean distance using scipy"""
        return spatial.distance.euclidean(x, y)
    
    @staticmethod
    def cosine_similarity(x: np.ndarray, y: np.ndarray) -> float:
        """Cosine similarity"""
        return 1 - spatial.distance.cosine(x, y)
    
    @staticmethod
    def pairwise_distances_matrix(X: np.ndarray, metric: str = 'euclidean') -> np.ndarray:
        """Compute pairwise distance matrix"""
        return pairwise_distances(X, metric=metric)
    
    # ===== Activation and Transform Functions =====
    
    @staticmethod
    def sigmoid(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Standard sigmoid function"""
        x = np.asarray(x)
        return special.expit(x)  # More numerically stable than 1/(1+exp(-x))
    
    @staticmethod
    def sigmoid01(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Transform (0,inf) to (0,1) using modified sigmoid"""
        x = np.asarray(x)
        return (2.0 / (np.exp(-x) + 1.0)) - 1.0
    
    @staticmethod
    def tanh(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """Hyperbolic tangent"""
        return np.tanh(x)
    
    @staticmethod
    def relu(x: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """ReLU activation function"""
        x = np.asarray(x)
        return np.maximum(0, x)
    
    @staticmethod
    def leaky_relu(x: Union[float, np.ndarray], alpha: float = 0.01) -> Union[float, np.ndarray]:
        """Leaky ReLU activation function"""
        x = np.asarray(x)
        return np.where(x > 0, x, alpha * x)
    
    @staticmethod
    def softmax(x: np.ndarray) -> np.ndarray:
        """Softmax function (numerically stable)"""
        x = np.asarray(x)
        exp_x = np.exp(x - np.max(x))  # Numerical stability
        return exp_x / np.sum(exp_x)
    
    # ===== Mathematical Operations =====
    
    @staticmethod
    def ceil_div(x: int, y: int) -> int:
        """Ceiling division"""
        return -(-x // y)
    
    @staticmethod
    def log_sum_exp(x: np.ndarray) -> float:
        """Numerically stable log-sum-exp"""
        return special.logsumexp(x)
    
    @staticmethod
    def moving_average(values: np.ndarray, window: int) -> np.ndarray:
        """Moving average using convolution"""
        if window >= len(values):
            return np.full_like(values, np.mean(values))
        
        weights = np.ones(window) / window
        return np.convolve(values, weights, mode='same')
    
    @staticmethod
    def smooth_curve(values: np.ndarray, window_length: int = 5, polyorder: int = 2) -> np.ndarray:
        """Smooth curve using Savitzky-Golay filter"""
        if len(values) < window_length:
            return values
        
        if window_length % 2 == 0:
            window_length += 1  # Must be odd
        
        return savgol_filter(values, window_length, polyorder)
    
    @staticmethod
    def find_peaks(values: np.ndarray, height: Optional[float] = None, 
                   distance: Optional[int] = None) -> np.ndarray:
        """Find peaks in signal"""
        from scipy.signal import find_peaks as scipy_find_peaks
        peaks, _ = scipy_find_peaks(values, height=height, distance=distance)
        return peaks
    
    # ===== Interpolation and Fitting =====
    
    @staticmethod
    def interpolate_1d(x: np.ndarray, y: np.ndarray, x_new: np.ndarray, 
                      kind: str = 'linear') -> np.ndarray:
        """1D interpolation"""
        from scipy.interpolate import interp1d
        f = interp1d(x, y, kind=kind, fill_value='extrapolate')
        return f(x_new)
    
    @staticmethod
    def polynomial_fit(x: np.ndarray, y: np.ndarray, degree: int = 2) -> Tuple[np.ndarray, float]:
        """Polynomial fitting with R-squared"""
        coeffs = np.polyfit(x, y, degree)
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        return coeffs, r_squared
    
    # ===== Statistical Tests =====
    
    @staticmethod
    def t_test(sample1: np.ndarray, sample2: np.ndarray) -> Tuple[float, float]:
        """Independent t-test"""
        statistic, p_value = stats.ttest_ind(sample1, sample2)
        return statistic, p_value
    
    @staticmethod
    def chi_square_test(observed: np.ndarray, expected: np.ndarray) -> Tuple[float, float]:
        """Chi-square goodness of fit test"""
        statistic, p_value = stats.chisquare(observed, expected)
        return statistic, p_value
    
    @staticmethod
    def kolmogorov_smirnov_test(sample: np.ndarray, distribution: str = 'norm') -> Tuple[float, float]:
        """Kolmogorov-Smirnov test for normality"""
        if distribution == 'norm':
            statistic, p_value = stats.kstest(sample, 'norm')
        else:
            statistic, p_value = stats.kstest(sample, distribution)
        return statistic, p_value
    
    # ===== Utility Functions =====
    
    @staticmethod
    def is_outlier(values: np.ndarray, method: str = 'iqr', threshold: float = 1.5) -> np.ndarray:
        """Detect outliers using various methods"""
        values = np.asarray(values)
        
        if method == 'iqr':
            Q1 = np.percentile(values, 25)
            Q3 = np.percentile(values, 75)
            IQR = Q3 - Q1
            lower_bound = Q1 - threshold * IQR
            upper_bound = Q3 + threshold * IQR
            return (values < lower_bound) | (values > upper_bound)
        
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(values))
            return z_scores > threshold
        
        elif method == 'modified_zscore':
            median = np.median(values)
            mad = stats.median_abs_deviation(values)
            modified_z_scores = 0.6745 * (values - median) / mad
            return np.abs(modified_z_scores) > threshold
        
        else:
            raise ValueError(f"Unknown outlier detection method: {method}")
    
    @staticmethod
    def bootstrap_ci(data: np.ndarray, statistic_func: callable = np.mean, 
                    n_bootstrap: int = 1000, confidence_level: float = 0.95) -> Tuple[float, float]:
        """Bootstrap confidence interval"""
        bootstrap_stats = []
        n = len(data)
        
        for _ in range(n_bootstrap):
            bootstrap_sample = np.random.choice(data, size=n, replace=True)
            bootstrap_stats.append(statistic_func(bootstrap_sample))
        
        bootstrap_stats = np.array(bootstrap_stats)
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        ci_lower = np.percentile(bootstrap_stats, lower_percentile)
        ci_upper = np.percentile(bootstrap_stats, upper_percentile)
        
        return ci_lower, ci_upper
    
    @staticmethod
    def entropy(probabilities: np.ndarray, base: float = 2) -> float:
        """Calculate entropy"""
        probabilities = np.asarray(probabilities)
        # Remove zero probabilities to avoid log(0)
        probabilities = probabilities[probabilities > 0]
        if len(probabilities) == 0:
            return 0.0
        
        return stats.entropy(probabilities, base=base)
    
    @staticmethod
    def mutual_information(x: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
        """Estimate mutual information between two variables"""
        from sklearn.feature_selection import mutual_info_regression
        x = x.reshape(-1, 1) if x.ndim == 1 else x
        return mutual_info_regression(x, y)[0]
    
    @staticmethod
    def gini_coefficient(values: np.ndarray) -> float:
        """Calculate Gini coefficient (inequality measure)"""
        values = np.asarray(values)
        values = np.sort(values)
        n = len(values)
        cumsum = np.cumsum(values)
        return (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0.0 