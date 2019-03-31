
import time,sys,os
import pickle

def manageasset(workpath):
    assetdict = {}
    for files in os.listdir(workpath):
        file = os.path.join(workpath, files)
        if os.path.isdir(file):
            assetdict[files] = getasset(file)
    return assetdict

def getasset(assetpath):
    assetdict = {}
    for item in os.listdir(assetpath):
        if ".png" in item:
            assetdict[item.split(".")[0]] = getimage(os.path.join(assetpath,item))
    return assetdict

def getimage(path,threshold=50):
    import cv2
    img = cv2.imread(path, 0)
    img[img<threshold]=1
    img[img>threshold]=0
    return img.tolist()

def packasset(packagepath,dictasset):
    with open(os.path.join(packagepath,'assets.dat'), 'wb') as handle:
        pickle.dump(dictasset, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print("Successfully pack assets!!!")

def unpackasset(packagepath):
    assetdict = None
    with open(os.path.join(packagepath,'assets.dat'), 'rb') as handle:
        assetdict = pickle.load(handle)
    return assetdict

mypath = r"C:\Users\aizat\PycharmProjects\pySnakesLadder\assets"
dicttest = manageasset(mypath)
packasset(mypath,dicttest)
dicttestun = unpackasset(mypath)
print(dicttestun)
print(dicttest == dicttestun)
#testdict=(getasset(r"C:\Users\aizat\PycharmProjects\pySnakesLadder\assets\dice"))
#print(testdict['dice1'])
