"""
Dataset representation for P2Rank
"""
from typing import List, Dict, Optional, Any
import logging
from pathlib import Path

from .protein import Protein


logger = logging.getLogger(__name__)


class Dataset:
    """
    Dataset represents a list of items (usually proteins) to be processed by the program.
    Multi-column format with declared variable header allows to specify complementary data.
    """
    
    class Item:
        """Dataset item representing a single protein with metadata"""
        
        def __init__(self, dataset: 'Dataset', label: str, protein_file: str,
                     apo_protein_file: Optional[str] = None,
                     prediction_file: Optional[str] = None,
                     chains: Optional[List[str]] = None,
                     apo_chains: Optional[List[str]] = None,
                     ligand_definitions: Optional[List[Any]] = None,
                     column_values: Optional[Dict[str, str]] = None):
            """
            Initialize dataset item.
            
            Args:
                dataset: Parent dataset
                label: Item label/identifier
                protein_file: Path to protein structure file
                apo_protein_file: Optional path to APO structure
                prediction_file: Optional path to prediction file
                chains: Optional list of chain IDs to process
                apo_chains: Optional list of APO chain IDs
                ligand_definitions: Optional ligand definitions
                column_values: Optional additional column values
            """
            self.origin_dataset = dataset
            self.current_dataset = dataset
            self.label = label
            self.protein_file = protein_file
            self.apo_protein_file = apo_protein_file
            self.pocket_prediction_file = prediction_file
            self.chains = chains
            self.apo_chains = apo_chains
            self.ligand_definitions = ligand_definitions or []
            self.column_values = column_values or {}
            
            # Cached data
            self.cached_pair: Optional[Any] = None  # PredictionPair
            self.transformation: Optional[Any] = None  # GeometricTransformation
        
        def __str__(self) -> str:
            return f"Item(label={self.label}, protein={self.protein_file})"
    
    def __init__(self, name: str = ""):
        """Initialize dataset"""
        self.name = name
        self.label = name
        self.items: List[Dataset.Item] = []
        self.header: List[str] = []
        self.cached_items: Dict[str, Any] = {}
        
        # Dataset properties
        self.properties: Dict[str, Any] = {}
        self.column_types: Dict[str, type] = {}
    
    def add_item(self, item: 'Dataset.Item'):
        """Add item to dataset"""
        self.items.append(item)
    
    def create_item(self, label: str, protein_file: str, **kwargs) -> 'Dataset.Item':
        """Create and add new dataset item"""
        item = Dataset.Item(self, label, protein_file, **kwargs)
        self.add_item(item)
        return item
    
    def get_item(self, label: str) -> Optional['Dataset.Item']:
        """Get item by label"""
        for item in self.items:
            if item.label == label:
                return item
        return None
    
    def get_items_by_file(self, protein_file: str) -> List['Dataset.Item']:
        """Get items by protein file"""
        return [item for item in self.items if item.protein_file == protein_file]
    
    @property
    def size(self) -> int:
        """Get number of items in dataset"""
        return len(self.items)
    
    @property
    def empty(self) -> bool:
        """Check if dataset is empty"""
        return len(self.items) == 0
    
    def filter_by_chains(self, chain_ids: List[str]) -> 'Dataset':
        """Create filtered dataset with specific chains"""
        filtered = Dataset(f"{self.name}_filtered")
        for item in self.items:
            if item.chains and any(chain in chain_ids for chain in item.chains):
                filtered.add_item(item)
        return filtered
    
    def split(self, ratio: float = 0.8) -> tuple['Dataset', 'Dataset']:
        """Split dataset into train/test sets"""
        import random
        
        items_copy = self.items.copy()
        random.shuffle(items_copy)
        
        split_point = int(len(items_copy) * ratio)
        
        train_dataset = Dataset(f"{self.name}_train")
        test_dataset = Dataset(f"{self.name}_test")
        
        train_dataset.items = items_copy[:split_point]
        test_dataset.items = items_copy[split_point:]
        
        return train_dataset, test_dataset
    
    @classmethod
    def load_from_file(cls, file_path: str) -> 'Dataset':
        """Load dataset from file"""
        dataset_file = Path(file_path)
        dataset = cls(dataset_file.stem)
        
        if not dataset_file.exists():
            logger.error(f"Dataset file not found: {file_path}")
            return dataset
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            if not lines:
                return dataset
            
            # Parse header
            header = lines[0].strip().split('\t')
            dataset.header = header
            
            # Parse items
            for line_num, line in enumerate(lines[1:], 2):
                if line.strip():
                    try:
                        columns = line.strip().split('\t')
                        if len(columns) >= 2:  # At least label and protein file
                            label = columns[0]
                            protein_file = columns[1]
                            
                            # Parse additional columns
                            column_values = {}
                            for i, value in enumerate(columns[2:], 2):
                                if i < len(header):
                                    column_values[header[i]] = value
                            
                            dataset.create_item(
                                label=label,
                                protein_file=protein_file,
                                column_values=column_values
                            )
                    except Exception as e:
                        logger.warning(f"Error parsing line {line_num} in {file_path}: {e}")
        
        except Exception as e:
            logger.error(f"Error loading dataset from {file_path}: {e}")
        
        logger.info(f"Loaded dataset '{dataset.name}' with {dataset.size} items")
        return dataset
    
    def save_to_file(self, file_path: str):
        """Save dataset to file"""
        try:
            with open(file_path, 'w') as f:
                # Write header
                if self.header:
                    f.write('\t'.join(self.header) + '\n')
                else:
                    f.write('label\tprotein_file\n')
                
                # Write items
                for item in self.items:
                    row = [item.label, item.protein_file]
                    
                    # Add additional columns
                    if self.header and len(self.header) > 2:
                        for col_name in self.header[2:]:
                            value = item.column_values.get(col_name, '')
                            row.append(value)
                    
                    f.write('\t'.join(row) + '\n')
            
            logger.info(f"Saved dataset '{self.name}' to {file_path}")
        
        except Exception as e:
            logger.error(f"Error saving dataset to {file_path}: {e}")
    
    def __str__(self) -> str:
        return f"Dataset(name={self.name}, size={self.size})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def __len__(self) -> int:
        return self.size
    
    def __iter__(self):
        return iter(self.items)
    
    def __getitem__(self, index) -> 'Dataset.Item':
        return self.items[index] 