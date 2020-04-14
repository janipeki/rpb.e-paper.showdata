import redis                                                                                                                                                                                     
import sys
import time
import os
import configparser
from tkinter import *

import logging

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
    logging.info("tkinter Demo - open redis")

    configParser = getConfig()
    rhost = configParser.get('redis', 'rhost')
    password = configParser.get('redis', 'password')
    rhost = redis.Redis(host=rhost, port=6379, db=0, password=password)
    
    # # partial update
    logging.info("Start the show ...")

    root = Tk()
    var = StringVar()
    label = Label(root, textvariable = var, relief = RAISED, anchor='w', justify = 'left' )
    label.pack()

    while True:
        
        # Get the values for the world:
        worldinfected, worldinfecnew, worlddeceased, worlddeceanew = getWorld(rhost)
        worldInfo = 'World: ' + worldinfected + ' - ' + worldinfecnew + ' - ' + worlddeceased + ' - ' + worlddeceanew
        logging.info(worldInfo)

        # Get the values for the countries which where last updated:
        countrystats  = getItem(rhost)
        counter = 0
        countryInfo = ''
        for countries in countrystats.keys():
            logging.info('Country: ' + countries.decode('UTF-8'))
            country = countries.decode('UTF-8')
            infected, infecnew, deceased, deceanew = countrystats.get(countries)
            logging.info ('Values: ' + infected + ' - ' + infecnew + ' - ' + deceased + ' - ' + deceanew)
#             countryInfo = countryInfo + '\n' + country + ': ' + infected + ' - ' + infecnew + ' - ' + deceased + ' - ' + deceanew
            countryInfo = country + ': ' + infected + ' - ' + infecnew + ' - ' + deceased + ' - ' + deceanew

            counter += 1
    
        # Output the values:
        logging.info('Count of Countries: ' + str(counter))
        var.set(worldInfo + "\n" + countryInfo)
        root.update_idletasks()

        time.sleep(2)

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    epd2in13.epdconfig.module_exit()
    exit()

