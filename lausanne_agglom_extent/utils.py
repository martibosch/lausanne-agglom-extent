import geopandas as gpd
import numpy as np
from rasterio import features, transform

# ugly hardcoded values extracted from the Swiss GMB agglomeration boundaries
WEST, SOUTH, EAST, NORTH = (2512518, 1146825, 2558887, 1177123)

# ugly hardcoded CRS to avoid issues with pyproj versions
CRS = 'epsg:2056'

# lulc column in Vaud's cadastre shapefile
CADASTRE_LULC_COLUMN = 'GENRE'

# other lulc values
URBAN_CLASSES = list(range(8))
LULC_WATER_VAL = 14


def _lausanne_reclassify(value, dst_nodata):
    if value < 0:
        return dst_nodata
    if value >= 9:
        return value - 1
    else:
        return value


def rasterize_cadastre(cadastre_filepath, dst_res, dst_nodata):

    cadastre_transform = transform.from_origin(WEST + dst_res // 2,
                                               NORTH - dst_res // 2, dst_res,
                                               dst_res)
    cadastre_gdf = gpd.read_file(cadastre_filepath,
                                 bbox=(WEST, SOUTH, EAST, NORTH))
    cadastre_ser = cadastre_gdf[CADASTRE_LULC_COLUMN].apply(
        _lausanne_reclassify, args=(dst_nodata, ))

    cadastre_shape = ((NORTH - SOUTH) // dst_res, (EAST - WEST) // dst_res)
    cadastre_arr = features.rasterize(
        ((geom, value)
         for geom, value in zip(cadastre_gdf['geometry'], cadastre_ser)),
        out_shape=cadastre_shape,
        fill=dst_nodata,
        transform=cadastre_transform,
        dtype=np.uint8)

    return cadastre_arr, cadastre_transform
