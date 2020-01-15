import freetype
from PIL import Image


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

    def kerning_offset(self, previous_char, char):
        kerning = self.face.get_kerning(previous_char, char)
        return kerning.x // 64

    def text_dimensions(self, text):
        """Return (width, height, baseline) of `text` rendered in the
        current font.
        """
        width = 0
        max_ascent = 0
        max_descent = 0
        previous_char = None

        for char in text:
            glyph = self.glyph_for_character(char)
            max_ascent = max(max_ascent, glyph.ascent)
            max_descent = max(max_descent, glyph.descent)
            kerning_x = self.kerning_offset(previous_char, char)

            width += max(glyph.advance_width + kerning_x,
                         glyph.width + kerning_x)

            previous_char = char

        height = max_ascent + max_descent
        return width, height, max_descent

    def render_text(self, text, width=None, height=None, baseline=None):
        """Render the given `text` into a Bitmap and return it.

        If `width`, `height`, and `baseline` are not specified they
        are computed using the `text_dimensions' method.
        """
        if None in (width, height, baseline):
            width, height, baseline = self.text_dimensions(text)

        x = 0
        previous_char = None
        outbuffer = Bitmap(width, height)

        for char in text:
            glyph = self.glyph_for_character(char)

            x += self.kerning_offset(previous_char, char)
            y = height - glyph.ascent - baseline

            outbuffer.bitblt(glyph.bitmap, x, y)

            x += glyph.advance_width
            previous_char = char

        return outbuffer


class Glyph:

    def __init__(self, pixels, width, height, top, advance_width):
        self.bitmap = Bitmap(width, height, pixels)

        self.top = top
        self.descent = max(0, self.height - self.top)
        self.ascent = max(0, max(self.top, self.height) - self.descent)
        self.advance_width = advance_width

    @property
    def width(self):
        return self.bitmap.width

    @property
    def height(self):
        return self.bitmap.height

    @staticmethod
    def from_glyphslot(slot):
        """Construct and return a Glyph object from a FreeType GlyphSlot."""
        pixels = Glyph.unpack_mono_bitmap(slot.bitmap)
        width, height = slot.bitmap.width, slot.bitmap.rows
        top = slot.bitmap_top
        advance_width = slot.advance.x // 64
        return Glyph(pixels, width, height, top, advance_width)

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

    def __init__(self, width, height, pixels=None):
        self.width = width
        self.height = height
        if pixels is None:
            self.pixels = [False for __ in range(width * height)]
        else:
            self.pixels = pixels

    def bitblt(self, src, x, y):
        """Copy all pixels from `src` into this bitmap, starting at
        (`x`, `y`)."""
        srcpixel = 0
        dstpixel = y * self.width + x
        row_offset = self.width - src.width

        for sy in range(src.height):
            for sx in range(src.width):
                self.pixels[dstpixel] = self.pixels[dstpixel] \
                                        or src.pixels[srcpixel]
                srcpixel += 1
                dstpixel += 1
            dstpixel += row_offset

    def show(self):
        img = Image.new('P', (self.width, self.height))
        img.putpalette(bytes.fromhex('000000ffffff'))
        img.frombytes(bytes(self.pixels))
        img.show()


def main(font, text):
    print(f'Font: {font.face.family_name.decode()}'
          f' {font.face.style_name.decode()} {font.face.size.y_ppem} px')
    print(f'Text to display: {text!r}')

    bitmap = font.render_text(text)
    print(f'Pixel dimensions of displayed text: {bitmap.width}'
          f' x {bitmap.height} px')
    bitmap.show()


if __name__ == '__main__':
    main(Font('NotoSerif-Regular.ttf', 40), 'I kinda \u2665 Python')
