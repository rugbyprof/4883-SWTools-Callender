import cv2
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from PIL import Image
import sys,os
import pprint
import requests
from math import sqrt
import glob
import json

def brightness(r,g,b):
    """A function to return the calculated "brightness" of a color.
    http://www.nbdtech.com/Blog/archive/2008/04/27/Calculating-the-Perceived-Brightness-of-a-Color.aspx
    Arguments:
        r: [int]
        g: [int]
        b: [int]
    Returns:
        Values between 0-1 (percent of 0-255)
    Used By:
        get_dominant_colors
    """
    return sqrt(pow(r,2) * .241  + pow(g,2) * .691 + pow(b,2) * .068 ) / 255

def find_histogram(clt):
    """ Create a histogram with k clusters
    Arguments:
        :param: clt
        :return:hist
    Used By:
        get_dominant_colors
    """
    numLabels = np.arange(0, len(np.unique(clt.labels_)) + 1)
    (hist, _) = np.histogram(clt.labels_, bins=numLabels)

    hist = hist.astype("float")
    hist /= hist.sum()

    return hist


def get_color_data(r,g,b,d=3):
    """Get color name and hsv from color api.
    Arguments:
        r -- red   [int]
        g -- green [int]
        b -- blue  [int]
    Returns:
        json
    """
    payload = {'r':r, 'g':g, 'b':b,'d':d}
    r = requests.get('http://cs.mwsu.edu/~griffin/color-api/', params=payload)
    return r.json()


def extract_cluster_color_values(hist, centroids,ignore_background=False):
    """Get the dominant colors of an image.
    Arguments:
        hist        -- [numpy.ndarray]
        centroids   -- [numpy.ndarray] 
    Returns:
        dictionary of color values
    Used By:
        get_dominant_colors
    """

    colors = []
    
    for (percent, color) in zip(hist, centroids):
        rgb = []
        total = 0
        for c in color:
            c = round(float(c))
            total += c
            rgb.append(c)
        if ignore_background:
            if total > 15 and total < 750:
                colors.append({'percent':round(float(percent),2),'rgb':rgb})
        else:
            colors.append({'percent':round(float(percent),2),'rgb':rgb})

    return colors

def plot_colors(hist, centroids):
    """Get the dominant colors of an image.
    Arguments:
        hist        -- [numpy.ndarray]
        centroids   -- [numpy.ndarray] 
    Returns:
        plot image
    """
    bar = np.zeros((50, 300, 3), dtype="uint8")
    startX = 0

    for (percent, color) in zip(hist, centroids):
        # plot the relative percentage of each cluster
        endX = startX + (percent * 300)
        cv2.rectangle(bar, (int(startX), 0), (int(endX), 50),
                      color.astype("uint8").tolist(), -1)
        startX = endX

    # return the bar chart
    return bar


def get_dominant_colors(img,save_path=None,n=3):
    """Get the dominant colors of an image.
    Arguments:
        img         -- the image [string, numpy.ndarray]
        save_path   -- out path for saving [string] (default None)
        n           -- number of clusters [int] (default 3)
    Returns:
        dictionary of colors
        load_subimages_data
    Requres:
        extract_cluster_color_values
        query_color
        brightness
    """

    #bg,_ = determine_background(img_path)

    # if its string open it
    if isinstance(img,str):
        if os.path.isfile(img):
            img = cv2.imread(img)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        else:
            usage("Error: image path not valid")

    img = img.reshape((img.shape[0] * img.shape[1],3)) #represent as row*column,channel number

    clt = KMeans(n_clusters=n) #cluster number
    clt.fit(img)

    hist = find_histogram(clt)
    colors = extract_cluster_color_values(hist, clt.cluster_centers_,True)

    if save_path != None:
        bar = plot_colors(hist, clt.cluster_centers_)
        cv2.imwrite(save_path,bar)
        # plt.axis("off")
        #plt.imshow(bar)
        #plt.show()

    start_delta = 3

    # loop through each cluster
    for i in range(len(colors)):
        c = []
        d = start_delta
        # while we haven't found a named color match (increment delta)
        while len(c) < 1:
            #c = query_color(colors[i]['rgb'][0],colors[i]['rgb'][1],colors[i]['rgb'][2],d)
            c = get_color_data(colors[i]['rgb'][0],colors[i]['rgb'][1],colors[i]['rgb'][2],d)
            d += 3
        colors[i]['named_data'] = c
        colors[i]['brightness'] = brightness(colors[i]['rgb'][0],colors[i]['rgb'][1],colors[i]['rgb'][2])

    return colors



if __name__=='__main__':
    # path to image to process
    files = glob.glob('./emojis/**/*.png', recursive=True)
    allColors = {}
    for file in files:
        img = file
        #print(img)
    
        # gets a json of dominant colors
        # if you supply a path (like './lilly_colors_bar.jpg') it will save the color bar there.
        # it also lets you specify number of clusters if you want
        #colors1 = get_dominant_colors(img,'./emojis/-1.png')

        # 4 clusters and save image
        #colors2 = get_dominant_colors(img,'./emojis/-1.png',4)
        
        # What you should probably use
        colors = get_dominant_colors(img)
        allColors[img] = {}
        #print(colors)
        x=0
        for info in colors:
            #print(x, ": ")
            allColors[img][x] = {}
            

            for k,v in info.items(): 
                
                allColors[img][x]["Percent"] = info["percent"]
                allColors[img][x]["RGB"] = info["rgb"]
                allColors[img][x]["Brightness"] = info["brightness"]
                allColors[img][x]["Colors"] = {}
                
                for result in info["named_data"]["result"]:
                    #print("Keys: ",named, " Value: ",nameinfo )
                    for named,nameinfo in result.items():
                        #print("Keys: ",named, " Value: ",nameinfo )
                        #print(result["name"])
                        if result["name"] not in allColors[img][x]["Colors"].keys():
                            allColors[img][x]["Colors"][result["name"]] = {}
                        allColors[img][x]["Colors"][result["name"]]["R"] = result["r"]
                        allColors[img][x]["Colors"][result["name"]]["G"] = result["g"]
                        allColors[img][x]["Colors"][result["name"]]["B"] = result["b"]
                        allColors[img][x]["Colors"][result["name"]]["Distance"] = result["dist"]
                    #print(result)

            x=x+1
    f = open("Images.json","w")
    f.write(json.dumps(allColors))
    f.close()
    #print(allColors)

    #2246537024