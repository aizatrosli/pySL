import os,sys,time
import pickle,random
from OmegaExpansion import oledExp
from OmegaExpansion import onionI2C

OLED_EXP_ADDR = 0x3C
OLED_EXP_REG_DATA = 0x40
OLED_I2C_MAX_BUFFER = 32

OLED_PAGE_SIZE = 8
OLED_PAGES = 8
OLED_WIDTH = 128
OLED_HEIGHT = OLED_PAGE_SIZE * OLED_PAGES

i2c = onionI2C.OnionI2C()

oledExp.driverInit()
oledExp.setImageColumns()
oledExp.setMemoryMode(0)


def clearBuffers():
    """
        Clears the framebuffers (all elements to 0).
    """
    global pagebuffer
    pagebuffer = [[0 for i in range(OLED_WIDTH)] for j in range(OLED_PAGES)]

def reversetranslate(bitmap):
    bitmapHeight = len(bitmap)
    bitmapWidth = len(bitmap[0])
    bitmapRows = int((bitmapHeight -1)/ OLED_PAGE_SIZE) + 1
    #print("H:{0}, W:{1}, Rows:{2}".format(bitmapHeight,bitmapWidth,bitmapRows))
    translation = [[0 for i in range(bitmapWidth)] for j in range(bitmapRows)]
    #print("translation: {0}".format(translation))
    for x in range(bitmapWidth):
        for y in range(bitmapHeight):
            byte = (bitmap[y][x] << int(y%OLED_PAGE_SIZE))
            #print("{0} = {1} << {2} if x:{3} y:{4}".format(byte,bitmap[y][x],(y%OLED_PAGE_SIZE),x,y))
            translation[int((y / OLED_PAGE_SIZE) % bitmapRows)][x] |= byte
    return translation

def reverseblit(x, y, translatedBitmap):
    bitmapHeight = len(translatedBitmap)
    bitmapWidth = len(translatedBitmap[0])
    bitmapPage = 0
    bufferPage = int((y / OLED_PAGE_SIZE) % OLED_PAGES)
    # print("Bitmap height: " + str(bitmapHeight))
    while bitmapPage < bitmapHeight:
        # print("Bitmap page: " + str(bitmapPage))
        oledExp.setCursorByPixel(bufferPage+bitmapPage, x)
        count = 0
        while count < bitmapWidth:
            lineWidth = bitmapWidth if bitmapWidth < OLED_I2C_MAX_BUFFER else (
                OLED_I2C_MAX_BUFFER if bitmapWidth - count > OLED_I2C_MAX_BUFFER else bitmapWidth - count)
            bytes = [translatedBitmap[bitmapPage][count + i] for i in range(lineWidth)]
            #print("bitmappage: {0}, count:{1}, bytes: {2}".format(bitmapPage,count,bytes))
            i2c.writeBytes(OLED_EXP_ADDR, OLED_EXP_REG_DATA, bytes)
            count += lineWidth
        oledExp.setCursorByPixel(0, 0)
        bitmapPage += 1

print("Initialize Driver")
oledExp.clear()
time.sleep(1)
print("Unpack Assets")
assetdict = None
with open('assets.dat', 'rb') as handle:
    assetdict = pickle.load(handle)
counter = 0
try:
    while True:
        counter += 1
        bitmap = reversetranslate(assetdict['dice']['dice{0}'.format(random.randint(1,6))])
        reverseblit(10,10,bitmap)
except KeyboardInterrupt:
    print('interrupted! count:'+str(counter))