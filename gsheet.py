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

from taskAccount import taskAccount

class gsheet(object):
    LEADERBOARDS_ID = '1Pb4p4qFPaJ2nA7ABwxVzazF2pYDiIVpoGHH-BolKtJY'

    def loadKnownTaskAccounts(self):
        try:
            scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)

            service = build('sheets', 'v4', credentials=creds)
            sheet = service.spreadsheets()

            range_name = 'RawData!A2:K'

            result = sheet.values().get(
                spreadsheetId = self.LEADERBOARDS_ID,
                range=range_name).execute()
            
            taskAccounts = []
            for account in result.get('values'):
                spreadsheetUrl = account[8]
                nickname = account[0]
                isOfficial = account[7] == 'True' or account[7] == 'TRUE'

                newTaskAccount = taskAccount(spreadsheetUrl, nickname, isOfficial)
                newTaskAccount.easyProgress = int(account[1])
                newTaskAccount.mediumProgress = int(account[2])
                newTaskAccount.hardProgress = int(account[3])
                newTaskAccount.eliteProgress = int(account[4])
                newTaskAccount.masterProgress = int(account[5])
                newTaskAccount.godProgress = int(account[6])
                newTaskAccount.lastUpdated = float(account[9])
                newTaskAccount.currentTask = account[10]

                taskAccounts.append(newTaskAccount)

            return taskAccounts
        except Exception: raise

    def updateTaskAccount(self, taskAccount):
        try:
            scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)

            service = build('sheets', 'v4', credentials=creds)
            sheet = service.spreadsheets()

            range_names = [
                'Easy!A2:C',
                'Medium!A2:C',
                'Hard!A2:C',
                'Elite!A2:C',
                'Master!A2:C',
                'God!A2:C',
                'DASHBOARD!B15'
            ]

            result = sheet.values().batchGet(
                spreadsheetId = self.getIdFromUrl(taskAccount.spreadsheetUrl),
                ranges = range_names,
                valueRenderOption = 'FORMATTED_VALUE').execute()

            difficultyCompletions = []
            for range in result.get('valueRanges'):
                compl = []
                if(range.get('range') == 'DASHBOARD!B15'):
                    difficultyCompletions.append(range.get('values')[0][0])
                else:
                    for x in range.get('values'):
                        if(len(x) < 3):
                            compl.append('')
                        else:
                            compl.append(x[2])
                    difficultyCompletions.append(compl)

            difficultyTotals = []
            for difficultyCompletion in difficultyCompletions[:len(difficultyCompletions) - 1]:
                count = 0
                for taskCompletion in difficultyCompletion:
                    if(len(taskCompletion) != 0):
                        count+=1
                difficultyTotals.append(count)
            if(len(difficultyCompletions[len(difficultyCompletions)-1]) != 0):
                currentTask = difficultyCompletions[len(difficultyCompletions)-1]
            else:
                currentTask = 'None'

            taskAccount.easyProgress = int(difficultyTotals[0])
            taskAccount.mediumProgress = int(difficultyTotals[1])
            taskAccount.hardProgress = int(difficultyTotals[2])
            taskAccount.eliteProgress = int(difficultyTotals[3])
            taskAccount.masterProgress = int(difficultyTotals[4])
            taskAccount.godProgress = int(difficultyTotals[5])
            taskAccount.currentTask = currentTask

            self.updateLeaderboards(taskAccount)
        except Exception: raise

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
            taskAccount.spreadsheetUrl,
            taskAccount.lastUpdated,
            taskAccount.currentTask
        ]

        existingAccounts = worksheet.col_values(1)

        for nickname in existingAccounts:
            if (nickname == taskAccount.nickname):
                index = existingAccounts.index(nickname) + 1
                cell_list = worksheet.range(f'A{index}:K{index}')

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
