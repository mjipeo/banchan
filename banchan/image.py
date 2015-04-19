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
