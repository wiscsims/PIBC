import os.path
import re


class Zeiss_Microscope:

    def __init__(self):
        print('init Zeiss Microscope')

    def parse_meta_data(self, image_path, meta_dir):
        file_name = os.path.basename(image_path)
        meta_file = os.path.join(meta_dir, f'{file_name}_metadata.xml')

        if not os.path.exists(meta_file):
            return None

        with open(meta_file, 'rb') as f:
            # make regex
            flags = re.I | re.M | re.S
            metadata = f.read().decode('utf-8').replace('\ufeff', '')
            p = re.compile(
                'ImagePixelSize&gt;(?P<ps_x>[^,]+),(?P<ps_y>[^&]+)&.*?'
                'StageXPosition>(?P<x>[^<]+).*?StageYPosition>(?P<y>[^<]+)<.*?'
                'SizeX="(?P<w>\d+)".*?SizeY="(?P<h>\d+)"',
                flags
            )
            m = p.search(metadata)

            x = float(m.group('x'))
            y = float(m.group('y')) * -1
            ps_x = float(m.group('ps_x')) * 1e6  # m to um
            ps_y = float(m.group('ps_y')) * 1e6  # m to um
            w = int(m.group('w'))
            h = int(m.group('h'))

            out = {
                'x': x - (ps_x * w) / 2,
                'y': y + (ps_y * h) / 2,
                'pixelsize': {
                    'x': ps_x,
                    'y': ps_y
                },
                'w': w,
                'h': y,
                'unit': 'um'
            }
            return out
