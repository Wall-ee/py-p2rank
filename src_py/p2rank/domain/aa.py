"""
20 main amino acid codes
"""
from enum import Enum
from typing import Optional, Dict


class AA(Enum):
    """Amino acid enumeration with single letter codes"""
    
    ALA = 'A'
    CYS = 'C'
    ASP = 'D'
    GLU = 'E'
    PHE = 'F'
    GLY = 'G'
    HIS = 'H'
    ILE = 'I'
    LYS = 'K'
    LEU = 'L'
    MET = 'M'
    ASN = 'N'
    PRO = 'P'
    GLN = 'Q'
    ARG = 'R'
    SER = 'S'
    THR = 'T'
    VAL = 'V'
    TRP = 'W'
    TYR = 'Y'
    
    def __init__(self, code_char: str):
        self.code_char = code_char
    
    @property
    def code(self) -> str:
        """3 letter uppercase code identical with the enum element name"""
        return self.name
    
    @classmethod
    def for_name(cls, name: str) -> Optional['AA']:
        """Get AA by 3-letter name"""
        try:
            return cls[name.upper()]
        except KeyError:
            return None
    
    @classmethod
    def for_code(cls, code: str) -> Optional['AA']:
        """Get AA by 3-letter code (same as for_name)"""
        return cls.for_name(code)
    
    @classmethod
    def for_code_char(cls, code_char: str) -> Optional['AA']:
        """Get AA by single letter code"""
        for aa in cls:
            if aa.code_char == code_char.upper():
                return aa
        return None
    
    @classmethod
    def is_standard_one_letter_code(cls, code_char: str) -> bool:
        """Check if single letter code is a standard amino acid"""
        return cls.for_code_char(code_char) is not None
    
    @classmethod
    def all_code_chars(cls) -> str:
        """Get all single letter codes as a string"""
        return ''.join([aa.code_char for aa in cls])


# Create lookup dictionaries for efficient access
_AA_BY_NAME: Dict[str, AA] = {aa.name: aa for aa in AA}
_AA_BY_CODE_CHAR: Dict[str, AA] = {aa.code_char: aa for aa in AA}

ALL_CODE_CHARS = AA.all_code_chars() 