# -*- coding:utf-8 -*-
try:
    from typing import List, Tuple, Dict, Any, Optional, Iterable
except ImportError:
    pass

import shapefile
import zipfile
import scriptcontext as sc
import shp_importer
import Rhino.Geometry as geo
import rhinoscriptsyntax as rs
import ghpythonlib.components as ghcomp  # ignore
import importlib

importlib.reload(shp_importer)

# path = > grasshopper 로부터 받아온 zip 파일 경로

RESOLUTION = 4


def get_projected_pt_on_mesh(pt, mesh):
    # type: (geo.Point3d, geo.Mesh) -> geo.Point3d | None
    # Z축 방향 레이 생성
    ray = geo.Ray3d(pt, geo.Vector3d(0, 0, -1))  # Z축 아래 방향
    t = geo.Intersect.Intersection.MeshRay(mesh, ray)

    if t >= 0:
        # 레이의 t 값으로 교차점 계산
        return ray.PointAt(t)

    ray = geo.Ray3d(pt, geo.Vector3d(0, 0, 1))  # Z축 윗 방향
    t = geo.Intersect.Intersection.MeshRay(mesh, ray)

    if t >= 0:
        # 레이의 t 값으로 교차점 계산
        return ray.PointAt(t)

    return None  # 교차가 없을 경우 None 반환


def get_vertices(crv):
    # type: (geo.Curve) -> List[geo.Point3d]
    """crv의 꼭지점 찾기"""
    vertices = []  # type: List[geo.Point3d]
    # 스팬의 모든 시작점 추가
    for i in range(crv.SpanCount):
        span_domain = crv.SpanDomain(i)
        span_start_pt = crv.PointAt(span_domain[0])
        vertices.append(span_start_pt)

    # 열린 커브는 끝점 추가.
    if not crv.IsClosed:
        vertices.append(crv.PointAtEnd)

    return vertices


def read_shapefile_from_zip(zip_path):

    zipshape = zipfile.ZipFile(zip_path, "r")

    # 등고선
    try:
        contour_shape = shapefile.Reader(
            shp=zipshape.open("N1L_F0010000.shp"),
            shx=zipshape.open("N1L_F0010000.shx"),
            dbf=zipshape.open("N1L_F0010000.dbf"),
            prj=zipshape.open("N1L_F0010000.dbf"),
        )
    except KeyError:
        contour_shape = shapefile.Reader(
            shp=zipshape.open("N3L_F0010000.shp"),
            shx=zipshape.open("N3L_F0010000.shx"),
            dbf=zipshape.open("N3L_F0010000.dbf"),
            prj=zipshape.open("N3L_F0010000.dbf"),
        )

    # 빌딩 정보
    try:
        building_shape = shapefile.Reader(
            shp=zipshape.open("N1A_B0010000.shp"),
            shx=zipshape.open("N1A_B0010000.shx"),
            dbf=zipshape.open("N1A_B0010000.dbf"),
            prj=zipshape.open("N1A_B0010000.dbf"),
        )
    except KeyError:
        building_shape = shapefile.Reader(
            shp=zipshape.open("N3A_B0010000.shp"),
            shx=zipshape.open("N3A_B0010000.shx"),
            dbf=zipshape.open("N3A_B0010000.dbf"),
            prj=zipshape.open("N3A_B0010000.dbf"),
        )

    # 도로영역 정보
    try:
        road_regions_shape = shapefile.Reader(
            shp=zipshape.open("N3A_A0010000.shp"),
            shx=zipshape.open("N3A_A0010000.shx"),
            dbf=zipshape.open("N3A_A0010000.dbf"),
            prj=zipshape.open("N3A_A0010000.dbf"),
        )
    except KeyError:
        raise ("NO ROAD REGION")
        # road_regions_shape = shapefile.Reader(
        #     shp=zipshape.open(".shp"),
        #     shx=zipshape.open(".shx"),
        #     dbf=zipshape.open(".dbf"),
        #     prj=zipshape.open(".dbf"),
        # )

    # 도로 중심선 정보
    try:
        road_centerlines_shape = shapefile.Reader(
            shp=zipshape.open("N3L_A0020000.shp"),
            shx=zipshape.open("N3L_A0020000.shx"),
            dbf=zipshape.open("N3L_A0020000.dbf"),
            prj=zipshape.open("N3L_A0020000.dbf"),
        )
    except KeyError:
        raise ("NO ROAD CENTER")
        # road_centerlines_shape = shapefile.Reader(
        #     shp=zipshape.open(".shp"),
        #     shx=zipshape.open(".shx"),
        #     dbf=zipshape.open(".dbf"),
        #     prj=zipshape.open(".dbf"),
        # )

    return contour_shape, building_shape, road_regions_shape, road_centerlines_shape


def create_contour_curves(contour_geometry_records):
    contour_crvs = []
    for contour_geom, contour_record in contour_geometry_records:
        contour_crvs.append(
            geo.PolylineCurve(
                [
                    geo.Point3d(
                        contour_geom[0].Point(pt_count).X,
                        contour_geom[0].Point(pt_count).Y,
                        contour_record[1],
                    )
                    for pt_count in range(contour_geom[0].SpanCount)
                ]
            )
        )
    return contour_crvs


def create_points_for_mesh(contour_crvs, resolution):
    pts_for_mesh = []
    for crv in contour_crvs:
        params = crv.DivideByLength(resolution, True)
        if params:
            pts_for_mesh.extend([crv.PointAt(param) for param in params])
    return pts_for_mesh


def create_building_breps(building_geometry_records, mesh_terrain):
    bldg_breps = []
    for building_geom, building_record in building_geometry_records:
        bldg_crv = building_geom[0]
        bldg_floor = building_record[5]
        vertices = get_vertices(bldg_crv)

        projected_pts = list(
            filter(
                None, [get_projected_pt_on_mesh(pt, mesh_terrain) for pt in vertices]
            )
        )
        if not projected_pts:
            continue

        min_z = min(pt.Z for pt in projected_pts)
        translation_vector = geo.Vector3d(0, 0, min_z - vertices[0].Z)
        bldg_crv.Translate(translation_vector)
        bldg_brep = geo.Extrusion.Create(bldg_crv, -bldg_floor * 3.5, True)
        bldg_breps.append(bldg_brep)
    return bldg_breps


# 1. zip 파일에서 shapefile 추출
contour_shape, building_shape, road_region_shape, road_centerline_shape = (
    read_shapefile_from_zip(path)
)

contour_data = shp_importer.extract_data_from_shapefile(contour_shape)
building_data = shp_importer.extract_data_from_shapefile(building_shape)
road_region_data = shp_importer.extract_data_from_shapefile(road_region_shape)
road_centerline_data = shp_importer.extract_data_from_shapefile(road_centerline_shape)

# 2. shp 파일로부터 데이터 추출
contour_data.geometry, contour_data.records
contour_geometry_records = list(zip(contour_data.geometry, contour_data.records))
building_geometry_records = list(zip(building_data.geometry, building_data.records))


# 3. 추출한 데이터로 등고선, 지형, 건물, 도로, 도로 중심선 생성
contour_crvs = create_contour_curves(contour_geometry_records)
pts_for_mesh = create_points_for_mesh(contour_crvs, RESOLUTION)
mesh_terrain = ghcomp.DelaunayMesh(pts_for_mesh)
bldg_breps = create_building_breps(building_geometry_records, mesh_terrain)

road_regions = [data[0] for data in road_region_data.geometry]
road_centerlines = [data[0] for data in road_centerline_data.geometry]
