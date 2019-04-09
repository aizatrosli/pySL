import os,sys,time,math
import pickle,random
import threading
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
        self.textsplit = {}
        self.textsplititter = {}
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

    def drawtext(self, x, y, text, font='char10', rotate=0, size=None):

        font = self.prepackasset[font]
        charheight = len(font[list(font)[0]])
        charwidth = len(font[list(font)[0]][0])
        chararr = []
        if not self.textsplit or not text in self.textsplit.keys():
            chararr = [[] for i in range(charheight)]
            for char in text:
                for j,row in enumerate(font[char]):
                    chararr[j] = chararr[j]+row
            if rotate:
                chararr = self.rotateasset(chararr, rotate)
            self.textsplititter[text] = 0
            chararrheight = len(chararr)
            chararrwidth = len(chararr[0])
            deltaheight = int(self.OLED_HEIGHT-y)
            deltawidth = int(self.OLED_WIDTH-x)
            temptextsplit = []
            if chararrheight > deltaheight:
                for i in range(int(math.ceil(chararrheight/deltaheight))):
                    splitarr = chararr[:deltaheight]
                    if len(splitarr) != deltaheight:
                        splitarr = splitarr + [[0 for i in range(chararrwidth)] for j in range(deltaheight-len(splitarr))]
                    temptextsplit.append(splitarr)
                    chararr = chararr[deltaheight:]
            elif chararrwidth > deltawidth:
                for i in range(int(math.ceil(chararrwidth/deltawidth))):
                    splitarr = [[] for i in range(chararrheight)]
                    for j, row in enumerate(chararr):
                        splitarr[j] = row[:deltawidth]
                        chararr[j] = row[deltawidth:]
                    temptextsplit.append(splitarr)
            else:
                chararr = self.cacheasset(chararr)
                temptextsplit = None
            self.textsplit[text] = temptextsplit

        if len(self.textsplit[text]) > 0:
            chararr = self.cacheasset(self.textsplit[text][self.textsplititter[text]])
            self.textsplititter[text] = self.textsplititter[text] + 1 if self.textsplititter[text] < len(self.textsplit[text])-1 else 0
        self.drawasset(x, y, chararr)

    def drawtextscroll(self, x, y, text, font='char10', rotate=0, size=None, gap=1):

        font = self.prepackasset[font]
        charheight = len(font[list(font)[0]])
        charwidth = len(font[list(font)[0]][0])
        chararr = []
        if not self.textsplit or not text in self.textsplit.keys():
            chararr = [[] for i in range(charheight)]
            for char in text:
                for j,row in enumerate(font[char]):
                    chararr[j] = chararr[j]+row
            if rotate:
                chararr = self.rotateasset(chararr, rotate)
            self.textsplititter[text] = 0
            chararrheight = len(chararr)
            chararrwidth = len(chararr[0])
            deltaheight = int(self.OLED_HEIGHT-y)
            deltawidth = int(self.OLED_WIDTH-x)
            temptextsplit = []
            if chararrheight > deltaheight:
                for i in range(int(math.ceil(chararrheight/gap))):
                    splitarr = chararr[:deltaheight]
                    if len(splitarr) != deltaheight:
                        splitarr = splitarr + [[0 for i in range(chararrwidth)] for j in range(deltaheight-len(splitarr))]
                    temptextsplit.append(splitarr)
                    chararr = chararr[gap:]
            elif chararrwidth > deltawidth:
                for i in range(int(math.ceil(chararrwidth/gap))):
                    splitarr = [[] for i in range(chararrheight)]
                    for j, row in enumerate(chararr):
                        splitarr[j] = row[:deltawidth]
                        chararr[j] = row[gap:]
                    temptextsplit.append(splitarr)
            else:
                chararr = self.cacheasset(chararr)
                self.textsplit = None
            self.textsplit[text] = temptextsplit

        if len(self.textsplit[text]) > 0:
            chararr = self.cacheasset(self.textsplit[text][self.textsplititter[text]])
            self.textsplititter[text] = self.textsplititter[text] + 1 if self.textsplititter[text] < len(self.textsplit[text])-1 else 0
        self.drawasset(x, y, chararr)


def drawthreadscroll(classoled,text,x,y,rotate,gap):
    while True:
        classoled.drawtextscroll(x, y, text, rotate=rotate,gap=gap)

def drawthreadassets(classoled,asset,x,y):
    while True:
        classoled.drawasset(x,y,asset)

def drawthreadsnake(classoled,x,y):
    while True:
        for counter in range(10):
            classoled.drawasset(x, y, classoled.assets['snake']['snake{0}'.format(counter)])


if __name__ == "__main__":

    try:
        test = oled('/root/assets')
        task1 = threading.Thread(target=drawthreadscroll, kwargs={'classoled': test,'text':"PRESS_START_TO_BEGIN",'x':2,'y':2,'rotate':90,'gap':1})
        task2 = threading.Thread(target=drawthreadscroll, kwargs={'classoled': test,'text':"PLAYER_3",'x':96,'y':36,'rotate':0,'gap':1})
        task3 = threading.Thread(target=drawthreadassets, kwargs={'classoled': test,'asset': test.assets['dice']['dice{0}'.format(random.randint(1, 6))],'x':32,'y':10})
        #task4 = threading.Thread(target=drawthreadassets, kwargs={'classoled': test,'x':96,'y':2})
        counter = 0

        task1.start()
        task2.start()
        task3.start()
        #task4.start()
    except KeyboardInterrupt:
        print('interrupted!')

