

##  Screenshot tool for padagraph iframe

*  Select webdriver ( Phantomjs, gecko, chrome)
*  Use ```chromium``` through ```selenium``` for ```python``` & ```phantomjs```
*  Saves image in ```png``` format.
*  different templates 
*  image size 
*  initial position z
*  labels & buttons visibility 

## Installation

    $ make install
    
    # add drivers to ```$PATH```
    # 'ChromeDriver executable needs to be available in the path.
    $ export PATH=$PATH:./

## Usage  
        
### start geckodriver, chromiumdriver or phantomjs   
   
    $ ./geckodriver
    # or
    $ ./chromedriver

### capture

    $ python screenshot.py strains crop.png --host http://localhost:5000 --width 600 --height 600 --zoom 600  

Open image ```crop.png```

![network](https://github.com/padagraph/community/blob/master/screenshot/crop.png?raw=true)


## Todo

* script gviz for zoom selection, rotation  

PR welcome 
