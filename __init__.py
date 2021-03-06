# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PlaceImageByCoordinates
                                 A QGIS plugin
 This plugin places images by coordinates
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-10-23
        copyright            : (C) 2020 by Kouki Kitajima
        email                : kitajim@wisc.edu
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PlaceImageByCoordinates class from file PlaceImageByCoordinates.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .pibc import PlaceImageByCoordinates
    return PlaceImageByCoordinates(iface)
