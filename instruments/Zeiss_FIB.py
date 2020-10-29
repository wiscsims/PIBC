import os.path
import re

from PIL import Image
from PIL.TiffTags import TAGS

 
class Zeiss_FIB:

    def __init__(self):
        pass

    def to_um(self, val, unit):
        if unit == 'um':
            return val
        if unit == 'mm':
            return val * 1000
        if unit == 'nm':
            return val / 1000

    def parse_meta_data(self, image_path, meta_dir=None):
        """parse meta data of image file"""

        # find embedded tag
        with Image.open(image_path) as img:
            metadata_key = 34118
            out = {}
            try:
                metadata = img.tag[metadata_key][0].split('\r\n')
            except KeyError:
                print('no meta keyes')
                return None
            for tag in metadata:
                tmp = re.split(r'\s+=\s+', tag)
                k = tmp[0].strip()
                v = ''
                if len(tmp) == 2:
                    v = tmp[1].strip()
                out[k] = v

            x, unit_x = map(lambda x: x.strip(), out['Stage Centre X'].split(' '))
            y, unit_y = map(lambda x: x.strip(), out['Stage Centre Y'].split(' '))
            x = self.to_um(float(x), unit_x)
            y = self.to_um(float(y), unit_y)

            ps, ps_unit = map(lambda x: x.strip(), out['Image Pixel Size'].split(' '))
            ps = self.to_um(float(ps), ps_unit)

            pixelsize = { 'x': ps, 'y': ps }
            w = img.tag[256][0]
            h = img.tag[257][0]

            return {
                'x': x, 
                'y': y,
                'pixelsize': pixelsize,
                'w': w,  # pixel
                'h': h, # pixel
                'unit': 'um'
            }

        return None
