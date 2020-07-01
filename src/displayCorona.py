#!/usr/bin/python3

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
        return infected.replace(',', '.'), infecnew.replace(',', '.'), deceased.replace(',', '.'), deceanew.replace(',', '.')

# Get values of the last countries updated. 
# These values are stored in the redis key: Log:<epoch time stamp>
# To find the most actual entry:
#    - all keys of the name Log:* are imported
#    - then sorted
#    - and the first entry is taken
# From this entry the list of countries is taken and returned together
# with their values.
def getItem(rhost, countryCount):

    # Get the epoch of the last update:
    items = rhost.keys('NewLog:*')
    numbers = []
    for i in items:
        numbers.append (int(i.decode('UTF-8').partition(':')[2]))
    numbers.sort(reverse=True)
    newlog = []
    for i in range(0, countryCount):
        # TODO: During initialization or redis this does not work as long as 
        # less countries are changed as configured in config file
        newlog.append(rhost.hgetall('NewLog:' + str(numbers[i])))
#        newlog.append(str(numbers[i]))
    logging.info('NewLog: ' + str(numbers[0]))
    # Then get the entry of the last updates:

    countries =  {}
    count = 0
    for log in newlog:
        # And the entries for each country updated:
#        try:
            print ('log: ', log)
            for country, item in log.items():
                print (type(item))
                item = item.decode('UTF-8')
                values = item.split(':')
                infected, infecnew, deceased, deceanew = getVals(values)
                countries[count] = country, infected, infecnew, deceased, deceanew
                count = count + 1

#        except AttributeError:
#            print (countries[count - 1])
#            print (log)
#            countries[count - 1] = countries[count - 1], log
#            print (countries[count - 1])
    return countries

def key(event):
    logging.info("tkinter Demo - exit")
    logging.info ("pressed", repr(event.char))
    time.sleep(5)

logging.basicConfig(level=logging.DEBUG)

################### M A I N ##########################################################################################
try:
    logging.info("tkinter Demo - open redis")

    configParser = getConfig()
    rhost = configParser.get('redis', 'rhost')
    password = configParser.get('redis', 'password')
    rhost = redis.Redis(host=rhost, port=6379, db=0, password=password)
    countryCount = int(configParser.get('country', 'count'))
    countryNameLen = int(configParser.get('country', 'namelen'))
    
    # # partial update
    logging.info("Start the show ...")

    root = Tk()
    var = StringVar()
#     frame = Frame(root)
#     frame.pack()
#     b2 = Button(root, text='Quit', command=root.quit)
#     b2.pack(side=LEFT, padx=5, pady=5)
    label = Label(root, textvariable = var, relief = RAISED, anchor='w', justify = 'left' )
    label.config(font=("Courier", 24))
#    label.focus_set() 
#    label.bind('<Key>', key) 

    label.pack()

    while True:
        # Get the values for the world:
        worldinfected, worldinfecnew, worlddeceased, worlddeceanew = getWorld(rhost)
        worldinfectedlen = len(worldinfected) + 0
        worldinfecnewlen = len(worldinfecnew) + 2
        worlddeceasedlen = len(worlddeceased) + 2
        worlddeceanewlen = len(worlddeceanew) + 2
        
        worldInfo = 'World: '.ljust(14) + worldinfected.rjust(worldinfectedlen) + worldinfecnew.rjust(worldinfecnewlen) + worlddeceased.rjust(worlddeceasedlen) + worlddeceanew.rjust(worlddeceanewlen)
        logging.info(worldInfo)

        # Get the values for the countries which where last updated:
        countrystats  = getItem(rhost, countryCount)
        logging.info('Count of Countries: ' + str(len(countrystats)))
        countryInfo = ''
        for count in countrystats:
#             logging.info('Country: ' + count.decode('UTF-8'))
            country, infected, infecnew, deceased, deceanew = countrystats.get(count)
            country = country.decode('UTF-8')[:countryNameLen]
            logging.info ('Values: ' + country + '  ' + infected + '  ' + infecnew + ' - ' + deceased + '  ' + deceanew)
            countryInfo = countryInfo + '\n' + country.ljust(12) + ': ' + infected.rjust(worldinfectedlen) + infecnew.rjust(worldinfecnewlen) + deceased.rjust(worlddeceasedlen) + deceanew.rjust(worlddeceanewlen)

        # Output the values:
        logging.info ('countryInfo: ' + countryInfo)
        output = worldInfo + "\n" + countryInfo
        var.set(output)
        root.update_idletasks()

        time.sleep(2)

except IOError as e:
    logging.info(e)

except KeyboardInterrupt:
    logging.info("ctrl + c:")
    sys.exit(0)
    exit()

