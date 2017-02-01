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
    
    path = args.path
    height = args.height
    width = args.width
    url =  "%s/%s/%s#graph" % ( args.host, args.template, args.graph )
    
    try:
        
        
        driver.set_window_size(height, width)
        print "resize", driver.get_window_size()
        
        print "requesting", timeit.default_timer()

        driver.get(url)
        print(driver.title)
        

        print "waiting", timeit.default_timer()
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='vz_threejs_main']/canvas"))
        )
        
        #element = WebDriverWait(driver, 10).until(
            #lambda x : driver.find_element_by_css_selector( "canvas.pdg-renderer")
        #)

        #canvas = driver.find_element_by_css_selector( "canvas.pdg-renderer")
        #actions = ActionChains(driver)
        #actions.move_to_element_with_offset(canvas, 1, 1)
        ##actions.click(canvas)
        #actions.move_by_offset(-400, -400)
        #actions.double_click()
        #actions.perform()
        time.sleep(5)
        
        print "writing" , timeit.default_timer()
        driver.save_screenshot('screenshot.jpg')

        # foxus on graph rendering
        content = driver.find_element_by_id('vz_threejs_main')
        size = content.size
        location = { k:int(v) for k,v in  content.location.iteritems() }

        right  = size['width']
        bottom = size['height'] 
        left = (width - size['width']) / 2
        top  = (height - size['height'] ) / 2

        left, top, right, bottom = [ int(v) for v in  (left, top, right, bottom) ]

        if args.template == "presentation":
            left = left - 10
            top = top - 10
            right = right + 10
            bottom = bottom + 42
            
        print "croping" , timeit.default_timer()
        print(  'size', size , 'location', location , 'position ltrb', (left, top, right, bottom))

        im = Image.open('screenshot.jpg')
        im = im.crop( (left, top, right, bottom))
        im.save(path, "png")
        
    except:
        raise 



usage= """
    screenshot tool for the presentation template:
    saves image in png format.
    usage :
    python screenshot.py 'http://localhost:5000/presentation/strains' crop.png
"""
    
def main():

    parser = argparse.ArgumentParser()
    
    parser.add_argument("graph", action='store', help="graphname", default=None)
    parser.add_argument("-o" , action='store', help="output image", dest='path', default='crop.png')

    parser.add_argument("--width" , action='store', help="width", type=int, default=400)
    parser.add_argument("--height" , action='store', help="height", type=int, default=400)

    parser.add_argument("-d" , action='store', help="webdriver",  choices=('chromedriver', 'geckodriver', 'ghostdriver'), default='chromedriver')
    
    parser.add_argument("--host" , action='store', help="host", default="http://padagraph.io")
    parser.add_argument("-t" , action='store', dest="template",  choices=('presentation', 'iframe'), default='presentation')
    parser.add_argument("--background" , action='store', help="background", default='#12AAAA')

    args = parser.parse_args()

    
    
    #driver = webdriver.PhantomJS("./phantomjs-2.1.1-linux-x86_64/bin/phantomjs")
    #driver = webdriver.Firefox()
    driver = webdriver.Chrome("chromedriver")
    getScreenShot(driver, args)

    driver.quit()


if __name__ == '__main__':
    sys.exit(main())