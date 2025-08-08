# P2Rank Python Implementation

This is a Python port of the P2Rank protein pocket prediction tool, originally implemented in Groovy/Java.

## Overview

P2Rank is a machine learning-based tool for prediction of ligand binding pockets from protein structure. This Python implementation aims to provide the same functionality with improved accessibility and integration with the Python scientific ecosystem.

## Features

- **Pocket Prediction**: Identify and rank potential ligand binding sites in protein structures
- **Machine Learning**: Uses trained models to score surface points for ligandability  
- **Clustering Algorithm**: Groups ligandable points into discrete pocket predictions
- **Configurable Parameters**: Extensive parameter system for algorithm customization
- **Multiple Input Formats**: Support for PDB and CIF protein structure files

## Architecture

The codebase is organized into several key packages:

### Core Components

- **`domain/`**: Core domain objects (Protein, Pocket, Dataset, etc.)
- **`prediction/`**: Pocket prediction algorithms and scoring
- **`geom/`**: Geometric operations and spatial data structures  
- **`program/`**: Main application logic and parameter management
- **`utils/`**: Utility functions for clustering, logging, etc.

### Key Classes

- **`PocketPredictor`**: Core algorithm implementation
- **`Protein`**: Represents protein structure with atoms and surfaces
- **`Pocket`**: Represents a predicted binding pocket
- **`Atoms`**: Collection of atoms with spatial operations
- **`Dataset`**: Manages collections of proteins for processing

## Installation

```bash
# Clone the repository
cd src_py

# Install dependencies  
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Usage

### Command Line Interface

```bash
# Predict pockets in a protein structure
p2rank predict -i protein.pdb -o results/

# Show help
p2rank help

# Show version information  
p2rank version
```

### Python API

```python
from p2rank.prediction.pocket_predictor import PocketPredictor
from p2rank.domain.protein import Protein
from p2rank.program.params import Params

# Initialize predictor with parameters
params = Params()
predictor = PocketPredictor(params)

# Load protein (would require BioPython integration)
protein = Protein()

# Predict pockets
pockets = predictor.predict_pockets(labeled_points, protein)
```

## Configuration

The system uses a comprehensive parameter system for configuration:

- **Algorithm Parameters**: Clustering distance, minimum cluster size, scoring methods
- **Runtime Parameters**: Number of threads, output directories, logging levels
- **Model Parameters**: Feature extraction settings, machine learning parameters

Parameters can be set via:
- Configuration files (YAML format)
- Command line arguments
- Python API

## Dependencies

- **NumPy**: Numerical computations and array operations
- **SciPy**: Scientific computing functions
- **scikit-learn**: Machine learning algorithms and KD-tree
- **BioPython**: Protein structure parsing (integration needed)
- **pandas**: Data manipulation and analysis
- **matplotlib/seaborn**: Visualization (optional)

## Architecture Differences from Original

### Language-Specific Adaptations

1. **Type System**: Uses Python type hints instead of Groovy/Java static typing
2. **Memory Management**: Relies on Python garbage collection vs manual memory management
3. **Concurrency**: Uses Python threading/multiprocessing instead of Java threads
4. **Collections**: Uses Python lists/dicts instead of Java Collections
5. **Package Structure**: Follows Python package conventions

### Algorithm Optimizations

1. **Spatial Operations**: Leverages scipy/sklearn for KD-tree operations
2. **Clustering**: Provides both custom single-linkage and DBSCAN implementations
3. **Numerical Computing**: Uses NumPy for vectorized operations
4. **Machine Learning**: Can integrate with scikit-learn ecosystem

### Missing Components (Future Work)

1. **BioPython Integration**: Complete protein structure loading
2. **Feature Extraction**: Full feature calculation pipeline
3. **Model Training**: Machine learning model training capabilities
4. **Conservation Scoring**: Sequence conservation analysis
5. **Visualization**: Protein structure visualization tools

## Development Status

This is an initial port focusing on core architecture and algorithms. Key components implemented:

- ✅ Core domain objects (Protein, Pocket, Atoms, etc.)
- ✅ Pocket prediction algorithm (PocketPredictor)
- ✅ Spatial clustering and operations
- ✅ Parameter management system
- ✅ Command line interface structure
- ✅ Dataset management

## Contributing

Contributions are welcome! Key areas for development:

1. **BioPython Integration**: Complete protein structure parsing
2. **Feature Extraction**: Implement feature calculation pipeline  
3. **Model Integration**: Add machine learning model loading/inference
4. **Testing**: Add comprehensive test suite
5. **Documentation**: Expand API documentation

## License

This project maintains compatibility with the original P2Rank licensing.

## Acknowledgments

This Python implementation is based on the original P2Rank tool developed by the Laboratory of Bioinformatics at the Faculty of Mathematics and Physics, Charles University.

Original P2Rank: https://github.com/rdk/p2rank 