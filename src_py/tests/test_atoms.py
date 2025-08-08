"""
Test cases for Atoms class
"""
import unittest
import tempfile
import os
from pathlib import Path

from p2rank.geom.atoms import Atoms
from p2rank.geom.point import Point, Atom
from p2rank.domain.protein import Protein


class MockAtom(Atom):
    """Mock atom implementation for testing"""
    
    def __init__(self, x: float, y: float, z: float, pdb_serial: int = 0, element: str = "C"):
        self.coords = [x, y, z]
        self.pdb_serial = pdb_serial
        self.element = element
    
    def get_coords(self):
        return self.coords
    
    def get_pdb_serial(self) -> int:
        return self.pdb_serial
    
    def get_element(self) -> str:
        return self.element


class TestAtoms(unittest.TestCase):
    """Test cases for Atoms class"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create some test atoms
        self.atom1 = MockAtom(0.0, 0.0, 0.0, 1)
        self.atom2 = MockAtom(1.0, 0.0, 0.0, 2)
        self.atom3 = MockAtom(0.0, 1.0, 0.0, 3)
        self.atom4 = MockAtom(5.0, 5.0, 5.0, 4)
        
        self.atoms = Atoms([self.atom1, self.atom2, self.atom3, self.atom4])
    
    def test_constructor(self):
        """Test Atoms constructor"""
        # Empty constructor
        empty_atoms = Atoms()
        self.assertEqual(empty_atoms.count, 0)
        self.assertTrue(empty_atoms.empty)
        
        # Constructor with list
        atoms_from_list = Atoms([self.atom1, self.atom2])
        self.assertEqual(atoms_from_list.count, 2)
        self.assertFalse(atoms_from_list.empty)
        
        # Constructor from another Atoms object
        atoms_copy = Atoms(atoms_from_list)
        self.assertEqual(atoms_copy.count, 2)
    
    def test_add_and_remove(self):
        """Test adding and removing atoms"""
        atoms = Atoms()
        self.assertEqual(atoms.count, 0)
        
        # Add atom
        atoms.add(self.atom1)
        self.assertEqual(atoms.count, 1)
        self.assertIn(self.atom1, atoms.list)
        
        # Add multiple atoms
        atoms.add_all([self.atom2, self.atom3])
        self.assertEqual(atoms.count, 3)
        
        # Remove atom
        removed = atoms.remove(self.atom1)
        self.assertTrue(removed)
        self.assertEqual(atoms.count, 2)
        self.assertNotIn(self.atom1, atoms.list)
        
        # Try to remove non-existent atom
        removed = atoms.remove(self.atom4)
        self.assertFalse(removed)
        self.assertEqual(atoms.count, 2)
    
    def test_with_index(self):
        """Test index building"""
        atoms = Atoms([self.atom1, self.atom2, self.atom3])
        
        # Build index
        atoms.with_index()
        
        # Test contains
        self.assertTrue(atoms.contains(self.atom1))
        self.assertTrue(atoms.contains(self.atom2))
        self.assertFalse(atoms.contains(self.atom4))
        
        # Test get_by_id
        found_atom = atoms.get_by_id(2)
        self.assertEqual(found_atom, self.atom2)
        
        not_found = atoms.get_by_id(999)
        self.assertIsNone(not_found)
    
    def test_centroid(self):
        """Test centroid calculation"""
        # Simple case with known centroid
        atoms = Atoms([
            MockAtom(0.0, 0.0, 0.0),
            MockAtom(2.0, 0.0, 0.0),
            MockAtom(1.0, 2.0, 0.0)
        ])
        
        centroid = atoms.get_centroid()
        self.assertAlmostEqual(centroid.x, 1.0, places=5)
        self.assertAlmostEqual(centroid.y, 2.0/3, places=5)
        self.assertAlmostEqual(centroid.z, 0.0, places=5)
    
    def test_cutout_sphere(self):
        """Test cutout sphere functionality"""
        atoms = Atoms([self.atom1, self.atom2, self.atom3, self.atom4])
        
        # Cutout sphere around origin with radius 2.0
        center = Point(0.0, 0.0, 0.0)
        sphere_atoms = atoms.cutout_sphere(center, 2.0)
        
        # Should include atom1, atom2, atom3 but not atom4 (which is at 5,5,5)
        self.assertEqual(sphere_atoms.count, 3)
        self.assertIn(self.atom1, sphere_atoms.list)
        self.assertIn(self.atom2, sphere_atoms.list)
        self.assertIn(self.atom3, sphere_atoms.list)
        self.assertNotIn(self.atom4, sphere_atoms.list)
    
    def test_cutout_shell(self):
        """Test cutout shell functionality"""
        atoms = Atoms([self.atom1, self.atom2, self.atom3, self.atom4])
        shell_atoms = Atoms([self.atom1])  # Shell around atom1
        
        result = atoms.cutout_shell(shell_atoms, 1.5)
        
        # Should include atoms within 1.5 distance of atom1
        self.assertIn(self.atom1, result.list)
        self.assertIn(self.atom2, result.list)  # distance = 1.0
        self.assertIn(self.atom3, result.list)  # distance = 1.0
        self.assertNotIn(self.atom4, result.list)  # distance > 1.5
    
    def test_to_points(self):
        """Test conversion to points"""
        atoms = Atoms([self.atom1, self.atom2])
        points = atoms.to_points()
        
        self.assertEqual(points.count, 2)
        for point in points:
            self.assertIsInstance(point, Point)
    
    def test_copy_points(self):
        """Test copy_points class method"""
        points = Atoms.copy_points(self.atom1, self.atom2)
        
        self.assertEqual(points.count, 2)
        for point in points:
            self.assertIsInstance(point, Point)
    
    def test_iteration(self):
        """Test iteration over atoms"""
        atom_list = [self.atom1, self.atom2, self.atom3]
        atoms = Atoms(atom_list)
        
        iterated_atoms = list(atoms)
        self.assertEqual(len(iterated_atoms), 3)
        self.assertEqual(iterated_atoms, atom_list)
    
    def test_kd_tree(self):
        """Test KD tree functionality"""
        atoms = Atoms([self.atom1, self.atom2, self.atom3, self.atom4])
        
        # Build KD tree
        atoms.with_kd_tree()
        kd_tree = atoms.get_kd_tree()
        self.assertIsNotNone(kd_tree)
        
        # Test conditional KD tree
        small_atoms = Atoms([self.atom1, self.atom2])  # Below threshold
        small_atoms.with_kd_tree_conditional()
        self.assertIsNone(small_atoms.get_kd_tree())
        
        large_atoms = Atoms([MockAtom(i, 0, 0, i) for i in range(20)])  # Above threshold
        large_atoms.with_kd_tree_conditional()
        self.assertIsNotNone(large_atoms.get_kd_tree())


if __name__ == '__main__':
    unittest.main() 