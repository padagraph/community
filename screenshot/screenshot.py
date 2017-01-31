import sys
from PIL import Image

from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


#browser = webdriver.Firefox()
#browser.get('http://seleniumhq.org/')
#browser.quit()

def getScreenShot(driver, url):
    # http://stackoverflow.com/a/15870708
    import time
    import timeit

    try:
        print "requesting", timeit.default_timer()
        driver.get(url)
        print(driver.title)
        
        
        print "resize", timeit.default_timer()
        print driver.get_window_size()
        
        driver.set_window_size(800,1200)
        print driver.get_window_size()

        print "waiting", timeit.default_timer()
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@id='vz_threejs_main']/canvas"))
        )
        
        element = WebDriverWait(driver, 10).until(
            lambda x : driver.find_element_by_css_selector( "canvas.pdg-renderer")
        )

        #canvas = driver.find_element_by_css_selector( "canvas.pdg-renderer")
        #actions = ActionChains(driver)
        #actions.move_to_element_with_offset(canvas, 1, 1)
        ##actions.click(canvas)
        #actions.move_by_offset(-400, -400)
        #actions.double_click()
        #actions.perform()
        time.sleep(2)
        
        print "writing" , timeit.default_timer()
        driver.save_screenshot('screenshot.jpg')

        # foxus on graph rendering
        content = driver.find_element_by_id('vz_threejs_main')
        footer = driver.find_element_by_id('footer')

        location = { k:int(v) for k,v in  content.location.iteritems() }
        end = { k:int(v) for k,v in  footer.location.iteritems() }
        size = content.size

        left = location['x'] - 10
        top = location['y'] - 10
        right = location['x'] + size['width'] + 10
        bottom = location['y'] + size['height'] + 42

        #left = 40
        #top = 40
        #right = 400
        #bottom = 400
        

        left, top, right, bottom = [ int(v) for v in  (left, top, right, bottom) ]
        

        print "croping" , timeit.default_timer()
        print( 'end', end , 'size', size , 'location', location , 'position ltrb', (left, top, right, bottom))

        im = Image.open('screenshot.jpg')
        im = im.crop( (left, top, right, bottom))

        print "writing" , timeit.default_timer()
        im.save('crop.png', "png")
        
    except:
        raise 



usage= """
    screenshot tool:
    usage
    python screenshot.py 'http://localhost:5000/presentation/strains'
"""
    


def main():
    if len(sys.argv) == 2:
        url = sys.argv[1]
        #driver = webdriver.PhantomJS("./phantomjs-2.1.1-linux-x86_64/bin/phantomjs")
        driver = webdriver.Chrome("chromedriver")
        getScreenShot(driver, url)

        driver.quit()
    else :
        print usage

main()