import bpy
import bmesh

from mathutils import Vector
from bmesh.types import BMVert, BMEdge, BMFace
from ...utils import (
    select,
    filter_geom,
    calc_edge_median,
    calc_verts_median,
    filter_vertical_edges,
    filter_horizontal_edges
    )

def make_roof(bm, faces, type, **kwargs):
    select(faces, False)
    if type == 'FLAT':
        make_flat_roof(bm, faces, **kwargs)
    elif type == 'GABLE':
        make_gable_roof(bm, faces, **kwargs)
    elif type == 'HIP':
        make_hip_roof(bm, faces, **kwargs)

def make_flat_roof(bm, faces, thick, outset, **kwargs):

    ret = bmesh.ops.extrude_face_region(bm, geom=faces)
    bmesh.ops.translate(bm,
        vec=(0, 0, thick),
        verts=filter_geom(ret['geom'], BMVert))

    top_face = filter_geom(ret['geom'], BMFace)[-1]
    link_faces = [f for e in top_face.edges for f in e.link_faces
                    if f is not top_face]

    bmesh.ops.inset_region(bm, faces=link_faces, depth=outset, use_even_offset=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    bmesh.ops.delete(bm,
        geom=faces,
        context=5)


def make_gable_roof(bm, faces, thick, outset, height, orient, **kwargs):
    if not is_rectangular(faces):
        return

    # -- if more than one face, dissolve
    if len(faces) > 1:
        faces = bmesh.ops.dissolve_faces(bm,
            faces=faces, use_verts=True).get('region')

    # -- extrude the face to height
    ret = bmesh.ops.extrude_face_region(bm, geom=faces)
    verts = filter_geom(ret['geom'], BMVert)
    edges = filter_geom(ret['geom'], BMEdge)
    nfaces = filter_geom(ret['geom'], BMFace)
    bmesh.ops.translate(bm, verts=verts, vec=(0, 0, height))
    bmesh.ops.delete(bm, geom=faces + nfaces, context=3)

    # -- merge opposite verts
    axis = 'x' if orient == 'LEFT' else 'y'
    _max = max([v for e in edges for v in e.verts], key=lambda v: getattr(v.co, axis))
    _min = min([v for e in edges for v in e.verts], key=lambda v: getattr(v.co, axis))
    mid = getattr((_max.co + _min.co)/2, axis)
    for v in set([v for e in edges for v in e.verts]):
        setattr(v.co, axis, mid)
    bmesh.ops.remove_doubles(bm, verts=bm.verts)


def make_hip_roof(bm, faces, **kwargs):
    pass

def is_rectangular(faces):
    # -- determine if faces form a rectangular area
    face_area = sum([f.calc_area() for f in faces])

    verts = [v for f in faces for v in f.verts]
    verts = sorted(verts, key=lambda v: (v.co.x, v.co.y))

    _min, _max = verts[0], verts[-1]
    width = abs(_min.co.x - _max.co.x)
    length = abs(_min.co.y - _max.co.y)
    area = width * length

    if round(face_area, 4) == round(area, 4):
        return True
    return False