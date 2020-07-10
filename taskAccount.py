from time import time
from math import floor

#Task accounts

class taskAccount(object):
    easyProgress = 0
    mediumProgress = 0
    hardProgress = 0
    eliteProgress = 0
    extraProgress = 0
    petsProgress = 0
    currentTask = 'Unknown'
    isOfficial = False

    # In the taskAccountList, this parameter has to be modified through the updateLastUpdated method because
    # it is used as the sorting key. Any other way of changing it might make it unretrievable from the list
    lastUpdated = 0

    def __init__(self, spreadsheetUrl, nickname, isOfficial):
        self.spreadsheetUrl = spreadsheetUrl
        self.nickname = nickname
        self.isOfficial = isOfficial

    def getAccountInfo(self):
        return (f'**{self.nickname}:** Easy: {self.easyProgress}, Medium: {self.mediumProgress}, \
            Hard: {self.hardProgress}, Elite: {self.eliteProgress}, Extra: {self.extraProgress}, \
            Pets: {self.petsProgress}\n**Current Task:** {self.currentTask}\n**Time since last update:** \
            {self.formatTimeSinceUpdate()}').replace("            ", "")

    def formatTimeSinceUpdate(self):
        timeSinceLastUpdate = time() - self.lastUpdated
        seconds = round(timeSinceLastUpdate % 60, 2)
        minutes = floor(timeSinceLastUpdate/60) % 60
        hours = floor(timeSinceLastUpdate/(60*60)) % 24
        days = floor(timeSinceLastUpdate/(60*60*24))

        return f'{days} days {hours} hours {minutes} minutes {seconds} seconds'
        