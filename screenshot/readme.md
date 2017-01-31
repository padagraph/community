

*  *Screenshot tool for the ```presentation``` template*
*  Saves image in ```png``` format.
*  Use ```chromium``` through ```selenium``` for ```python``` & ```phantomjs```

## Installation

    $ make install
    
    # add drivers to ```$PATH```
    # 'ChromeDriver executable needs to be available in the path.
    $ export PATH=$PATH:./

## Usage  
        
### start geckodriver   
   
    $ ./geckodriver

### capture

    # url pointing to presentation template
    # ex: http://padagraph.io/presentation/strains
    $ python screenshot.py url crop.png


Open image ```crop.png```


## Todo

* add argparser
* add image size option 
* Select webdriver ( Phantomjs, gecko, chrome)
* script gviz for zoom selection, rotation  

PR welcome 
