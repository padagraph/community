

*  *Screenshot tool for the ```presentation``` template*
*  Saves image in ```png``` format.
*  Use ```chromium``` through ```selenium``` for ```python``` & ```phantomjs```

## Installation

    $ make install

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

PR welcome 
