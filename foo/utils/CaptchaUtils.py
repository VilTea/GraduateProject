from random import randint
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

import foo.conf.config as config

class CaptchaGenerator():
    def __init__(self, width=140, height=60, length=4):
        self.width = width
        self.height = height
        self.length = length
        self.__code = ''
        self.pen: ImageDraw.Draw = None

    def __new__(cls, *args, **kwargs):
        """
        单例模式
        """
        if not hasattr(cls, "_instance"):
            cls.__instance = super(CaptchaGenerator, cls).__new__(cls)
        return cls.__instance

    @property
    def code(self):
        return self.__code

    def generate(self):
        img = Image.new('RGB', (self.width, self.height), (250, 250, 250))
        self.pen = ImageDraw.Draw(img)
        self.__rand_code()
        self.__draw_code()
        self.__draw_point()
        self.__draw_rand_line()
        buf = BytesIO()
        img.save(buf, 'png')
        res = buf.getvalue()
        return res

    def __rand_color(self, min=120, max=200):
        return randint(min, max), randint(min, max), randint(min, max)

    def __rand_code(self):
        self.__code = ''
        for i in range(self.length):
            self.__code += self.__rand_chr()

    def __rand_chr(self):
        codes = [[chr(i) for i in range(48, 58)],
                 [chr(i) for i in range(65, 91)],
                 [chr(i) for i in range(97, 123)]]
        codes = codes[randint(0, 2)]
        return codes[randint(0, len(codes) - 1)]

    def __draw_code(self):
        font = ImageFont.truetype(config.ROOT_PATH + "\\static\\materialize\\fonts\\consolab.ttf", size=36)
        for i in range(len(self.__code)):
            rand_len = randint(-5, 5)
            self.pen.text((self.width * 0.2 * (i + 1) + rand_len, self.height * 0.2 + rand_len),
                          self.__code[i],
                          font=font,
                          fill=self.__rand_color())

    def __draw_rand_line(self):
        for i in range(3):
            x1 = randint(0, self.width)
            y1 = randint(0, self.height)
            x2 = randint(0, self.width)
            y2 = randint(0, self.height)
            self.pen.line((x1, y1, x2, y2), fill=self.__rand_color())

    def __draw_point(self):
        for i in range(16):
            self.pen.point((randint(0, self.width), randint(0, self.height)), fill=self.__rand_color())


cg = CaptchaGenerator()