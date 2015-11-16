from PIL import Image


def reset(src_image):
    """Reset an image if it has transparent background. """
    if src_image.mode == 'RGBA':
        image = Image.new('RGB', src_image.size, (255, 255, 255))
        image.paste(src_image, src_image)
        return image
    else:
        image = src_image.convert('RGB')
        return image


def resize(src_image, size):
    """Resize an image to specified size. """
    image = src_image.copy()
    image.thumbnail(size, Image.ANTIALIAS)
    return image


def thumbnail(src_image, size, crop=None):
    """Return dynamically generated thumbnail image object.

    The argument ``crop`` should be one of None, 'top', 'middle', and 'bottom'.
    If it's set to None, the image won't be cropped. For now, only vertical
    cropping is supported.
    """
    image = src_image.copy()

    if crop is None:
        image.thumbnail(size, Image.ANTIALIAS)
        width, height = image.size

        square_image = Image.new('RGBA', size, 'white')
        if width > height:
            square_image.paste(image, (0, (size[1] - height)/2))
        else:
            square_image.paste(image, ((size[0] - width)/2, 0))

        image = square_image
    else:
        src_width, src_height = image.size
        src_ratio = float(src_width) / float(src_height)
        dst_width, dst_height = size
        dst_ratio = float(dst_width) / float(dst_height)

        x_offset, y_offset = 0, 0

        if dst_ratio < src_ratio:
            # No vertical cropping is needed
            crop_height = src_height
            crop_width = crop_height * dst_ratio
            x_offset = float(src_width - crop_width) / 2
            y_offset = 0
        else:
            crop_width = src_width
            crop_height = crop_width / dst_ratio

            if crop == 'top':
                pass
            elif crop == 'middle':
                y_offset = float(src_height - crop_height) / 2
            elif crop == 'bottom':
                y_offset = float(src_height - crop_height)
            else:
                raise ImageException('Only top, middle, bottom cropping is '
                                     'supported : %s' % crop)

        image = image.crop((int(x_offset),
                            int(y_offset),
                            int(x_offset) + int(crop_width),
                            int(y_offset) + int(crop_height)))
        image = image.resize((dst_width, dst_height), Image.ANTIALIAS)

    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    return image


# -*- coding: utf-8 -*-
"""
    sphinx.util.png
    ~~~~~~~~~~~~~~~

    PNG image manipulation helpers.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import struct
import binascii


LEN_IEND = 12
LEN_DEPTH = 22

DEPTH_CHUNK_LEN = struct.pack('!i', 10)
DEPTH_CHUNK_START = b'tEXtDepth\x00'
IEND_CHUNK = b'\x00\x00\x00\x00IEND\xAE\x42\x60\x82'


def read_png_depth(filename):
    """Read the special tEXt chunk indicating the depth from a PNG file."""
    result = None
    f = open(filename, 'rb')
    try:
        f.seek(- (LEN_IEND + LEN_DEPTH), 2)
        depthchunk = f.read(LEN_DEPTH)
        if not depthchunk.startswith(DEPTH_CHUNK_LEN + DEPTH_CHUNK_START):
            # either not a PNG file or not containing the depth chunk
            return None
        result = struct.unpack('!i', depthchunk[14:18])[0]
    finally:
        f.close()
    return result


def write_png_depth(filename, depth):
    """Write the special tEXt chunk indicating the depth to a PNG file.

    The chunk is placed immediately before the special IEND chunk.
    """
    data = struct.pack('!i', depth)
    f = open(filename, 'r+b')
    try:
        # seek to the beginning of the IEND chunk
        f.seek(-LEN_IEND, 2)
        # overwrite it with the depth chunk
        f.write(DEPTH_CHUNK_LEN + DEPTH_CHUNK_START + data)
        # calculate the checksum over chunk name and data
        crc = binascii.crc32(DEPTH_CHUNK_START + data) & 0xffffffff
        f.write(struct.pack('!I', crc))
        # replace the IEND chunk
        f.write(IEND_CHUNK)
    finally:
        f.close()
