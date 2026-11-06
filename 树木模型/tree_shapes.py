"""Branching miniature tree geometry, shared by the editable and web assets."""
import bpy
import math
import random
from mathutils import Vector

PALETTE = dict(camphor='829b6c', plane='93a879', ginkgo='b1b77b',
               willow='8aa58a', pine='6f917c', cedar='7b9b8b', blossom='b9ae9e')


def linear(h):
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [(v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4) for v in rgb]


def make_tree(species, compact, material):
    rng = random.Random(729 + list(PALETTE).index(species))
    verts, faces, colors, normals = [], [], [], []
    sides = 5 if compact else 7
    bark, base = linear('8d7e6b'), linear(PALETTE[species])

    def vertex(p, c, normal):
        verts.append((p[0], p[1], max(0, p[2])))
        colors.append(c)
        normals.append(normal)
        return len(verts) - 1

    def branch(a, b, radius, end_radius=None):
        a, b = Vector(a), Vector(b)
        axis = (b - a).normalized()
        guide = Vector((0, 1, 0)) if abs(axis.y) < .9 else Vector((1, 0, 0))
        u, w = axis.cross(guide).normalized(), None
        w = axis.cross(u).normalized()
        n, rows = (4 if compact else 5), []
        for p, r in [(a, radius), (b, end_radius if end_radius is not None else radius * .42)]:
            row = []
            for k in range(n):
                radial = u * math.cos(k * math.tau / n) + w * math.sin(k * math.tau / n)
                row.append(vertex(p + radial * r, bark, radial))
            rows.append(row)
        for k in range(n):
            j = (k + 1) % n
            faces.append((rows[0][k], rows[0][j], rows[1][j], rows[1][k]))
        faces.extend([tuple(reversed(rows[0])), tuple(rows[1])])

    def crown(center, radii, seed, tone=1, droop=False):
        # Irregular masses with explicit normals avoid pole pinching on low-poly crowns.
        cx, cy, cz = center
        rx, ry, rz = radii
        phase, rings = seed * 2.39996 + .53, []
        levels = [(-.66, .65), (-.02, 1), (.64, .67)]
        if droop:
            levels = [(-.7, .38), (-.08, .89), (.52, .82)]
        for level, width in levels:
            row = []
            for k in range(sides):
                a = math.tau * k / sides
                ripple = 1 + .13 * math.sin(3 * a + phase) + .07 * math.cos(2 * a - phase)
                x, y = math.cos(a) * width * ripple, math.sin(a) * width * ripple
                z = level + .11 * math.sin(2 * a + phase)
                p = (cx + rx * (x + .1 * level), cy + ry * (y - .08 * level), cz + rz * z)
                normal = Vector((x / rx, y / ry, z / rz)).normalized()
                normal = (normal * .9 + Vector((0, 0, .1))).normalized()
                shade = tone * (.94 + .045 * level + .025 * math.sin(a + phase))
                row.append(vertex(p, [c * shade for c in base], normal))
            rings.append(row)
        bottom = vertex((cx - .1 * rx, cy, cz - rz), [c * tone * .9 for c in base], Vector((0, 0, -1)))
        top = vertex((cx + .12 * rx, cy - .06 * ry, cz + rz), [c * tone for c in base], Vector((0, 0, 1)))
        for k in range(sides):
            j = (k + 1) % sides
            faces.extend([(bottom, rings[0][j], rings[0][k]), (rings[-1][k], rings[-1][j], top)])
        for lower, upper in zip(rings, rings[1:]):
            for k in range(sides):
                j = (k + 1) % sides
                faces.append((lower[k], lower[j], upper[j], upper[k]))

    # Each cluster is x,y,z,rx,ry,rz. Overlapping irregular lobes form a broad
    # silhouette while exposing forks and small gaps around the lower crown.
    clusters = {
        'camphor': [(0, 0, 2.8, .78, .71, .91), (-.64, -.2, 2.32, .7, .64, .68),
                    (.63, .05, 2.52, .68, .67, .79), (-.12, .58, 2.51, .72, .65, .74),
                    (.15, -.62, 2.18, .76, .6, .64), (-.52, .3, 3.02, .58, .55, .61),
                    (.48, -.38, 3.07, .53, .52, .63)],
        'plane': [(0, .04, 2.76, .83, .75, .68), (-.77, -.21, 2.42, .76, .67, .62),
                  (.75, .12, 2.48, .77, .64, .68), (-.2, .7, 2.34, .74, .66, .62),
                  (.16, -.73, 2.32, .76, .65, .61), (-.51, .25, 3.04, .65, .56, .57),
                  (.46, -.35, 3.05, .63, .54, .59)],
        'ginkgo': [(0, 0, 3.11, .7, .65, .65), (-.55, -.12, 2.7, .62, .55, .7),
                   (.55, .08, 2.85, .61, .56, .72), (-.13, .53, 2.88, .63, .55, .67),
                   (.18, -.54, 2.62, .64, .55, .69), (-.37, .2, 3.39, .52, .49, .52),
                   (.37, -.21, 3.46, .48, .48, .54)],
        'willow': [(0, 0, 2.76, .84, .74, .55), (-.72, -.15, 2.1, .55, .56, 1.05),
                   (.72, .13, 2.15, .58, .53, .98), (-.17, .7, 2.18, .6, .52, .98),
                   (.2, -.7, 1.97, .59, .49, 1.02), (-.46, .32, 2.63, .64, .58, .64),
                   (.4, -.31, 2.65, .64, .6, .63)],
        'pine': [(.23, .04, 3.29, .78, .66, .49), (-.68, -.23, 2.08, .85, .68, .39),
                 (.7, .12, 2.48, .81, .67, .42), (-.31, .53, 2.7, .8, .61, .4),
                 (.06, -.59, 2.78, .78, .57, .4), (-.34, -.09, 3.18, .6, .55, .42),
                 (.63, .26, 3.14, .57, .52, .38)],
        'cedar': [(-.02, .03, 3.46, .38, .35, .63), (-.51, -.09, 1.54, .65, .63, .43),
                  (.47, .18, 1.75, .65, .57, .48), (-.09, -.42, 2.18, .64, .55, .48),
                  (.11, .31, 2.59, .57, .55, .51), (-.34, .1, 2.76, .47, .46, .5),
                  (.25, -.17, 3.09, .41, .4, .5)],
        'blossom': [(0, .07, 2.36, .76, .67, .64), (-.63, -.2, 2.05, .63, .6, .59),
                    (.62, .08, 2.13, .66, .57, .59), (-.13, .6, 2.09, .65, .58, .55),
                    (.18, -.57, 1.95, .64, .55, .54), (-.42, .2, 2.64, .54, .5, .51),
                    (.39, -.29, 2.64, .51, .49, .54)]
    }[species]
    if species == 'pine':
        bend = (.16, -.06, 1.68)
        branch((0, 0, 0), bend, .145, .095)
        branch(bend, (.32, .06, 3.28), .095, .035)
    elif species == 'cedar':
        bend = (.04, 0, 1.82)
        branch((0, 0, 0), bend, .135, .085)
        branch(bend, (-.04, .03, 3.67), .085, .02)
    else:
        bend = (.11, .02, 1.28)
        branch((0, 0, 0), bend, .14, .1)
        branch(bend, (-.06, .08, 2.45), .1, .04)
    for j in range(1, 3 if compact else 5):
        x, y, z, *_ = clusters[j]
        start = (.17, 0, z - .65) if species == 'pine' else (0, 0, z + .14) if species == 'cedar' else bend
        branch(start, (x, y, z + (.4 if species == 'willow' else -.1)), .065)
    for j in range(5 if compact else 7):
        x, y, z, rx, ry, rz = clusters[j]
        tone = .96 + rng.random() * .11
        crown((x, y, z), (rx, ry, rz), j + list(PALETTE).index(species), tone,
              droop=species == 'willow' and 0 < j < 5)

    name = species + ('_compact' if compact else '_full')
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material)
    attr = mesh.color_attributes.new(name='Color', type='BYTE_COLOR', domain='POINT')
    for i, c in enumerate(colors):
        attr.data[i].color = (*c, 1)
    for f in mesh.polygons:
        f.use_smooth = True
    mesh.normals_split_custom_set_from_vertices(normals)
    return obj
