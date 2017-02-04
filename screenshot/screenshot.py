import sys
import argparse
import time
import timeit

from PIL import Image

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait



def getScreenShot(driver, args):
    # http://stackoverflow.com/a/15870708
    
    params = {
        #template
        'color' : args.color,
        'zoom' : args.zoom,
        'buttons': 0, # removes play/vote buttons
        'labels': 0 if args.no_labels else 1,  # removes graph name/attributes 
        # gviz
        'vtx_size' : args.vertex_size,
        'show_text': 0 if args.no_text else 1,  # removes vertex text 
        'show_nodes': 0 if args.no_nodes else 1,  # removes vertex only 
        'show_edges': 0 if args.no_edges else 1,  # removes edges 
        'show_images': 0 if args.no_images else 1,  # removes vertex images 
    }

    querystr = "&".join(["%s=%s" % (k,v) for k,v in params.iteritems()])
    url =  "%s/%s/%s?%s#graph" % ( args.host, args.template, args.graph, querystr )
    
    try:
        driver.set_window_size(args.width, args.height)
        print "resize", driver.get_window_size()
        
        print "requesting", url, timeit.default_timer()

        driver.get(url)
        print(driver.title)
        
        print "waiting", timeit.default_timer(), args.wait, " sec"
        time.sleep( args.wait)
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='vz_threejs_main']/canvas"))
        )
        
        element = WebDriverWait(driver, 10).until(
            lambda x : driver.find_element_by_css_selector( "canvas.pdg-renderer")
        )

        print "writing" , timeit.default_timer()
        driver.save_screenshot(args.path)
        #crop(driver, args.path, args.height, args.width)

    except:
        raise

def crop(driver, path, height, width):
        # focus on graph rendering html element
        content = driver.find_element_by_id('vz_threejs_main')
        size = content.size
        location = { k:int(v) for k,v in  content.location.iteritems() }

        print "croping" , timeit.default_timer()
        left, top, right, bottom = 0,0, min(width, size['width']), min(height, size['height'])
        left, top, right, bottom = [ int(v) for v in  (left, top, right, bottom) ]
        print(  'size', size , 'location', location , 'position ltrb', (left, top, right, bottom))

        im = Image.open(path)
        im = im.crop( (left, top, right, bottom))
        im.save(path, "png")
        



usage= """
    screenshot tool for the iframe template:
    saves image in png format.
    $ python screenshot.py --help
"""
    
def main():

    parser = argparse.ArgumentParser()
    
    parser.add_argument("graph", action='store', help="graphname", default=None)
    parser.add_argument("path" , action='store', help="output image", default='crop.png')

    parser.add_argument("--width" , action='store', help="width", type=int, default=400)
    parser.add_argument("--height" , action='store', help="height", type=int, default=400)
    parser.add_argument("--color" , action='store', default="12AAAA")
    parser.add_argument("--vertex-size" , action='store', type=int, default=0, help="(-5, 5) default 0") 
    parser.add_argument("--zoom" , action='store', type=int, default=1200)
    parser.add_argument("--no-labels" , action='store_true', default=False)
    parser.add_argument("--no-text" , action='store_true', default=False)
    parser.add_argument("--no-nodes" , action='store_true', default=False)
    parser.add_argument("--no-edges" , action='store_true', default=False)
    parser.add_argument("--no-images" , action='store_true', default=False)

    parser.add_argument("-d" , action='store', dest="driver", help="webdriver",  choices=('chromedriver', 'geckodriver', 'phantomjs'), default='chromedriver')
    
    parser.add_argument("--wait" , action='store', help="seconds to wait for layouts and vertex images to load", default=3., type=float)
    parser.add_argument("--host" , action='store', help="host", default="http://padagraph.io")
    parser.add_argument("-t" , action='store', help="template", dest="template",  choices=('presentation', 'iframe'), default='iframe')
    
    # todo
    parser.add_argument("--background" , action='store', help="background", default='#12AAAA')

    args = parser.parse_args()

    if args.driver == "phantomjs":
        driver = webdriver.PhantomJS("./phantomjs")
    elif args.driver == "geckodriver":
        driver = webdriver.Firefox()
    elif args.driver == "chromedriver":
        driver = webdriver.Chrome("chromedriver")

    #driver = webdriver.Chrome("chromedriver")
    
    getScreenShot(driver, args)

    driver.quit()


if __name__ == '__main__':
    sys.exit(main())