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

    BLANK_SHEET_ID = '1YJK_ZS66u_R48gJmsRQ2Qt-wxki7Nr3Dn9g8qLLQadU'
    DASHBOARD_ID = 892013748
    EASY_ID = 329575153
    MEDIUM_ID = 1727754730
    HARD_ID = 609485244
    ELITE_ID = 515954571
    Extra_ID = 1316949566
    Pets_ID = 2119535386
    PASSIVE_ID = 334976592

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
            if result.get('values') is None:
                return taskAccounts
            for account in result.get('values'):
                spreadsheetUrl = account[8]
                nickname = account[0]
                isOfficial = account[7] == 'True' or account[7] == 'TRUE'

                newTaskAccount = taskAccount(spreadsheetUrl, nickname, isOfficial)
                newTaskAccount.easyProgress = int(account[1])
                newTaskAccount.mediumProgress = int(account[2])
                newTaskAccount.hardProgress = int(account[3])
                newTaskAccount.eliteProgress = int(account[4])
                newTaskAccount.petsProgress = int(account[5])
                newTaskAccount.extraProgress = int(account[6])
                newTaskAccount.lastUpdated = float(account[9])
                if (account[10]):
                    newTaskAccount.currentTask = account[10]
                else:
                    newTaskAccount.currentTask = "None"

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
                'Pets!A2:C',
                'Extra!A2:C',
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
                    if (range.get('values') and len(range.get('values')[0]) != 0):
                        difficultyCompletions.append(range.get('values')[0][0])
                    else:
                        difficultyCompletions.append('None')
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
                    if(len(taskCompletion) != 0 and taskCompletion == 'x'):
                        count+=1
                difficultyTotals.append(count)

            currentTask = difficultyCompletions[len(difficultyCompletions)-1]

            taskAccount.easyProgress = int(difficultyTotals[0])
            taskAccount.mediumProgress = int(difficultyTotals[1])
            taskAccount.hardProgress = int(difficultyTotals[2])
            taskAccount.eliteProgress = int(difficultyTotals[3])
            taskAccount.petsProgress = int(difficultyTotals[4])
            taskAccount.extraProgress = int(difficultyTotals[5])
            taskAccount.currentTask = currentTask

            self.updateLeaderboards(taskAccount)
        except Exception as e:
            print(e)
            raise

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
            taskAccount.petsProgress,
            taskAccount.extraProgress,
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

    def deleteAccount(self, accountName):
        scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        gsclient = gspread.authorize(creds)
        sheet = gsclient.open_by_key(self.LEADERBOARDS_ID)
        worksheet = sheet.worksheet("RawData")

        existingAccounts = worksheet.col_values(1)

        for nickname in existingAccounts:
            if (nickname == accountName):
                index = existingAccounts.index(nickname) + 1
                
                worksheet.delete_row(index)
                return

    def updateSpreadsheetToLatestVersion(self, spreadsheetUrl):
        try:
            scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
            creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)

            service = build('sheets', 'v4', credentials=creds)
            sheet = service.spreadsheets()

            spreadsheetId = self.getIdFromUrl(spreadsheetUrl)
            infoTabId = 0

            # Get all task completions
            range_names = [
                'Easy!A2:C',
                'Medium!A2:C',
                'Hard!A2:C',
                'Elite!A2:C',
                'Pets!A2:C',
                'Extra!A2:C',
                'Passive!A2:C',
            ]

            sheet_names = [
                'Easy',
                'Medium',
                'Hard',
                'Elite',
                'Pets',
                'Extra',
                'Passive'
            ]

            completionsResult = sheet.values().batchGet(
                spreadsheetId = spreadsheetId,
                ranges = range_names,
                valueRenderOption = 'FORMATTED_VALUE').execute()

            completedTaskDictionary = {}
            for range in completionsResult.get('valueRanges'):
                for x in range.get('values'):
                    if (len(x) >= 3):
                        if x[0] in completedTaskDictionary:
                            completedTaskDictionary[x[0]] = completedTaskDictionary[x[0]] + 1
                        else:
                            completedTaskDictionary[x[0]] = 1

            # Get sheet IDs to delete
            res = sheet.get(spreadsheetId=spreadsheetId).execute()
            sheet_ids = []
            for sh in res.get('sheets'):
                if(sh.get('properties').get('title') == 'Info'):
                    infoTabId = sh.get('properties').get('sheetId')
                elif(sh.get('properties').get('title') in sheet_names):
                    sheet_ids.append(sh.get('properties').get('sheetId'))

            sheet_delete_requests = []
            for sheet_id in sheet_ids:
                sheet_delete_requests.append({
                    'deleteSheet': {
                        'sheetId': sheet_id
                    }
                })

            # Delete old sheets
            delete_sheets_body = {
                'requests': sheet_delete_requests
            }

            sheet.batchUpdate(spreadsheetId=spreadsheetId,body=delete_sheets_body).execute()

            # Copy new sheets
            source_sheet_ids = [
                self.EASY_ID,
                self.MEDIUM_ID,
                self.HARD_ID,
                self.ELITE_ID,
                self.Pets_ID,
                self.Extra_ID,
                self.PASSIVE_ID,
            ]

            copy_sheet_to_another_spreadsheet_request_body = {
                'destination_spreadsheet_id': spreadsheetId,
            }

            updated_sheet_ids = []
            for source_sheet_id in source_sheet_ids:
                res = sheet.sheets().copyTo(spreadsheetId=self.BLANK_SHEET_ID, sheetId=source_sheet_id, body=copy_sheet_to_another_spreadsheet_request_body).execute()

                updated_sheet_ids.append(res.get('sheetId'))
            
            # Rename new sheets
            sheet_rename_requests = []
            i = 0
            for sheet_name in sheet_names:
                sheet_rename_requests.append({
                    'updateSheetProperties': {
                        'properties': {
                            'title': sheet_name,
                            'sheetId': updated_sheet_ids[i],
                        },
                        'fields': 'title'
                    }
                })
                i = i+1

            rename_sheets_body = {
                'requests': sheet_rename_requests
            }
            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=rename_sheets_body).execute()


            # Restore task completions
            taskNames_range_names = [
                'Easy!A2:A',
                'Medium!A2:A',
                'Hard!A2:A',
                'Elite!A2:A',
                'Pets!A2:A',
                'Extra!A2:A',
                'Passive!A2:A'
            ]

            taskNamesResult = sheet.values().batchGet(
                spreadsheetId = spreadsheetId,
                ranges = taskNames_range_names,
                valueRenderOption = 'FORMATTED_VALUE').execute()

            update_cells_requests = []

            i = 0
            for range in taskNamesResult.get('valueRanges'):
                rows = []
                for x in range.get('values'):
                    if (x[0] in completedTaskDictionary):
                        # need to append RowData objects, not just a string
                        if (x[0] == 'Skill pets' or x[0] == 'Other pets'):
                            rows.append({
                                'values': [{
                                    'userEnteredValue': {
                                        'stringValue': 'Completed' 
                                    },
                                }]
                            })
                        else:
                            rows.append({
                                'values': [{
                                    'userEnteredValue': {
                                        'stringValue': 'x' 
                                    },
                                }]
                            })
                        if(completedTaskDictionary[x[0]] < 2):
                            completedTaskDictionary.pop(x[0])
                        else:
                            completedTaskDictionary[x[0]] = completedTaskDictionary[x[0]] - 1
                    else:
                        rows.append({
                            'values': [{
                                'userEnteredValue': {},
                            }]
                        })

                update_cells_requests.append({
                    'updateCells': {
                        'rows': rows,
                        'fields': 'userEnteredValue',
                        'range': {
                            'sheetId': updated_sheet_ids[i],
                            'startColumnIndex': 2,
                            'endColumnIndex': 3,
                            'startRowIndex': 1,
                        }
                    }
                })
                i = i + 1

            update_cells_body = {
                'requests': update_cells_requests
            }

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=update_cells_body).execute()
            
            # Force google to update function results. Google seems to think there was no change when it is done through the API
            # so function results are not always updated. This break the info tab and therefore the dashboard.
            # We simply rewrite the exact same functions into the info tab.
            info_functions = [
                '=COUNTA(Easy!B:B)-1', '=COUNTA(Easy!C:C)-1', '',
                '=COUNTA(Medium!B:B)-1', '=COUNTA(Medium!C:C)-1', '',
                '=COUNTA(Hard!B:B)-1', '=COUNTA(Hard!C:C)-1', '',
                '=COUNTA(Elite!B:B)-1', '=COUNTA(Elite!C:C)-1',
            ]

            update_functions_rows = []
            for info_function in info_functions:
                if(info_function == ''):
                    update_functions_rows.append({
                        'values': [{
                            'userEnteredValue': {},
                        }]
                    })            
                else:
                    update_functions_rows.append({
                        'values': [{
                            'userEnteredValue': {
                                'formulaValue': info_function
                            },
                        }]
                    })

            refresh_functions_body = {
                'requests': [{
                    'updateCells': {
                        'rows': update_functions_rows,
                        'fields': 'userEnteredValue',
                        'range': {
                            'sheetId': infoTabId,
                            'startColumnIndex': 1,
                            'endColumnIndex': 2,
                            'startRowIndex': 0,
                            'endRowIndex': 11
                    }
                }
                }]
            }

            sheet.batchUpdate(spreadsheetId=spreadsheetId, body=refresh_functions_body).execute()
            
            return completedTaskDictionary
        except Exception: raise

    def getSpreadsheetLastUpdatedTime(self, spreadsheetUrl):
        scope = ['https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
        service = build('drive', 'v3', credentials=creds)
        try:
            result = service.files().get(fileId=self.getIdFromUrl(spreadsheetUrl), fields='modifiedTime').execute()

            unformatted = result.get('modifiedTime')
            # fromisoformat does not support the letter timezone notation
            ts = datetime.fromisoformat(unformatted.replace("Z", "+00:00")).timestamp()
            return ts
        except Exception as e:
            return 0
            
    def getIdFromUrl(self, url):
        return re.search('\/d\/(.*?)(\/|$)', url).group(1)
