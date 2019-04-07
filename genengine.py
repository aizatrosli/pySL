import os,sys,time
import pickle,random
from OmegaExpansion import oledExp
from OmegaExpansion import onionI2C

class oled(object):

    def __init__(self,path):
        self.OLED_EXP_ADDR = 0x3C
        self.OLED_EXP_REG_DATA = 0x40
        self.OLED_I2C_MAX_BUFFER = 32

        self.OLED_PAGE_SIZE = 8
        self.OLED_PAGES = 8
        self.OLED_WIDTH = 128
        self.OLED_HEIGHT = self.OLED_PAGE_SIZE * self.OLED_PAGES

        self.i2c = onionI2C.OnionI2C()
        oledExp.driverInit()
        oledExp.setImageColumns()
        oledExp.setMemoryMode(0)
        oledExp.clear()
        print("> Unpack Assets...")
        self.prepackasset = self.unpackasset(path)
        print("> Precache Assets...")
        self.assets = self.cachepackasset(self.prepackasset)
        self.assets90 = self.cachepackasset(self.prepackasset, 90)
        self.assets180 = self.cachepackasset(self.prepackasset, 180)
        self.assets270 = self.cachepackasset(self.prepackasset, 270)
        print("> Done.")

    def unpackasset(self,assetpath):
        assetdict = None
        with open(os.path.join(assetpath, 'assets.dat'), 'rb') as handle:
            assetdict = pickle.load(handle)
        return assetdict

    def rotateasset(self,assetarr,rotate=0):
        width = len(assetarr[0])
        height = len(assetarr)
        rotated = [[0 for i in range(height)] for j in range(width)]
        for x in range(width):
            for y in range(height):
                if rotate == 270:
                    rotated[x][y] = assetarr[y][x]
                elif rotate == 180:
                    rotated[y][x] = assetarr[height - 1 - y][x]
                elif rotate == 90:
                    rotated[x][y] = assetarr[height - 1 - y][x]
                elif rotate == 0:
                    rotated[x][y] = assetarr[x][y]
        return rotated

    def cachepackasset(self,assetdict,rotate=0):
        cachedict = {}
        for assetkey in assetdict.keys():
            cacheassetdict = {}
            for asset, assetarr in assetdict[assetkey].items():
                if rotate:
                    assetarr = self.rotateasset(assetarr,rotate)
                cacheassetdict[asset] = self.cacheasset(assetarr)
            cachedict[assetkey] = cacheassetdict
        return cachedict

    def cacheasset(self,assetarr):
        assetheight = len(assetarr)
        assetwidth = len(assetarr[0])
        assetrows = int((assetheight - 1) / self.OLED_PAGE_SIZE) + 1
        cache = [[0 for i in range(assetwidth)] for j in range(assetrows)]
        for x in range(assetwidth):
            for y in range(assetheight):
                byte = (assetarr[y][x] << int(y % self.OLED_PAGE_SIZE))
                cache[int((y / self.OLED_PAGE_SIZE) % assetrows)][x] |= byte
        return cache

    def drawasset(self,x,y,cachearr):
            cacheheight = len(cachearr)
            cachewidth = len(cachearr[0])
            cachepage = 0
            bufferPage = int((y / self.OLED_PAGE_SIZE) % self.OLED_PAGES)
            while cachepage < cacheheight:
                oledExp.setCursorByPixel(bufferPage + cachepage, x)
                count = 0
                while count < cachewidth:
                    lineWidth = cachewidth if cachewidth < self.OLED_I2C_MAX_BUFFER else (
                        self.OLED_I2C_MAX_BUFFER if cachewidth - count > self.OLED_I2C_MAX_BUFFER else cachewidth - count)
                    bytes = [cachearr[cachepage][count + i] for i in range(lineWidth)]
                    self.i2c.writeBytes(self.OLED_EXP_ADDR, self.OLED_EXP_REG_DATA, bytes)
                    count += lineWidth
                oledExp.setCursorByPixel(0, 0)
                cachepage += 1


test = oled('/root/assets')
counter = 0
try:
    while True:
        counter += 1
        test.drawasset(2, 0, test.assets90['char10']['H'])
        test.drawasset(2, 16, test.assets90['char10']['I'])
        test.drawasset(32, 10, test.assets['dice']['dice{0}'.format(random.randint(1, 6))])
        counter = 1 if counter > 10 else counter
        test.drawasset(96, 2, test.assets['snake']['snake{0}'.format(counter)])
        test.drawasset(96, 36, test.assets['snake']['snake{0}'.format(counter)])
except KeyboardInterrupt:
    print('interrupted! count:' + str(counter))