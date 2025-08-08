"""
File utilities for P2Rank
"""
import os
import gzip
import zipfile
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class Futils:
    """File utility methods"""
    
    GZIP_DEFAULT_LEVEL = 6
    ZIP_BEST_COMPRESSION = 9
    BUFFER_SIZE = 128 * 1024
    COMPRESSED_EXTENSIONS = {"gz", "zst", "zip", "bz2"}
    
    @staticmethod
    def exists(path: str) -> bool:
        """Check if file exists"""
        return os.path.exists(path)
    
    @staticmethod
    def is_file(path: str) -> bool:
        """Check if path is a file"""
        return os.path.isfile(path)
    
    @staticmethod
    def is_directory(path: str) -> bool:
        """Check if path is a directory"""
        return os.path.isdir(path)
    
    @staticmethod
    def mkdirs(path: str):
        """Create directories if they don't exist"""
        os.makedirs(path, exist_ok=True)
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension"""
        return Path(filename).suffix.lstrip('.')
    
    @staticmethod
    def remove_extension(filename: str) -> str:
        """Remove file extension"""
        return str(Path(filename).with_suffix(''))
    
    @staticmethod
    def get_base_name(path: str) -> str:
        """Get base name of file"""
        return os.path.basename(path)
    
    @staticmethod
    def get_dir_name(path: str) -> str:
        """Get directory name"""
        return os.path.dirname(path)
    
    @staticmethod
    def write_file(filename: str, content: str):
        """Write string content to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"Error writing file {filename}: {e}")
            raise
    
    @staticmethod
    def read_file(filename: str) -> str:
        """Read file content as string"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {filename}: {e}")
            raise
    
    @staticmethod
    def read_lines(filename: str) -> List[str]:
        """Read file content as list of lines"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.readlines()
        except Exception as e:
            logger.error(f"Error reading lines from {filename}: {e}")
            raise
    
    @staticmethod
    def load_properties(resource_path: str) -> Dict[str, str]:
        """Load properties from resource path"""
        # In Java this would load from classpath, in Python we'll load from file
        try:
            # Remove leading slash for Python path handling
            if resource_path.startswith('/'):
                resource_path = resource_path[1:]
            
            # Try to load as JSON first (more Pythonic)
            if resource_path.endswith('.json'):
                with open(resource_path, 'r') as f:
                    return json.load(f)
            
            # Load as simple key=value properties
            props = {}
            if os.path.exists(resource_path):
                with open(resource_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                props[key.strip()] = value.strip()
            return props
        except Exception as e:
            logger.warning(f"Could not load properties from {resource_path}: {e}")
            return {}
    
    @staticmethod
    def read_resource(resource_path: str) -> str:
        """Read resource file content"""
        try:
            # Remove leading slash for Python path handling
            if resource_path.startswith('/'):
                resource_path = resource_path[1:]
            
            # Try to find in package resources
            import pkg_resources
            try:
                return pkg_resources.resource_string('p2rank', resource_path).decode('utf-8')
            except:
                # Fall back to regular file reading
                return Futils.read_file(resource_path)
        except Exception as e:
            logger.error(f"Error reading resource {resource_path}: {e}")
            return ""
    
    @staticmethod
    def is_compressed(filename: str) -> bool:
        """Check if file is compressed based on extension"""
        ext = Futils.get_file_extension(filename).lower()
        return ext in Futils.COMPRESSED_EXTENSIONS
    
    @staticmethod
    def open_file(filename: str, mode: str = 'r'):
        """Open file, automatically handling compression"""
        if filename.endswith('.gz'):
            return gzip.open(filename, mode + 't', encoding='utf-8')
        else:
            return open(filename, mode, encoding='utf-8')
    
    @staticmethod
    def zip_and_delete(filename: str, compression_level: int = ZIP_BEST_COMPRESSION):
        """Zip file and delete original"""
        try:
            zip_filename = filename + '.zip'
            with zipfile.ZipFile(zip_filename, 'w', 
                               compression=zipfile.ZIP_DEFLATED,
                               compresslevel=compression_level) as zipf:
                zipf.write(filename, os.path.basename(filename))
            
            os.remove(filename)
            logger.info(f"Compressed {filename} to {zip_filename}")
        except Exception as e:
            logger.error(f"Error compressing {filename}: {e}")
    
    @staticmethod
    def safe_delete(filename: str) -> bool:
        """Safely delete file"""
        try:
            if os.path.exists(filename):
                os.remove(filename)
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting {filename}: {e}")
            return False
    
    @staticmethod
    def dir(path: str) -> str:
        """Get directory of path"""
        return os.path.dirname(os.path.abspath(path)) 