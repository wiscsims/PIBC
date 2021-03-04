# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PIBC - Place Images By Coordinates
                                 A QGIS plugin
 This plugin places images by coordinates
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2020-10-23
        git sha              : $Format:%H$
        copyright            : (C) 2020 by Kouki Kitajima
        email                : kitajima@wisc.edu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os.path
import sys
import glob

from osgeo import gdal

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction

# Initialize Qt resources from file resources.py
from .resources import *  # noqa: F401,F403
# Import the code for the dialog
from .pibc_dialog import PlaceImageByCoordinatesDialog

# Import modules
from .modules.WorldFileTool.worldFileTool import WorldFileTool


class PlaceImageByCoordinates:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'PlaceImageByCoordinates_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&WiscSIMS')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        self.wft = WorldFileTool()

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PlaceImageByCoordinates', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/pibc/img/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'PIBC'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&PIBC'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):
        """Run method that performs all the real work"""

        # load classes of imaging instruments
        self.instruments = self.load_instruemnt_modules()

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start is True:
            self.first_start = False
            self.dlg = PlaceImageByCoordinatesDialog()

        # set list of instruments combobox in the dialog
        parser_list = list(self.instruments.keys())
        self.dlg.set_instruments(parser_list)

        # set the dialog as a modal window
        self.dlg.setModal(True)

        # show the dialog
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()

        if not result:
            return

        # get selected values by user
        self.importing_params = self.dlg.res_values

        img_exts = [
            'jpg', 'JPG', 'JPEG' 'jpeg', 'Jpeg'
            'PNG', 'png',
            'tif', 'TIF', 'tiff', 'TIFF'
        ]
        imgs = []

        # get image list from giving img_dir
        for ext in img_exts:
            imgs += glob.glob(f'{self.importing_params["image"]}/*.{ext}')

        # set parser class for the instrument and instantiate
        my_inst = self.importing_params['instrument']
        cls = getattr(self.instruments[my_inst], my_inst)
        parser = cls()

        # get meta data
        my_imgs = {}
        image_x, image_y = [], []

        for img in imgs:
            idx = os.path.basename(img)
            metadata = parser.parse_meta_data(img, self.importing_params['meta'])

            if metadata is None:
                print(f'no meta information for {img}')
                continue

            my_imgs[idx] = metadata
            my_imgs[idx]['img_path'] = img
            img_right = my_imgs[idx]['x'] + my_imgs[idx]['w'] * my_imgs[idx]['pixelsize']['x']
            img_bottom = my_imgs[idx]['y'] - my_imgs[idx]['h'] * my_imgs[idx]['pixelsize']['y']
            image_x += [my_imgs[idx]['x'], img_right]
            image_y += [my_imgs[idx]['y'], img_bottom]

        x_max, x_min = max(image_x), min(image_x)
        y_max, y_min = max(image_y), min(image_y)
        total_w = x_max - x_min
        total_h = y_max - y_min
        x_center, y_center = 0, 0

        # normalize position
        if self.importing_params['shiftposition']:
            x_center = x_min + total_w / 2.0
            y_center = y_min + total_h / 2.0

        # create world files
        for idx in list(my_imgs.keys()):
            self.wft.save(
                my_imgs[idx]['img_path'],        # image path
                my_imgs[idx]['x'] - x_center,    # x coordinate
                my_imgs[idx]['y'] - y_center,    # y coordinate
                my_imgs[idx]['pixelsize']['x'],  # pixel size x
                my_imgs[idx]['pixelsize']['y'],  # pixel size y
                0                                # rotation
            )

        # Add imrges to canvas
        if self.importing_params['import'] == 'multi':
            # add images as multiple layers
            self.add_images_to_canvas(imgs)

        elif self.importing_params['import'] == 'virtual':
            # add images as a signle layer of virtual format
            self.add_virtual_layer_to_canvas(
                self.importing_params['image'], imgs)
        else:
            print('not imported')

    """
    Functions

    """

    def add_virtual_layer_to_canvas(self, img_dir, imgs):
        """create and add virtual layer from images"""

        layer_name = os.path.basename(img_dir)

        # create output file path from parent directory name
        # if file exists, add incremental number to the filename (filename-1)
        layer_name_original = layer_name
        i = 0
        while True:
            output_file_name = f'{layer_name}.vrt'
            output_file_path = os.path.join(img_dir, output_file_name)
            if not os.path.exists(output_file_path):
                break
            i += 1
            layer_name = f'{layer_name_original}-{i}'

        # create gdal command
        # cmd = '/Applications/QGIS3.14.app/Contents/MacOS/bin/gdalbuildvrt '
        # cmd = 'gdalbuildvrt '
        # cmd += '-resolution highest -r lanczos '
        # cmd += '-input_file_list "{}" "{}"'.format(list_file_path, output_file_path)
        #
        # # run gdal command
        # # os.system(cmd)
        # import subprocess
        # subprocess.check_output(
        #         cmd,
        #         stderr=subprocess.STDOUT,
        #         shell=True)
        # # os.system(cmd)
        # print(cmd)

        # create vrt file
        gdal_options = gdal.BuildVRTOptions(
            resolution='highest',
            resampleAlg=gdal.GRA_Lanczos,
        )
        gdal.BuildVRT(output_file_path, imgs, options=gdal_options)

        # add vrt file to canvas
        if os.path.exists(output_file_path):
            self.iface.addRasterLayer(output_file_path, layer_name)
        else:
            print('Error on gdalbuildvrt')

    def add_images_to_canvas(self, imgs):
        """Add image to the canvas"""

        # sort images reverse order
        # - good result when images have texts and scale bar at the bottom
        imgs.sort(reverse=True)
        for img_path in imgs:
            img_file_name = os.path.splitext(os.path.basename(img_path))[0]
            self.iface.addRasterLayer(img_path, img_file_name)

    def load_instruemnt_modules(self):
        """load modules for imaging istruments"""
        # get absolute path of instruments folder
        instrument_module_path = os.path.join(os.path.dirname(__file__), 'instruments')

        # append instrument_module_path to system path
        # python modules in the instruments folder can read only by name
        sys.path.append(instrument_module_path)

        # get python parse modules for imaging instruments
        lst = os.listdir(instrument_module_path)

        # import modules
        mdls = {}
        for l in lst:
            class_name = l[:-3]  # remove extension (.py)

            # excluding __init__ and other unwanted files
            if l[0:2] == '__':
                continue
            # excluding dot files
            if l[0] == '.':
                continue

            mdls[class_name] = __import__(class_name)

        return mdls
