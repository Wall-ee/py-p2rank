# P2Rank Python Distribution

A complete, ready-to-use Python implementation of P2Rank protein pocket prediction tool.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or newer
- pip package manager

### Installation

1. **Download** this distribution package
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run P2Rank**:
   ```bash
   # Linux/macOS
   ./p2rank_py predict -f protein.pdb
   
   # Windows
   p2rank_py.bat predict -f protein.pdb
   
   # Or use Python directly
   python p2rank_py.py predict -f protein.pdb
   ```

## 📖 Usage Examples

### Basic Prediction
```bash
# Predict pockets in a single protein
./p2rank_py predict -f examples/1fbl.pdb

# Predict pockets in multiple proteins
./p2rank_py predict -f protein1.pdb,protein2.pdb,protein3.pdb

# Use a dataset file
./p2rank_py predict -d dataset.ds
```

### Advanced Options
```bash
# Use AlphaFold configuration (without B-factors)
./p2rank_py predict -f alphafold_structure.pdb -c alphafold

# Specify output directory
./p2rank_py predict -f protein.pdb -o results/

# Adjust number of threads
./p2rank_py predict -f protein.pdb -threads 8

# Enable verbose output
./p2rank_py predict -f protein.pdb -v
```

### Configuration Options
```bash
# List available configurations
./p2rank_py help configs

# Use custom configuration
./p2rank_py predict -f protein.pdb -c custom_config.yaml

# Override specific parameters
./p2rank_py predict -f protein.pdb -threads 4 -seed 123
```

## 📁 Package Structure

```
p2rank-python/
├── p2rank_py              # Main launcher (Linux/macOS)
├── p2rank_py.bat          # Main launcher (Windows)
├── p2rank_py.py           # Python launcher script
├── config/                # Configuration files
│   ├── default.yaml       # Default configuration
│   ├── alphafold.yaml     # AlphaFold-optimized config
│   └── ...
├── models/                # Pre-trained models
│   ├── default/           # Default model files
│   └── ...
├── test_data/             # Example data (symlink)
├── requirements.txt       # Python dependencies
├── LICENSE.txt           # License information
└── README.md             # This file
```

## ⚙️ Configuration

P2Rank Python uses YAML configuration files for parameter management:

### Default Configuration
The default configuration (`config/default.yaml`) contains settings optimized for general protein pocket prediction.

### AlphaFold Configuration
Use `config/alphafold.yaml` for AlphaFold predicted structures, cryo-EM, or NMR structures where B-factors may not be reliable.

### Custom Configuration
Create your own YAML configuration file:

```yaml
# my_config.yaml
model: "default"
threads: 8
features:
  - "chem"
  - "volsite"
  - "protrusion"
pred_min_cluster_size: 5
```

## 🔧 Command Line Parameters

### Required Parameters
- `-f <file>` or `--file <file>`: Input protein file(s)
- `-d <dataset>` or `--dataset <dataset>`: Dataset file

### Optional Parameters
- `-c <config>` or `--config <config>`: Configuration file
- `-o <dir>` or `--output <dir>`: Output directory
- `-threads <n>`: Number of CPU threads (default: auto-detect)
- `-seed <n>`: Random seed for reproducibility
- `-v, --verbose`: Enable verbose output
- `-model <name>`: Model name to use

### Parameter Override
Any configuration parameter can be overridden on the command line:
```bash
./p2rank_py predict -f protein.pdb -pred_min_cluster_size 5 -rf_trees 200
```

## 📊 Output Files

P2Rank generates several output files:

- **`protein_predictions.csv`**: Pocket predictions with scores
- **`protein_residues.csv`**: Per-residue pocket predictions
- **`visualizations/`**: PyMOL and ChimeraX visualization files
- **`params.txt`**: Parameters used for the run

## 🧪 Testing

Test the installation with provided examples:

```bash
# Basic functionality test
./p2rank_py predict -f test_data/1fbl.pdb -o test_output/

# Test different configurations
./p2rank_py predict -f test_data/1fbl.pdb -c alphafold -o test_alphafold/
```

## 🔍 Troubleshooting

### Common Issues

1. **Python not found**
   ```
   Error: Python not found
   ```
   **Solution**: Install Python 3.8+ or set `P2RANK_PYTHON` environment variable:
   ```bash
   export P2RANK_PYTHON=/usr/bin/python3.9
   ```

2. **Missing dependencies**
   ```
   Error: Required Python packages not found
   ```
   **Solution**: Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration file not found**
   ```
   Error: Configuration file not found
   ```
   **Solution**: Check available configs:
   ```bash
   ls config/
   ```

4. **Permission denied (Linux/macOS)**
   ```bash
   chmod +x p2rank_py
   ```

### Verbose Mode
Use `-v` flag for detailed debugging information:
```bash
./p2rank_py predict -f protein.pdb -v
```

## 🌟 Features

- **Cross-platform**: Works on Linux, macOS, and Windows
- **Easy installation**: No compilation required
- **Fast execution**: Optimized with NumPy and SciPy
- **Flexible configuration**: YAML-based configuration system
- **Multiple models**: Support for different pre-trained models
- **Rich output**: Comprehensive prediction results and visualizations

## 📚 Documentation

- **Original P2Rank**: https://github.com/rdk/p2rank
- **Python Implementation**: Documentation included in this package
- **Configuration Reference**: See `config/` directory for examples

## 🐛 Support

For issues and questions:

1. Check the troubleshooting section above
2. Verify your Python version and dependencies
3. Run with `-v` flag for detailed error information
4. Consult the original P2Rank documentation

## 📄 License

This software is distributed under the same license as the original P2Rank.
See `LICENSE.txt` for details.

## 🙏 Acknowledgments

This Python implementation is based on the original P2Rank tool developed by the Laboratory of Bioinformatics at Charles University.

**Original P2Rank Citation:**
> Krivák R, Hoksza D. P2Rank: machine learning based tool for rapid and accurate prediction of ligand binding sites from protein structure. Journal of Cheminformatics. 2018;10(1):39. 