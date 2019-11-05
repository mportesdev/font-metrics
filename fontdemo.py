import freetype


class Font:

    def __init__(self, filename, size):
        self.face = freetype.Face(filename)
        self.face.set_pixel_sizes(0, size)

    def glyph_for_character(self, char):
        """Let FreeType load the glyph for the given character and
        tell it to render a monochromatic bitmap representation.
        """
        self.face.load_char(char, freetype.FT_LOAD_RENDER |
                            freetype.FT_LOAD_TARGET_MONO)

        return Glyph.from_glyphslot(self.face.glyph)

    def render_character(self, char):
        glyph = self.glyph_for_character(char)
        return glyph.bitmap


class Glyph:

    def __init__(self, pixels, width, height):
        self.bitmap = Bitmap(width, height, pixels)

    @staticmethod
    def from_glyphslot(slot):
        """Construct and return a Glyph object from a FreeType GlyphSlot."""
        pixels = Glyph.unpack_mono_bitmap(slot.bitmap)
        width, height = slot.bitmap.width, slot.bitmap.rows
        return Glyph(pixels, width, height)

    @staticmethod
    def unpack_mono_bitmap(bitmap):
        """Unpack a freetype FT_LOAD_TARGET_MONO glyph bitmap into
        a list where each pixel is represented by True or False.
        """
        assert len(bitmap.buffer) == bitmap.rows * bitmap.pitch
        data = []

        for row in zip(*[iter(bitmap.buffer)] * bitmap.pitch):
            row_int = int.from_bytes(row, 'big')
            bin_str = f'{row_int:0{bitmap.pitch*8}b}'[:bitmap.width]
            assert len(bin_str) == bitmap.width
            data.extend(bit == '1' for bit in bin_str)

        assert len(data) == bitmap.rows * bitmap.width
        return data


class Bitmap:
    """A 2D bitmap image represented as a list of boolean values. Each
    boolean value indicates the state of a single pixel in the bitmap.
    """

    def __init__(self, width, height, pixels):
        self.width = width
        self.height = height
        self.pixels = pixels

    def __repr__(self):
        """Return a string representation of the bitmap's pixels."""
        return '\n'.join(''.join('██' if self.pixels[y*self.width + x] else '  '
                                 for x in range(self.width))
                         for y in range(self.height))


if __name__ == '__main__':
    fnt = Font('OpenSans-Regular.ttf', 40)
    print(fnt.render_character('P'))
