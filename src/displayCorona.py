import redis                                                                                                                                                                                     
import sys
import time
import os
import configparser
picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')
libdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import logging
from waveshare_epd import epd2in13
from PIL import Image,ImageDraw,ImageFont
import traceback

def getConfig():
    configParser = configparser.RawConfigParser()   
    configFilePath = r'rpb.e-paper.showdata.config'
    configParser.read(configFilePath)
    return configParser

def getVals(valstring):
        infected = valstring[1].split('\'')[1].replace(' ', '')
        infecnew = valstring[2].split('\'')[1].replace(' ', '')
        deceased = valstring[3].split('\'')[1].replace(' ', '')
        deceanew = valstring[4].split('\'')[1].replace(' ', '')
        return infected, infecnew, deceased, deceanew

# Get values for the world
def getWorld(rhost):
    items = rhost.hgetall('World')
    for key, item in items.items():
        item = item.decode('UTF-8')
        worldvalues = item.split(':')
        infected, infecnew, deceased, deceanew = getVals(worldvalues)
        return infected, infecnew, deceased, deceanew

# Get values of the last countries updated. 
# These values are stored in the redis key: Log:<epoch time stamp>
# To find the most actual entry:
#    - all keys of the name Log:* are imported
#    - then sorted
#    - and the first entry is taken
# From this entry the list of countries is taken and returned together
# with their values.
def getItem(rhost):

    # Get the epoch of the last update:
    items = rhost.keys('NewLog:*')
    numbers = []
    for i in items:
        numbers.append (int(i.decode('UTF-8').partition(':')[2]))
    numbers.sort(reverse=True)
    high = numbers[0]

    # Then get the entry of the last update:
    newlog = rhost.hgetall('NewLog:' + str(high))
    
    # And the entries for each country updated:
    countries =  {}
    for country, item in newlog.items():
        country = country[:7]
        item = item.decode('UTF-8')
        values = item.split(':')
        infected, infecnew, deceased, deceanew = getVals(values)
        countries[country] = infected, infecnew, deceased, deceanew

    return countries

logging.basicConfig(level=logging.DEBUG)

################### M A I N ##########################################################################################
try:
    logging.info("epd2in13 Demo")

    configParser = getConfig()
    rhost = configParser.get('redis', 'rhost')
    password = configParser.get('redis', 'password')
    epd = epd2in13.EPD()
    epd.init(epd.lut_full_update)
    font15 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 15)
    font24 = ImageFont.truetype(os.path.join(picdir, 'Font.ttc'), 24)
    
    # # partial update
    logging.info("Start the show ...")

    rhost = redis.Redis(host=rhost, port=6379, db=0, password=password)
    while True:
        
        stats_image = Image.new('1', (epd.height, epd.width), 255)
        stats_draw = ImageDraw.Draw(stats_image)

        # Get the values for the world:
        worldinfected, worldinfecnew, worlddeceased, worlddeceanew = getWorld(rhost)
        logging.info('World: ' + worldinfected + ' - ' + worldinfecnew + ' - ' + worlddeceased + ' - ' + worlddeceanew)

        # Output the values for the world:
        stats_draw.text((0, 5), 'World', font = font15, fill = 0)
        stats_draw.text((0, 21), worldinfected, font = font15, fill = 0)
        stats_draw.text((70, 21), worldinfecnew, font = font15, fill = 0)
        stats_draw.text((140, 21), worlddeceased, font = font15, fill = 0)
        stats_draw.text((200, 21), worlddeceanew, font = font15, fill = 0)
    
        # Get the values for the countries which where last updated:
        countrystats  = getItem(rhost)
        counter = 0
        for countries in countrystats.keys():
            logging.info('Country: ' + countries.decode('UTF-8'))
            country = countries.decode('UTF-8')
            infected, infecnew, deceased, deceanew = countrystats.get(countries)
            logging.info ('Values: ' + infected + ' - ' + infecnew + ' - ' + deceased + ' - ' + deceanew)

            stats_draw.text((0, 39 + counter * 15), country, font = font15, fill = 0)
            stats_draw.text((70, 39 + counter * 15), infected, font = font15, fill = 0)
            stats_draw.text((130, 39 + counter * 15), infecnew, font = font15, fill = 0)
            stats_draw.text((180, 39 + counter * 15), deceased, font = font15, fill = 0)
            stats_draw.text((220, 39 + counter * 15), deceanew, font = font15, fill = 0)

            counter += 1
    
        epd.display(epd.getbuffer(stats_image))
        time.sleep(300)

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd2in13.epdconfig.module_exit()
    exit()

