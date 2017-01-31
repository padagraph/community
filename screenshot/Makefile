

.PHONY : install

install :

	pip install -r requirements.txt

	# phantomjs
	wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
	tar -xzf phantomjs-2.1.1-linux-x86_64.tar.bz2

	#chrome driver
	#wget https://chromedriver.storage.googleapis.com/2.27/chromedriver_linux64.zip
	wget https://chromedriver.storage.googleapis.com/2.26/chromedriver_linux64.zip
	unzip chromedriver_linux64.zip
	
	# geckodriver
	wget https://github.com/mozilla/geckodriver/releases/download/v0.13.0/geckodriver-v0.13.0-linux64.tar.gz
	tar -xzf geckodriver-v0.13.0-linux64.tar.gz



try :

	echo 