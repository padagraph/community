

*  *Screenshot tool for the ```presentation``` template*
*  Saves image in ```png``` format.
*  Use ```chromium``` through ```selenium``` for ```python``` & ```phantomjs```

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

    # url pointing to presentation template
    # ex: http://padagraph.io/presentation/strains
    $ python screenshot.py strains --host http://localhost:5000 -t iframe -o crop.png --width 600 --height 600 --zoom 600  

Open image ```crop.png```


## Todo

* add argparser
* add image size option 
* Select webdriver ( Phantomjs, gecko, chrome)
* script gviz for zoom selection, rotation  

PR welcome 
