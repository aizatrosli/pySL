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
        print("Unpack Assets...")
        self.prepackasset = self.unpackasset(path)
        print("Precache Assets...")
        self.assets =self.cachepackasset(self.prepackasset)
        print("Done.")

    def unpackasset(self,assetpath):
        assetdict = None
        with open(os.path.join(assetpath, 'assets.dat'), 'rb') as handle:
            assetdict = pickle.load(handle)
        return assetdict

    def cachepackasset(self,assetdict):
        cachedict = {}
        for assetkey in assetdict.keys():
            cacheassetdict = {}
            for asset, assetarr in assetdict[assetkey].items():
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
        test.drawasset(20,10,test.assets['dice']['dice{0}'.format(random.randint(1, 6))])
        test.drawasset(70, 10, test.assets['dice']['dice{0}'.format(random.randint(1, 6))])
except KeyboardInterrupt:
    print('interrupted! count:' + str(counter))