from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

import numpy as np

try:
    import aarwild_bpy.funcs as F
    import bpy
    import bmesh
except:
    pass

@dataclass
class Edge:
    index: int
    v1_ind: int
    v2_ind: int
    v1_co: np.ndarray
    v2_co: np.ndarray
    midpoint: np.array
    direction: np.array
    length: float

    def cross(self, other: Edge) -> np.array:
        return np.cross(self.direction, other.direction)

    def distance_to_point(self, point: np.array) -> float:
        """
        Perpendicular distance from Edge to `point`
        """
        d = self.direction
        v = point - self.v1_co
        return np.linalg.norm(np.cross(v, d))

    def distance_to_edge(self, other: Edge) -> float:
        """
        Euclidean distance from midpoint of self to
        midpoint of `other` edge
        """
        return np.linalg.norm(self.midpoint - other.midpoint)

    def to_dict(self):
        return {
            'index': self.index,
            'v1_ind': self.v1_ind,
            'v2_ind': self.v2_ind,
            'v1_co': self.v1_co.tolist(),
            'v2_co': self.v2_co.tolist(),
            'midpoint': self.midpoint.tolist(),
            'direction': self.direction.tolist(),
            'length': self.length
        }

    @classmethod
    def from_dict(cls, edge_dict):
        index = edge_dict['index']
        v1_ind = edge_dict['v1_ind']
        v2_ind = edge_dict['v2_ind']
        v1_co = np.array(edge_dict['v1_co'])
        v2_co = np.array(edge_dict['v2_co'])
        mid = np.array(edge_dict['midpoint'])
        direction = np.array(edge_dict['direction'])
        length = edge_dict['length']
        return cls(index, v1_ind, v2_ind, v1_co, v2_co, mid, direction, length)

def _compute_boundary_edges(obj) -> List[Edge]:
    bpy.ops.object.select_all(action='DESELECT')
    F.make_active(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    mesh = obj.data
    W = obj.matrix_world
    bm = bmesh.from_edit_mesh(mesh)
    boundary_edges = []
    for e in bm.edges:
        if not e.is_boundary:
            continue
        v1, v2 = e.verts
        v1_co = np.array(W @ v1.co)
        v2_co = np.array(W @ v2.co)
        midpoint = 0.5 * (v1_co + v2_co)
        delta = np.array(v2_co - v1_co)
        direction = delta / np.linalg.norm(delta)
        length = np.linalg.norm(delta)
        edge = Edge(e.index, v1.index, v2.index, v1_co, v2_co, midpoint, direction, length)
        boundary_edges.append(edge)
    bm.free()
    bpy.ops.object.mode_set(mode='OBJECT')
    return boundary_edges

def _overlap(e1: Edge, e2: Edge) -> bool:
    return np.allclose(e1.cross(e2), 0) \
        and e1.distance_to_point(e2.midpoint) < (e1.length / 10) \
        and e1.distance_to_edge(e2) < e1.length

def _compute_shared_verts(label1: str, edges1: List[Edge],
                      label2: str, edges2: List[Edge]) -> Dict:

    # with open('_boundary_edges.json') as f:
    #     edges = json.load(f)
    # label1, label2 = 'Grid', 'Grid.001'
    # edges1 = [Edge.from_dict(d) for d in edges[label1]]
    # edges2 = [Edge.from_dict(d) for d in edges[label2]]

    shared_verts1 = set()
    shared_verts2 = set()

    obj1_edges = bpy.data.objects[label1].data.edges
    obj2_edges = bpy.data.objects[label2].data.edges
    for e1 in edges1:
        for e2 in edges2:
            if _overlap(e1, e2):
                v1, v2 = obj1_edges[e1.index].vertices
                shared_verts1.add(v1)
                shared_verts1.add(v2)
                v3, v4 = obj2_edges[e2.index].vertices
                shared_verts2.add(v3)
                shared_verts2.add(v4)

    return {label1: shared_verts1, label2: shared_verts2}

def _insert_vertices_into_sparse_boundary(edges_map: Dict,
                                          sparse_bdry_label: str,
                                          dense_bdry_label) -> None:
    # Create Bmesh object to edit the mesh
    # of the object with sparse boundary
    sparse_bdry_obj = bpy.data.objects[sparse_bdry_label]
    Wsi = sparse_bdry_obj.matrix_world.inverted_safe()
    F.make_active(sparse_bdry_obj)
    bpy.ops.object.mode_set(mode='EDIT')
    me = sparse_bdry_obj.data
    bm = bmesh.from_edit_mesh(me)

    # Loop through the vertices of dense boundary
    # and add vertex to the sparse boundary
    dense_bdry_obj = bpy.data.objects[dense_bdry_label]
    Wd = dense_bdry_obj.matrix_world
    dense_bdry_vert_idx = edges_map[dense_bdry_label]

    for idx in dense_bdry_vert_idx:
        vd = dense_bdry_obj.data.vertices[idx]
        vs = Wsi @ (Wd @ vd.co)
        print(f'Inserted verted in object: {sparse_bdry_label} at: {vs}')
        bm.verts.new(vs)

    bmesh.update_edit_mesh(me)

def main() -> None:
    if bpy.context.object and bpy.context.object.mode == 'EDIT':
        bpy.ops.object.mode_set(mode='OBJECT')

    num_selected = len(bpy.context.selected_objects)
    if num_selected != 2:
        raise ValueError(f'Need to select exactly two objects, found {num_selected} selected')

    bdry_edges_map = {}
    for obj in bpy.context.selected_objects:
        bdry_edges_map[obj.name] = _compute_boundary_edges(obj)

    bdry_edges_sz = {k: [e.to_dict() for e in v] for k, v in bdry_edges_map.items()}
    with Path('_boundary_edges.json').open('w') as f:
        json.dump(bdry_edges_sz, f, indent=2)

    # Get shared edges of two boundaries
    label1, label2 = list(bdry_edges_map.keys())[:2]
    edges1 = bdry_edges_map[label1]
    edges2 = bdry_edges_map[label2]
    verts_on_shared_bdry = _compute_shared_verts(label1, edges1, label2, edges2)

    # Add points to boundary containing less number of vertices
    n1 = len(verts_on_shared_bdry[label1])
    n2 = len(verts_on_shared_bdry[label2])
    if n1 < n2:
        sparse_bdry_label, dense_bdry_label = label1, label2
    else:
        sparse_bdry_label, dense_bdry_label = label2, label1

    _insert_vertices_into_sparse_boundary(
        verts_on_shared_bdry,
        sparse_bdry_label,
        dense_bdry_label
    )

    # # Highlight selected edges
    # name = label2
    # obj = bpy.data.objects[name]
    # F.make_active(obj)
    # bpy.ops.object.mode_set(mode='EDIT')
    # me = obj.data
    # bm = bmesh.from_edit_mesh(me)
    # bpy.ops.mesh.select_all(action='DESELECT')
    # bm.verts.ensure_lookup_table()
    # for vidx in verts_on_shared_bdry[name]:
    #     bm.verts[vidx].select = True
    # bmesh.update_edit_mesh(me)
    # # F.write_blendfile('_mesh.blend', relative_paths=False)
    # bm.free()

if __name__ == '__main__':
    main()
    # _get_shared_verts('', [], '', [])
