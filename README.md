[![GitHub license](https://img.shields.io/github/license/martibosch/lausanne-agglom-extent.svg)](https://github.com/martibosch/lausanne-agglom-extent/blob/master/LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.4311544.svg)](https://doi.org/10.5281/zenodo.4311544)

# Lausanne agglomeration extent

Computation of the spatial extent of the agglomeration of Lausanne with the [Urban footprinter](https://github.com/martibosch/urban-footprinter), which implements the methods proposed in the [Atlas of Urban Expansion](http://atlasofurbanexpansion.org/). More precisely, in this repository, a pixel is considered part of the urban extent when at least 15\% of the pixels that surround it (with a 500m radius) are of urban land use. The agglomeration extent shapefile as well as the land use/land cover raster file [can be downloaded from Zenodo](https://doi.org/10.5281/zenodo.4311544).

![Figure](reports/figures/spatial-extent.pdf)

## Use conditions

The obtained extent is based on the Official cadastral survey of the canton of Vaud whose exclusive owner is the canton of Vaud. In order to use this dataset, the source must be acknowledged as in:

> Source: Géodonnées Etat de Vaud

The use conditions from the dataset are disclosed in [the norm OIT 8401 (link in French)](https://dwa.vd.ch/prod/dinf/publicationdinf1_p.nsf/NORM/AB33A0F2E5159579C125712B0044F3F6/$FILE/8401.pdf?OpenElement).

## Acknowledgments

* **Source**: Géodonnées Etat de Vaud 
* With the support of the École Polytechnique Fédérale de Lausanne (EPFL)
* Project based on the [cookiecutter data science project template](https://drivendata.github.io/cookiecutter-data-science). #cookiecutterdatascience
