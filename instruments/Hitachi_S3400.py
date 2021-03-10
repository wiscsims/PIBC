import os.path
import re


class Hitachi_S3400:

    def __init__(self):
        print('init S3400')
        pass

    def parse_meta_data(self, image_path, meta_dir):
        """parse meta data of image file"""
        tmp = image_path.split(os.extsep)
        img_name = os.path.basename(tmp[0])
        file_name = os.path.splitext(image_path)[0]
        img_dir = os.path.dirname(image_path)
        meta_file = os.path.join(meta_dir, '{}.txt'.format(file_name))

        # print(meta_file, 'mete_file_exists?', os.path.exists(meta_file))

        if not os.path.exists(meta_file):
            return None

        with open(meta_file, 'r') as f:
            m = re.compile(
                r'ImageName=(?P<name>.*\.[a-zA-Z0-9]+).*'
                r'DataSize=(?P<width>\d+)x(?P<height>\d+).*'
                r'PixelSize=(?P<pxsize>[\d\.]+).*'
                r'StagePositionX=(?P<x>\d+).*'
                r'StagePositionY=(?P<y>\d+).*', re.M | re.S)
            p = m.search(f.read())
            if not p:
                return None

            # units are micron
            x = float(p.group('x')) / -1000.0
            y = float(p.group('y')) / 1000.0
            px_x = float(p.group('pxsize')) / 1000.0
            px_y = float(p.group('pxsize')) / 1000.0
            w = float(p.group('width'))  # pixel
            h = float(p.group('height'))  # pixel
            out = {
                'x': x - (w * px_x) / 2,
                'y': y + (h * px_y) / 2,
                'pixelsize': {
                    'x': px_x,
                    'y': px_y,
                },
                'w': w,  # pixel
                'h': h,  # pixel
                'unit': 'um'
            }

            # print(out)

            return out
