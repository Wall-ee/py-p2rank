"""
Collection utilities for P2Rank - Optimized with NumPy/SciPy
"""
from typing import List, Optional, TypeVar, Callable, Dict, Any, Iterable, Iterator, Union, Tuple
import json
from collections import Counter, defaultdict
import numpy as np
from scipy import sparse
from scipy.stats import mode
import threading
from itertools import combinations, permutations, product
import functools

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class Cutils:
    """Collection utilities - optimized with scientific computing libraries"""
    
    # ===== Basic Collection Operations =====
    
    @staticmethod
    def empty(collection: Optional[Union[List, np.ndarray]]) -> bool:
        """Check if collection is None or empty (supports numpy arrays)"""
        if collection is None:
            return True
        if isinstance(collection, np.ndarray):
            return collection.size == 0
        return len(collection) == 0
    
    @staticmethod
    def head(n: int, lst: Union[List[T], np.ndarray]) -> Union[List[T], np.ndarray]:
        """Get first n elements from list or array"""
        if isinstance(lst, np.ndarray):
            return lst[:min(n, len(lst))]
        
        if n >= len(lst):
            return lst
        return lst[:n]
    
    @staticmethod
    def tail(n: int, lst: Union[List[T], np.ndarray]) -> Union[List[T], np.ndarray]:
        """Get last n elements from list or array"""
        if isinstance(lst, np.ndarray):
            return lst[-min(n, len(lst)):]
        
        return lst[-min(n, len(lst)):]
    
    @staticmethod
    def previous_in_list(i: int, lst: Union[List[T], np.ndarray]) -> Optional[T]:
        """Get previous element in list"""
        if i > 0 and i < len(lst):
            return lst[i - 1]
        return None
    
    @staticmethod
    def next_in_list(i: int, lst: Union[List[T], np.ndarray]) -> Optional[T]:
        """Get next element in list"""
        if i >= 0 and i < len(lst) - 1:
            return lst[i + 1]
        return None
    
    # ===== Vectorized Operations =====
    
    @staticmethod
    def map_list(lst: Optional[Union[List[T], np.ndarray]], mapper: Callable[[T], V]) -> Union[List[V], np.ndarray]:
        """Map function over list (vectorized for numpy arrays when possible)"""
        if lst is None or Cutils.empty(lst):
            return [] if not isinstance(lst, np.ndarray) else np.array([])
        
        if isinstance(lst, np.ndarray):
            try:
                # Try vectorized operation first
                vectorized_mapper = np.vectorize(mapper)
                return vectorized_mapper(lst)
            except:
                # Fall back to list comprehension
                return np.array([mapper(item) for item in lst])
        
        return [mapper(item) for item in lst]
    
    @staticmethod
    def map_list_parallel(lst: Optional[List[T]], mapper: Callable[[T], V], n_jobs: int = -1) -> List[V]:
        """Parallel map operation using multiprocessing"""
        if lst is None or len(lst) == 0:
            return []
        
        # For small lists, don't use parallelization
        if len(lst) < 100:
            return [mapper(item) for item in lst]
        
        try:
            from joblib import Parallel, delayed
            return Parallel(n_jobs=n_jobs)(delayed(mapper)(item) for item in lst)
        except ImportError:
            # Fall back to regular map if joblib not available
            return [mapper(item) for item in lst]
    
    @staticmethod
    def transform_keys(d: Dict[K, V], transformer: Callable[[K], K]) -> Dict[K, V]:
        """Transform keys in dictionary"""
        return {transformer(k): v for k, v in d.items()}
    
    @staticmethod
    def prefix_map_keys(d: Dict[str, V], prefix: str) -> Dict[str, V]:
        """Prefix all string keys in dictionary"""
        return {prefix + k: v for k, v in d.items()}
    
    # ===== Numerical Operations =====
    
    @staticmethod
    def sum_doubles(lst: Optional[Union[List[float], np.ndarray]]) -> float:
        """Sum list of doubles, ignoring None values (optimized with numpy)"""
        if lst is None or Cutils.empty(lst):
            return 0.0
        
        if isinstance(lst, np.ndarray):
            return float(np.nansum(lst))
        
        # Convert to numpy array for efficient computation
        arr = np.array([d for d in lst if d is not None], dtype=float)
        return float(np.sum(arr)) if arr.size > 0 else 0.0
    
    @staticmethod
    def sum_with_weights(values: Union[List[float], np.ndarray], 
                        weights: Union[List[float], np.ndarray]) -> float:
        """Weighted sum using numpy"""
        values = np.asarray(values)
        weights = np.asarray(weights)
        
        if values.size != weights.size:
            raise ValueError("Values and weights must have the same length")
        
        return float(np.sum(values * weights))
    
    @staticmethod
    def cumulative_sum(lst: Union[List[float], np.ndarray]) -> np.ndarray:
        """Cumulative sum using numpy"""
        return np.cumsum(np.asarray(lst))
    
    @staticmethod
    def running_average(lst: Union[List[float], np.ndarray], window: int) -> np.ndarray:
        """Running average using numpy convolution"""
        arr = np.asarray(lst)
        if window >= len(arr):
            return np.full_like(arr, np.mean(arr))
        
        weights = np.ones(window) / window
        return np.convolve(arr, weights, mode='same')
    
    # ===== Advanced Collection Operations =====
    
    @staticmethod
    def map_with_index(values: Iterable[V], key_function: Callable[[V], K]) -> Dict[K, V]:
        """Create map using key function (optimized for large datasets)"""
        if isinstance(values, (list, tuple)) and len(values) > 1000:
            # Use numpy for large datasets
            try:
                keys = Cutils.map_list(values, key_function)
                return dict(zip(keys, values))
            except:
                pass
        
        return {key_function(v): v for v in values}
    
    @staticmethod
    def find_duplicates(values: Union[Iterable[T], np.ndarray]) -> List[T]:
        """Find duplicate values in iterable (optimized with numpy for arrays)"""
        if isinstance(values, np.ndarray):
            unique, counts = np.unique(values, return_counts=True)
            return unique[counts > 1].tolist()
        
        counts = Counter(values)
        return [item for item, count in counts.items() if count > 1]
    
    @staticmethod
    def unique_elements(values: Union[Iterable[T], np.ndarray], preserve_order: bool = False) -> Union[List[T], np.ndarray]:
        """Get unique elements (optimized with numpy)"""
        if isinstance(values, np.ndarray):
            if preserve_order:
                _, idx = np.unique(values, return_index=True)
                return values[np.sort(idx)]
            else:
                return np.unique(values)
        
        if preserve_order:
            seen = set()
            result = []
            for item in values:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            return result
        else:
            return list(set(values))
    
    @staticmethod
    def group_by(values: Iterable[V], key_function: Callable[[V], K]) -> Dict[K, List[V]]:
        """Group values by key function"""
        groups = defaultdict(list)
        for value in values:
            key = key_function(value)
            groups[key].append(value)
        return dict(groups)
    
    @staticmethod
    def partition(values: Iterable[T], predicate: Callable[[T], bool]) -> Tuple[List[T], List[T]]:
        """Partition values into two lists based on predicate"""
        true_values, false_values = [], []
        for value in values:
            (true_values if predicate(value) else false_values).append(value)
        return true_values, false_values
    
    # ===== Set Operations =====
    
    @staticmethod
    def intersection(lists: List[Union[List[T], np.ndarray]]) -> Union[List[T], np.ndarray]:
        """Intersection of multiple lists/arrays"""
        if not lists:
            return []
        
        if all(isinstance(lst, np.ndarray) for lst in lists):
            # Use numpy set operations for arrays
            result = lists[0]
            for lst in lists[1:]:
                result = np.intersect1d(result, lst)
            return result
        
        # Convert to sets for efficient intersection
        sets = [set(lst) for lst in lists]
        result = sets[0]
        for s in sets[1:]:
            result = result.intersection(s)
        return list(result)
    
    @staticmethod
    def union(lists: List[Union[List[T], np.ndarray]]) -> Union[List[T], np.ndarray]:
        """Union of multiple lists/arrays"""
        if not lists:
            return []
        
        if all(isinstance(lst, np.ndarray) for lst in lists):
            # Use numpy set operations for arrays
            result = lists[0]
            for lst in lists[1:]:
                result = np.union1d(result, lst)
            return result
        
        # Convert to sets for efficient union
        sets = [set(lst) for lst in lists]
        result = sets[0]
        for s in sets[1:]:
            result = result.union(s)
        return list(result)
    
    @staticmethod
    def difference(list1: Union[List[T], np.ndarray], list2: Union[List[T], np.ndarray]) -> Union[List[T], np.ndarray]:
        """Set difference of two lists/arrays"""
        if isinstance(list1, np.ndarray) and isinstance(list2, np.ndarray):
            return np.setdiff1d(list1, list2)
        
        return list(set(list1) - set(list2))
    
    # ===== Advanced Statistics =====
    
    @staticmethod
    def most_common(values: Union[Iterable[T], np.ndarray], n: int = 1) -> List[Tuple[T, int]]:
        """Get n most common values with counts"""
        if isinstance(values, np.ndarray):
            unique, counts = np.unique(values, return_counts=True)
            # Sort by counts in descending order
            idx = np.argsort(counts)[::-1]
            return list(zip(unique[idx][:n], counts[idx][:n]))
        
        counter = Counter(values)
        return counter.most_common(n)
    
    @staticmethod
    def mode_value(values: Union[List[T], np.ndarray]) -> T:
        """Get mode (most common value)"""
        if isinstance(values, np.ndarray):
            mode_result = mode(values, keepdims=False)
            return mode_result.mode
        
        counter = Counter(values)
        return counter.most_common(1)[0][0]
    
    @staticmethod
    def frequency_distribution(values: Union[Iterable[T], np.ndarray]) -> Dict[T, float]:
        """Get frequency distribution (normalized counts)"""
        if isinstance(values, np.ndarray):
            unique, counts = np.unique(values, return_counts=True)
            total = len(values)
            return dict(zip(unique, counts / total))
        
        counter = Counter(values)
        total = sum(counter.values())
        return {k: v / total for k, v in counter.items()}
    
    # ===== Sampling and Shuffling =====
    
    @staticmethod
    def random_sample(lst: Union[List[T], np.ndarray], n: int, replace: bool = False, 
                     random_state: Optional[int] = None) -> Union[List[T], np.ndarray]:
        """Random sampling using numpy"""
        if random_state is not None:
            np.random.seed(random_state)
        
        if isinstance(lst, np.ndarray):
            return np.random.choice(lst, size=min(n, len(lst)), replace=replace)
        
        indices = np.random.choice(len(lst), size=min(n, len(lst)), replace=replace)
        return [lst[i] for i in indices]
    
    @staticmethod
    def shuffle(lst: Union[List[T], np.ndarray], random_state: Optional[int] = None) -> Union[List[T], np.ndarray]:
        """Shuffle list or array"""
        if random_state is not None:
            np.random.seed(random_state)
        
        if isinstance(lst, np.ndarray):
            result = lst.copy()
            np.random.shuffle(result)
            return result
        
        result = lst.copy()
        np.random.shuffle(result)
        return result
    
    @staticmethod
    def stratified_sample(values: List[T], labels: List[K], n_per_class: int, 
                         random_state: Optional[int] = None) -> Tuple[List[T], List[K]]:
        """Stratified sampling maintaining class proportions"""
        if random_state is not None:
            np.random.seed(random_state)
        
        grouped = Cutils.group_by(zip(values, labels), lambda x: x[1])
        
        sampled_values = []
        sampled_labels = []
        
        for label, pairs in grouped.items():
            n_sample = min(n_per_class, len(pairs))
            sampled_pairs = Cutils.random_sample(pairs, n_sample, random_state=random_state)
            
            for value, label in sampled_pairs:
                sampled_values.append(value)
                sampled_labels.append(label)
        
        return sampled_values, sampled_labels
    
    # ===== Combinatorial Operations =====
    
    @staticmethod
    def combinations(lst: List[T], r: int) -> List[Tuple[T, ...]]:
        """Generate combinations"""
        return list(combinations(lst, r))
    
    @staticmethod
    def permutations(lst: List[T], r: Optional[int] = None) -> List[Tuple[T, ...]]:
        """Generate permutations"""
        return list(permutations(lst, r))
    
    @staticmethod
    def cartesian_product(lists: List[List[T]]) -> List[Tuple[T, ...]]:
        """Cartesian product of multiple lists"""
        return list(product(*lists))
    
    # ===== Validation and Checking =====
    
    @staticmethod
    def map_with_unique_index(values: Iterable[V], key_function: Callable[[V], K]) -> Dict[K, V]:
        """Create map with unique keys, raise error if duplicates found"""
        result = {}
        duplicates = []
        
        for value in values:
            key = key_function(value)
            if key in result:
                duplicates.append(key)
            else:
                result[key] = value
        
        if duplicates:
            raise ValueError(f"Duplicate keys found: {duplicates}")
        
        return result
    
    @staticmethod
    def has_duplicates(lst: Union[List[T], np.ndarray]) -> bool:
        """Check if list has duplicates (optimized)"""
        if isinstance(lst, np.ndarray):
            return len(lst) != len(np.unique(lst))
        
        return len(lst) != len(set(lst))
    
    @staticmethod
    def is_sorted(lst: Union[List[T], np.ndarray], reverse: bool = False) -> bool:
        """Check if list is sorted"""
        if isinstance(lst, np.ndarray):
            if reverse:
                return np.all(lst[:-1] >= lst[1:])
            else:
                return np.all(lst[:-1] <= lst[1:])
        
        if reverse:
            return all(lst[i] >= lst[i + 1] for i in range(len(lst) - 1))
        else:
            return all(lst[i] <= lst[i + 1] for i in range(len(lst) - 1))
    
    # ===== Safe Access =====
    
    @staticmethod
    def list_element(idx: int, lst: Optional[Union[List[T], np.ndarray]]) -> Optional[T]:
        """Get element at index or None if out of bounds"""
        if lst is None:
            return None
        if idx < 0 or idx >= len(lst):
            return None
        return lst[idx]
    
    @staticmethod
    def safe_get(d: Dict[K, V], key: K, default: V = None) -> V:
        """Safely get value from dictionary"""
        return d.get(key, default)
    
    @staticmethod
    def deep_get(d: Dict, keys: List[str], default: Any = None) -> Any:
        """Safely get nested dictionary value"""
        current = d
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    # ===== Thread Safety =====
    
    @staticmethod
    def synchronized_list() -> List:
        """Create thread-safe list with proper locking"""
        class SynchronizedList:
            def __init__(self):
                self._list = []
                self._lock = threading.RLock()
            
            def append(self, item):
                with self._lock:
                    self._list.append(item)
            
            def extend(self, items):
                with self._lock:
                    self._list.extend(items)
            
            def __getitem__(self, index):
                with self._lock:
                    return self._list[index]
            
            def __setitem__(self, index, value):
                with self._lock:
                    self._list[index] = value
            
            def __len__(self):
                with self._lock:
                    return len(self._list)
            
            def __iter__(self):
                with self._lock:
                    return iter(self._list.copy())
        
        return SynchronizedList()
    
    # ===== Caching and Memoization =====
    
    @staticmethod
    def memoize(func: Callable) -> Callable:
        """Memoization decorator for expensive functions"""
        cache = {}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create hashable key
            key = str(args) + str(sorted(kwargs.items()))
            
            if key not in cache:
                cache[key] = func(*args, **kwargs)
            
            return cache[key]
        
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {'hits': len(cache), 'size': len(cache)}
        
        return wrapper
    
    # ===== Matrix Operations =====
    
    @staticmethod
    def list_to_matrix(lst: List[List[T]], fill_value: T = None) -> np.ndarray:
        """Convert list of lists to numpy matrix (handling ragged arrays)"""
        if not lst:
            return np.array([])
        
        max_len = max(len(row) for row in lst)
        
        # Pad shorter rows
        padded = []
        for row in lst:
            if len(row) < max_len:
                padded_row = row + [fill_value] * (max_len - len(row))
            else:
                padded_row = row
            padded.append(padded_row)
        
        return np.array(padded)
    
    @staticmethod
    def sparse_matrix_from_dict(data: Dict[Tuple[int, int], float], shape: Tuple[int, int]) -> sparse.csr_matrix:
        """Create sparse matrix from dictionary of (row, col): value"""
        rows, cols, values = [], [], []
        
        for (row, col), value in data.items():
            rows.append(row)
            cols.append(col)
            values.append(value)
        
        return sparse.csr_matrix((values, (rows, cols)), shape=shape)
    
    # ===== Functional Programming Helpers =====
    
    @staticmethod
    def compose(*functions):
        """Compose multiple functions"""
        return functools.reduce(lambda f, g: lambda x: f(g(x)), functions, lambda x: x)
    
    @staticmethod
    def curry(func: Callable, *args, **kwargs) -> Callable:
        """Curry a function with partial arguments"""
        return functools.partial(func, *args, **kwargs)
    
    @staticmethod
    def chain(*iterables) -> Iterator:
        """Chain multiple iterables"""
        from itertools import chain
        return chain(*iterables) 