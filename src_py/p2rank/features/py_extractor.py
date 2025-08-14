"""
Python-native feature extraction (initial version).

This module computes a minimal subset of P2Rank-like features around protein atoms
as an approximation to SAS-point features. It is intended for pure-Python
inference and future training pipelines without Java.

Provided features per point (atom proxy):
- volsite.vsAromatic, vsCation, vsAnion, vsHydrophobic, vsAcceptor, vsDonor (local densities)
- protrusion.protrusion (local outwardness proxy)
- bfactor.bfactor (normalized)

Notes:
- Points are approximated by exposed atoms (heuristic). Future versions can adopt
  true SAS tessellation.
- Densities are computed in a spherical neighborhood with a configurable radius.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np
from Bio.PDB import PDBParser


@dataclass
class FeatureConfig:
    neighbor_radius: float = 6.0
    protrusion_radius: float = 10.0
    exposure_cutoff: float = 6.0  # distance to nearest neighbor defining exposure
    weight_sigma: float = 2.2


class PythonFeatureExtractor:
    def __init__(self, config: FeatureConfig | None = None):
        self.cfg = config or FeatureConfig()
        self._volsite_map = None

    def _load_volsite_map(self):
        if self._volsite_map is not None:
            return self._volsite_map
        vs_path = Path(__file__).resolve().parents[3] / 'tables' / 'volsite-atomic-properties.csv'
        mapping = {}
        try:
            with open(vs_path, 'r', encoding='utf-8') as f:
                header = f.readline()
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    parts = [p.strip() for p in line.split(',')]
                    if len(parts) < 7:
                        continue
                    key = parts[0].upper()  # e.g., ALA.CA
                    try:
                        vals = tuple(int(x) for x in parts[1:7])
                    except Exception:
                        # tolerate spacing issues
                        vals = tuple(int(x.strip()) for x in parts[1:7])
                    mapping[key] = vals
        except Exception:
            mapping = {}
        self._volsite_map = mapping
        return mapping

    def load_structure(self, pdb_path: Path) -> Tuple[np.ndarray, List[str], List[str], List[str], np.ndarray]:
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure("prot", str(pdb_path))
        coords: List[List[float]] = []
        resnames: List[str] = []
        atom_names: List[str] = []
        elements: List[str] = []
        bfactors: List[float] = []
        for atom in structure.get_atoms():
            try:
                c = atom.get_coord()
            except Exception:
                continue
            coords.append([float(c[0]), float(c[1]), float(c[2])])
            resnames.append(atom.get_parent().get_resname().strip().upper())
            try:
                atom_names.append(atom.get_name().strip().upper())
            except Exception:
                atom_names.append("")
            try:
                elements.append(atom.element.strip().upper())
            except Exception:
                elements.append("")
            try:
                bfactors.append(float(atom.get_bfactor()))
            except Exception:
                bfactors.append(0.0)
        if not coords:
            raise ValueError("No atoms parsed from structure")
        C = np.asarray(coords, dtype=np.float64)
        B = np.asarray(bfactors, dtype=np.float64)
        # normalize bfactor to 0..1
        bmin, bmax = float(np.min(B)), float(np.max(B))
        Bn = (B - bmin) / (bmax - bmin + 1e-12)
        return C, resnames, atom_names, elements, Bn

    def _classify_atom(self, res: str, atom_name: str, element: str) -> dict:
        res = (res or "").upper()
        atom_name = (atom_name or "").upper()
        element = (element or "").upper()
        # Prefer authoritative VolSite mapping from Java tables
        vs = self._load_volsite_map()
        key = f"{res}.{atom_name}"
        vals = vs.get(key)
        if vals is not None and len(vals) == 6:
            aromatic, cation, anion, hydrophobic, acceptor, donor = [bool(v) for v in vals]
        else:
            # fallback heuristics if mapping not found
            aromatic_res = {"PHE", "TYR", "TRP", "HIS"}
            cation_res = {"LYS", "ARG", "HIS"}
            anion_res = {"ASP", "GLU"}
            hydrophobic_res = {"ALA", "VAL", "LEU", "ILE", "MET", "PRO", "PHE", "TRP", "TYR"}
            donor_res = {"LYS", "ARG", "HIS", "SER", "THR", "TYR", "TRP", "ASN", "GLN"}
            acceptor_res = {"ASP", "GLU", "SER", "THR", "TYR", "TRP", "ASN", "GLN"}
            aromatic = (res in aromatic_res) and (element == 'C')
            cation = (res in cation_res)
            anion = (res in anion_res)
            hydrophobic = (res in hydrophobic_res) and (element == 'C')
            donor = ((element in {'N','O'}) and (res in donor_res))
            acceptor = ((element in {'O','N'}) and (res in acceptor_res))
        return {
            'aromatic': aromatic,
            'cation': cation,
            'anion': anion,
            'hydrophobic': hydrophobic,
            'acceptor': acceptor,
            'donor': donor,
        }

    def _estimate_exposure(self, coords: np.ndarray, pdb_path: Path | None = None) -> np.ndarray:
        # Prefer freesasa if available to estimate per-atom SASA and filter exposed atoms
        if pdb_path is not None:
            try:
                import freesasa  # type: ignore
                structure = freesasa.Structure(str(pdb_path))
                result = freesasa.calc(structure)
                sasas = np.array([result.atomArea(i).total for i in range(structure.nAtoms())], dtype=np.float64)
                thr = np.percentile(sasas, 35.0)
                return (sasas >= thr).astype(bool)
            except Exception:
                pass
        # fallback: exposed if NN distance above percentile threshold
        from sklearn.neighbors import NearestNeighbors
        nn = NearestNeighbors(n_neighbors=2, algorithm="auto").fit(coords)
        dists, _ = nn.kneighbors(coords, n_neighbors=2)
        nn_dist = dists[:, 1]
        thr = np.percentile(nn_dist, 65.0)
        return (nn_dist >= max(thr, self.cfg.exposure_cutoff)).astype(bool)

    def _neighbor_counts(self, labels: np.ndarray, center_idx: int, index: List[np.ndarray], dists: List[np.ndarray]) -> Tuple[float, ...]:
        # labels: N x 6 boolean array [aromatic,cation,anion,hydrophobic,acceptor,donor]
        nbrs = index[center_idx]
        if nbrs.size == 0:
            return (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
        sub = labels[nbrs]
        w = dists[center_idx]
        # exclude self (distance 0)
        mask = w > 1e-9
        if np.any(mask):
            nbrs = nbrs[mask]
            sub = labels[nbrs]
            w = w[mask]
        # Gaussian distance weight ~ Java params.weight_sigma
        sigma = max(1e-6, float(self.cfg.weight_sigma))
        weights = np.exp(-(w * w) / (2.0 * sigma * sigma))
        sw = weights.sum() + 1e-12
        return tuple(float((sub[:, i].astype(np.float64) * weights).sum() / sw) for i in range(6))

    def _build_radius_index(self, coords: np.ndarray) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        from sklearn.neighbors import KDTree
        if coords.shape[0] == 0:
            return [np.asarray([], dtype=int)], [np.asarray([], dtype=float)]
        tree = KDTree(coords)
        ind, dist = tree.query_radius(coords, r=self.cfg.neighbor_radius, return_distance=True, sort_results=False)
        return ind, dist

    def _query_radius_to_atoms(self, query_pts: np.ndarray, atom_coords: np.ndarray) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        from sklearn.neighbors import KDTree
        if atom_coords.shape[0] == 0 or query_pts.shape[0] == 0:
            empty_i = [np.asarray([], dtype=int) for _ in range(query_pts.shape[0])]
            empty_d = [np.asarray([], dtype=float) for _ in range(query_pts.shape[0])]
            return empty_i, empty_d
        tree = KDTree(atom_coords)
        ind, dist = tree.query_radius(query_pts, r=self.cfg.neighbor_radius, return_distance=True, sort_results=False)
        return ind, dist

    def _compute_normals(self, coords: np.ndarray, ind: List[np.ndarray]) -> np.ndarray:
        # local PCA normal: eigenvector of covariance with smallest eigenvalue
        N = coords.shape[0]
        normals = np.zeros((N, 3), dtype=np.float64)
        for i in range(N):
            nbr = ind[i]
            if nbr.size < 3:
                normals[i] = np.array([0.0, 0.0, 1.0])
                continue
            local = coords[nbr]
            c = local - local.mean(axis=0, keepdims=True)
            cov = c.T @ c / max(1, c.shape[0]-1)
            try:
                w, v = np.linalg.eigh(cov)
                n = v[:, 0]
            except Exception:
                n = np.array([0.0, 0.0, 1.0])
            # orient outward: from centroid of neighbors to point
            dirv = coords[i] - local.mean(axis=0)
            if np.dot(n, dirv) < 0:
                n = -n
            normals[i] = n / (np.linalg.norm(n) + 1e-12)
        return normals

    def _protrusion(self, coords: np.ndarray, ind: List[np.ndarray], normals: np.ndarray | None = None) -> np.ndarray:
        # protrusion: local outwardness along normal normalized by neighborhood spread
        N = coords.shape[0]
        out = np.zeros(N, dtype=np.float64)
        for i in range(N):
            nbr = ind[i]
            if nbr.size <= 1:
                out[i] = 0.0
                continue
            local = coords[nbr]
            centroid = np.mean(local, axis=0)
            v = coords[i] - centroid
            if normals is not None and normals.shape[0] == N:
                proj = abs(float(np.dot(v, normals[i])))
            else:
                proj = float(np.linalg.norm(v))
            spread = np.mean(np.linalg.norm(local - centroid, axis=1)) + 1e-12
            out[i] = proj / spread
        # normalize to 0..1 via min-max
        mn, mx = float(np.min(out)), float(np.max(out))
        return (out - mn) / (mx - mn + 1e-12)

    def extract(self, pdb_path: Path) -> np.ndarray:
        C, resnames, atom_names, elements, bnorm = self.load_structure(pdb_path)
        exposed = self._estimate_exposure(C, pdb_path)
        if not np.any(exposed):
            # fallback: keep top 30% by nearest-neighbor distance as exposed
            from sklearn.neighbors import NearestNeighbors
            nn = NearestNeighbors(n_neighbors=2).fit(C)
            d, _ = nn.kneighbors(C, n_neighbors=2)
            nn_dist = d[:, 1]
            thr = np.percentile(nn_dist, 70.0)
            exposed = (nn_dist >= thr)
            if not np.any(exposed):
                exposed[:] = True
        ind, dist = self._build_radius_index(C)
        labels = np.zeros((len(resnames), 6), dtype=bool)
        for i, rn in enumerate(resnames):
            d = self._classify_atom(rn, atom_names[i], elements[i])
            labels[i] = [d['aromatic'], d['cation'], d['anion'], d['hydrophobic'], d['acceptor'], d['donor']]
        # Build synthetic SAS points along estimated normals, scaled by probe distance
        normals = self._compute_normals(C, ind)
        probe = 1.4
        sas_pts = C + normals * probe
        # restrict to exposed atoms
        sas_pts = sas_pts[exposed]
        # volsite features for SAS points by querying atoms
        q_ind, q_dist = self._query_radius_to_atoms(sas_pts, C)
        feat_vs = np.zeros((sas_pts.shape[0], 6), dtype=np.float64)
        for i in range(sas_pts.shape[0]):
            # labels indexed in atom space
            if len(q_ind) > i:
                feat_vs[i] = self._neighbor_counts(labels, i, q_ind, q_dist)
        # protrusion among SAS points
        sp_ind, _ = self._build_radius_index(sas_pts)
        sp_normals = self._compute_normals(sas_pts, sp_ind)
        feat_pro = self._protrusion(sas_pts, sp_ind, sp_normals)[:, None]
        # bfactor for SAS point: nearest atom
        from sklearn.neighbors import NearestNeighbors
        nn = NearestNeighbors(n_neighbors=1).fit(C)
        d1, idx1 = nn.kneighbors(sas_pts, n_neighbors=1)
        feat_b = bnorm[idx1[:,0]][:, None]
        feats = np.hstack([feat_vs, feat_pro, feat_b])
        return feats


