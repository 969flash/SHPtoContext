# -*- coding:utf-8 -*-
try:
    from typing import List, Tuple, Dict, Any, Optional, Iterable
except ImportError:
    pass


import System
import clr

clr.AddReference("Grasshopper")
from Grasshopper.Kernel.Data import GH_Path
from Grasshopper import DataTree

import Grasshopper.Kernel as gh

we = gh.GH_RuntimeMessageLevel.Error
ww = gh.GH_RuntimeMessageLevel.Warning

try:
    import shapefile
except:
    message = "Python module 'pyshp' not found. Please download it and install to Rhino IronPython folder using manual at https://github.com/hiteca/ghshp"
    ghenv.Component.AddRuntimeMessage(we, message)
    message = "https://github.com/hiteca/ghshp#install-pyshp"
    ghenv.Component.AddRuntimeMessage(we, message)

import Rhino as rc


shape_types = {
    "point": [
        1,  # POINT
        8,  # MULTIPOINT
        11,  # POINTZ
        18,  # MULTIPOINTZ
        21,  # POINTM
        28,  # MULTIPOINTM
    ],
    "polyline": [
        3,  # POLYLINE
        5,  # POLYGON
        13,  # POLYLINEZ
        15,  # POLYGONZ
        23,  # POLYLINEM
        25,  # POLYGONM
        31,  # MULTIPATCH
    ],
}


def list2branch(source_tree, data, item_index, data_path):
    _p = GH_Path(data_path).AppendElement(item_index)
    for i in range(len(data)):
        _data = data[i]
        if type(_data) == list:
            soruce_tree = v2branch(source_tree, _data, i, _p)
        else:
            source_tree.AddRange([_data], GH_Path(_p))
    return source_tree


def py_tree(source_tree, reverse=False, default=None):
    if not reverse:
        result = {}
        for i in range(len(source_tree.Branches)):
            d = source_tree.Branches[i]
            p = GH_Path(source_tree.Paths[i])

            result[p] = list(d)
        if len(result.keys()) == 0:
            result[GH_Path(0)] = [default]
    else:
        result = DataTree[System.Object]()
        for p in source_tree.keys():
            d = source_tree[p]
            _d = []
            for j in range(len(d)):
                data = d[j]
                if type(data) == list:
                    result = list2branch(result, data, j, p)
                else:
                    _d.append(data)
            if len(_d) > 0:
                result.AddRange(_d, p)

    return result


def repeat_latest(data, length):
    if len(data) > length:
        return data[:length]
    else:
        return data + ([data[-1]] * (length - len(data)))


def graft_tree(t):
    r = {}
    for k, v in t.items():
        for i in range(len(v)):
            r[GH_Path(k).AppendElement(i)] = [v[i]]
    return r


def longest_list(t_a, t_b):
    r_b = {}
    r_a = {}
    prev_a = t_a.items()[0][1]
    prev_b = t_b.items()[0][1]

    if len(t_a) >= len(t_b):
        keys = t_a.keys()
    else:
        keys = t_b.keys()

    keys = sorted(keys, key=lambda x: str(GH_Path(x)))

    for k in keys:
        try:
            branch_a = t_a[k]
            prev_a = t_a[k]
        except:
            branch_a = prev_a
        try:
            branch_b = t_b[k]
            prev_b = t_b[k]
        except:
            branch_b = prev_b
        max_len = max(len(branch_b), len(branch_a))
        if len(branch_b) >= len(branch_a):
            branch_a = repeat_latest(branch_a, len(branch_b))
        else:
            branch_b = repeat_latest(branch_b, len(branch_a))
        r_a[k] = branch_a
        r_b[k] = branch_b

    return (r_a, r_b)


def find_type(t):
    for k in shape_types.keys():
        if t in shape_types[k]:
            return k


def list2point(pt):
    pt = list(pt)
    if len(pt) == 2:
        pt.append(0)
    return rc.Geometry.Point3d(pt[0], pt[1], pt[2])


def read_shapefile(sf, enc="utf-8"):
    """
    Reads a shapefile and extracts geometry and attribute data.
    Parameters:
    file_path (str): The path to the shapefile.
    read_data (bool): If True, reads attribute data from the shapefile. Default is True.
    read_geom (bool): If True, reads geometry data from the shapefile. Default is True.
    enc (str): The encoding to use for reading string data. Default is "utf-8".
    Returns:
    tuple: A tuple containing:
        - [sf.shapeType] (list): The type of shapes in the shapefile.
        - result_geom (list): A list of geometries extracted from the shapefile.
        - result_fields (list): A list of field definitions from the shapefile.
        - result_field_names (list): A list of field names from the shapefile.
        - result_records (list): A list of attribute records from the shapefile.
    """

    result_geom = []
    result_fields = []
    result_field_names = []
    result_records = []

    sf_type = find_type(sf.shapeType)
    # 필드 출력
    shpfields = sf.fields
    shprecords = sf.records()
    f = 0
    if str(sf.fields[0][0]).startswith("DeletionFlag"):
        shpfields.pop(0)  # remove DeletionFlag field

    for i in range(len(shpfields)):
        _shpfields = shpfields[i]
        _field = _shpfields[0]
        _field_type = _shpfields[1]
        _field_len = _shpfields[2]

        if isinstance(_field, str):
            _field = bytes(_field, "utf-8")

        _field = _field.decode(enc, errors="replace")

        result_field_names.append(_field)
        field = "%s;%s;%d" % (_field, _field_type, _field_len)
        result_fields.append(field)

    # 폴리라인 및 데이터 출력
    shapes = sf.shapes()

    for i in range(len(shapes)):
        path = GH_Path(i)

        # 지오메트리 읽기
        shape = shapes[i]
        # 부분으로 나누기

        if sf_type == "point":
            parts = shape.points
            pt_list = []
            for p in range(len(parts)):
                pt = list(parts[p])
                pt_list.append(list2point(pt))
            result_geom.append(pt_list)
        else:
            parts = shape.parts
            parts2 = parts[:]  # copy
            parts2.append(len(shape.points))
            part = []
            for p in range(len(parts)):
                points = []
                _p = p + 1
                for n in range(len(shape.points)):
                    if n < parts2[_p] and n >= parts2[p]:
                        pt = shape.points[n]
                        points.append(list2point(pt))

                polylinecurve = rc.Geometry.PolylineCurve(points)
                part.append(polylinecurve)
            result_geom.append(part)

        rec = shprecords[i]
        _result_records = []
        for r in range(len(sf.fields)):
            if str(sf.fields[0][0]).startswith("DeletionFlag") and r == 0:
                continue
            record = rec[r]
            if isinstance(record, str):
                record = bytes(record, "utf-8")
                record = record.decode(enc, errors="replace")

            _result_records.append(record)
        result_records.append(_result_records)

    return (
        [sf.shapeType],
        result_geom,
        result_fields,
        result_field_names,
        result_records,
    )


def extract_data_from_shapefile(shapefile):
    """
    Extracts data from a shapefile.
    Parameters:
    path (str): The file path(s) to the shapefile(s).
    """

    _sf_type, _geom, _fields, _field_names, _records = read_shapefile(shapefile)

    return ShpData(_sf_type, _geom, _fields, _field_names, _records)


class ShpData:
    def __init__(self, shape_type, geometry, fields, field_names, records):
        self.shape_type = shape_type
        self.geometry = geometry
        self.fields = fields
        self.field_names = field_names
        self.records = records
