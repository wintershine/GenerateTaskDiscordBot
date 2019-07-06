# BSD 3-Clause License
# Copyright (c) 2019, Hugonun(https://github.com/hugonun)
# All rights reserved.

import os.path
import re
import gspread
from time import time
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build

class gsheet(object):
    LEADERBOARDS_ID = '1Pb4p4qFPaJ2nA7ABwxVzazF2pYDiIVpoGHH-BolKtJY'

    def getKnownTaskAccounts(self):
        scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        gsclient = gspread.authorize(creds)
        sheet = gsclient.open_by_key(self.LEADERBOARDS_ID)
        worksheet = sheet.worksheet("RawData")
    
    def updateTaskAccount(self, taskAccount):
        try:
            scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
            gsclient = gspread.authorize(creds)
            sheet = gsclient.open_by_url(taskAccount.spreadsheetUrl)

            ranges = [
                ['Easy', 3],
                ['Medium', 3],
                ['Hard', 3],
                ['Elite', 3],
                ['Master', 3],
                ['God', 3]
            ]

            i = 0
            difficultyCompletions = [0,0,0,0,0,0]
            for range in ranges:
                difficultyCompletions[i] = sheet.worksheet(range[0]).col_values(range[1])
                i+=1

            i = 0
            difficultyTotals = [0,0,0,0,0,0]
            for difficultyCompletion in difficultyCompletions:
                count = 0
                for taskCompletion in difficultyCompletion:
                    if(taskCompletion == 'x'):
                        count+=1
                difficultyTotals[i] = count
                i+=1
            currentTask = sheet.worksheet('DASHBOARD').cell(15,2).value

            taskAccount.easyProgress = int(difficultyTotals[0])
            taskAccount.mediumProgress = int(difficultyTotals[1])
            taskAccount.hardProgress = int(difficultyTotals[2])
            taskAccount.eliteProgress = int(difficultyTotals[3])
            taskAccount.masterProgress = int(difficultyTotals[4])
            taskAccount.godProgress = int(difficultyTotals[5])
            taskAccount.currentTask = currentTask
            taskAccount.lastUpdated = time()

            self.updateLeaderboards(taskAccount)
        except gspread.exceptions.APIError: raise 

        

    def updateLeaderboards(self, taskAccount):
        scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        gsclient = gspread.authorize(creds)
        sheet = gsclient.open_by_key(self.LEADERBOARDS_ID)
        worksheet = sheet.worksheet("RawData")

        values = [
            taskAccount.nickname,
            taskAccount.easyProgress,
            taskAccount.mediumProgress,
            taskAccount.hardProgress,
            taskAccount.eliteProgress,
            taskAccount.masterProgress,
            taskAccount.godProgress,
            taskAccount.isOfficial,
            taskAccount.spreadsheetUrl
        ]

        existingAccounts = worksheet.col_values(1)

        for nickname in existingAccounts:
            if (nickname == taskAccount.nickname):
                index = existingAccounts.index(nickname) + 1
                cell_list = worksheet.range(f'A{index}:I{index}')

                i = 0
                for cell in cell_list:
                    cell.value = values[i]
                    i+=1
                worksheet.update_cells(cell_list)
                return
        
        #Add new row if the account was not on leaderboards yet
        worksheet.append_row(values)

    def getSpreadsheetLastUpdatedTime(self, spreadsheetUrl):
        scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        service = build('drive', 'v3', credentials=creds)
        try:
            result = service.files().get(fileId=self.getIdFromUrl(spreadsheetUrl), fields='modifiedTime').execute()
        except Exception as e:
            print(e)
        unformatted = result.get('modifiedTime')
        # fromisoformat does not support the letter timezone notation
        ts = datetime.fromisoformat(unformatted.replace("Z", "+00:00")).timestamp()
        return ts

    def getIdFromUrl(self, url):
        untrimmed = re.search('/[-\w]{25,}/', url).group()
        return untrimmed[1:len(untrimmed)-1]
