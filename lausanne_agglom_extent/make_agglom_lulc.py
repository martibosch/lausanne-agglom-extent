import logging

import click
import geopandas as gpd
import numpy as np
import rasterio as rio
import urban_footprinter as ufp
from rasterio import features, transform, windows
from scipy import ndimage as ndi
from shapely import geometry

# ugly hardcoded values extracted from the Swiss GMB agglomeration boundaries
WEST, SOUTH, EAST, NORTH = (2512518, 1146825, 2558887, 1177123)

# ugly hardcoded CRS to avoid issues with pyproj versions
CRS = 'epsg:2056'

# lulc column in Vaud's cadastre shapefile
CADASTRE_LULC_COLUMN = 'GENRE'

# other lulc values
URBAN_CLASSES = list(range(8))
LULC_WATER_VAL = 14

# sieve to clean isolated land pixels in the lake
SIEVE_SIZE = 10


def lausanne_reclassify(value, dst_nodata_val):
    if value < 0:
        return dst_nodata_val
    if value >= 9:
        return value - 1
    else:
        return value


@click.command()
@click.argument('cadastre_filepath', type=click.Path(exists=True))
@click.argument('dst_tif_filepath', type=click.Path())
@click.argument('dst_shp_filepath', type=click.Path())
@click.option('--dst-res', type=int, default=10, required=False)
@click.option('--num-patches', type=int, default=1, required=False)
@click.option('--kernel-radius', type=int, default=500, required=False)
@click.option('--urban-threshold', type=float, default=.15, required=False)
@click.option('--buffer-dist', type=int, default=1000, required=False)
@click.option('--dst-nodata-val', type=int, default=255, required=False)
def main(cadastre_filepath, dst_tif_filepath, dst_shp_filepath, dst_res,
         num_patches, kernel_radius, urban_threshold, buffer_dist,
         dst_nodata_val):
    logger = logging.getLogger(__name__)
    logger.info("preparing raster agglomeration LULC from %s",
                cadastre_filepath)

    cadastre_transform = transform.from_origin(WEST + dst_res // 2,
                                               NORTH - dst_res // 2, dst_res,
                                               dst_res)
    cadastre_gdf = gpd.read_file(cadastre_filepath,
                                 bbox=(WEST, SOUTH, EAST, NORTH))
    cadastre_ser = cadastre_gdf[CADASTRE_LULC_COLUMN].apply(
        lausanne_reclassify, args=(dst_nodata_val, ))

    cadastre_shape = ((NORTH - SOUTH) // dst_res, (EAST - WEST) // dst_res)
    cadastre_arr = features.rasterize(
        ((geom, value)
         for geom, value in zip(cadastre_gdf['geometry'], cadastre_ser)),
        out_shape=cadastre_shape,
        fill=dst_nodata_val,
        transform=cadastre_transform,
        dtype=np.uint8)
    logger.info("rasterized cadastre vector LULC dataset to shape %s",
                str(cadastre_shape))

    # get the urban extent mask according to the criteria used in the "Atlas
    # of Urban Expansion, The 2016 Edition" by Angel, S. et al.
    uf = ufp.UrbanFootprinter(cadastre_arr,
                              urban_classes=URBAN_CLASSES,
                              res=dst_res)
    urban_mask = uf.compute_footprint_mask(kernel_radius,
                                           urban_threshold,
                                           num_patches=num_patches,
                                           buffer_dist=buffer_dist)
    logger.info(
        "obtained extent of the %d largest urban cluster(s) (%d pixels)",
        num_patches, np.sum(urban_mask))

    # exclude lake
    # TODO: arguments to customize `LULC_WATER_VAL` and `SIEVE_SIZE`
    label_arr = ndi.label(cadastre_arr == LULC_WATER_VAL,
                          ndi.generate_binary_structure(2, 2))[0]
    cluster_label = np.argmax(np.unique(label_arr,
                                        return_counts=True)[1][1:]) + 1
    largest_cluster = np.array(label_arr == cluster_label, dtype=np.uint8)
    urban_mask = features.sieve(
        np.array(urban_mask.astype(bool) & ~largest_cluster.astype(bool),
                 dtype=urban_mask.dtype), SIEVE_SIZE)

    # get window and transform of valid data points, i.e., the computed extent
    extent_window = windows.get_data_window(urban_mask, nodata=0)
    extent_transform = windows.transform(extent_window, cadastre_transform)
    dst_arr = np.where(urban_mask, cadastre_arr,
                       dst_nodata_val)[windows.window_index(extent_window)]

    # dump it
    # ACHTUNG: use hardcoded CRS string (for the same CRS) to avoid issues
    with rio.open(
            dst_tif_filepath,
            'w',
            driver='GTiff',
            width=extent_window.width,
            height=extent_window.height,
            count=1,
            crs=CRS,  # cadastre_gdf.crs
            transform=extent_transform,
            dtype=np.uint8,
            nodata=dst_nodata_val) as dst:
        dst.write(dst_arr, 1)
    logger.info("dumped rasterized dataset to %s", dst_tif_filepath)

    if dst_shp_filepath:
        # save the geometry extent

        # get the urban mask geometry
        # urban_mask_geom = uf.compute_footprint_mask_shp(
        #     kernel_radius,
        #     urban_threshold,
        #     largest_patch_only=largest_patch_only,
        #     buffer_dist=buffer_dist,
        #     transform=extent_transform)
        urban_mask_geom = geometry.shape(
            max([(geom, val) for geom, val in features.shapes(
                np.array(dst_arr != dst_nodata_val, dtype=np.uint8),
                transform=extent_transform) if val == 1],
                key=lambda geom: len(geom[0]['coordinates']))[0])

        # get the window and transform of the lake extent
        lake_mask = features.sieve(largest_cluster, SIEVE_SIZE)
        extent_window = windows.get_data_window(lake_mask, nodata=0)
        extent_transform = windows.transform(extent_window, cadastre_transform)
        lake_mask = lake_mask[windows.window_index(extent_window)]

        # get the lake mask geometry
        lake_mask_geom = geometry.shape(
            max([(geom, val) for geom, val in features.shapes(
                lake_mask, transform=extent_transform) if val == 1],
                key=lambda geom: len(geom[0]['coordinates']))[0])

        # ACHTUNG: use hardcoded CRS string (for the same CRS) to avoid issues
        gpd.GeoSeries([urban_mask_geom, lake_mask_geom],
                      crs=CRS).to_file(dst_shp_filepath)
        logger.info("dumped extent geometry to %s", dst_shp_filepath)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    main()
