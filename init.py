import discord
from time import time
from asyncio import sleep
from discord.ext import tasks

import gsheet
from taskAccount import *
from taskAccountList import taskAccountList

client = discord.Client()
channelName = 'bot-command'

sheet = gsheet.gsheet()

maxChecksPerCycle = 50
maxUpdatesPerCycle = 10
taskAccountList = taskAccountList()

@tasks.loop(minutes=2)
async def updateTaskAccounts():
    taskAccounts = taskAccountList.taskAccounts
    print('Starting periodic update...')
    accountsToCheck = maxChecksPerCycle
    if(len(taskAccounts) == 0):
        print('Finished periodic update')
        return
    elif(len(taskAccounts) < accountsToCheck):
        accountsToCheck = len(taskAccounts)

    updatesThisCycle = 0
    for taskAccount in taskAccountList.getOldestUpdatedAccounts(accountsToCheck):
        sheetLastUpdated = sheet.getSpreadsheetLastUpdatedTime(taskAccount.spreadsheetUrl)
        if(sheetLastUpdated > taskAccount.lastUpdated):
            print(f'Updating {taskAccount.nickname}')
            sheet.updateTaskAccount(taskAccount)
            updatesThisCycle += 1
            await sleep(1)
        taskAccountList.updateLastUpdated(taskAccount, time())
        if(updatesThisCycle == maxUpdatesPerCycle):
            print('Finished periodic update')
            return
        await sleep(1)
    print('Finished periodic update')

@client.event
async def on_ready():
    if(not updateTaskAccounts.get_task()):
        updateTaskAccounts.start()

@client.event
async def on_message(message):
    if message.author == client.user or not message.content.startswith('!') or message.channel.name != channelName:
        return

    # Command to add a spreadsheet to the bot
    msg = message.content[1:]
    result = [x.strip() for x in msg.split(' ')]
    command = result[0]

    if(command == 'add'):
        if(len(result) < 3):
            await message.channel.send('Error: You need to add accounts with the syntax !add [[spreadsheetUrl]] [[nickname]]')
            return
        spreadsheetUrl = result[1]
        nickname = result[2]
        for res in result[3:]:
            nickname += ' ' + res
        
        if(getTaskAccountFromNickname(nickname)):
            await message.channel.send(f'Account {nickname} already exists')
            return

        newTaskAccount = taskAccount(spreadsheetUrl, nickname, False)
        try:
            sheet.updateTaskAccount(newTaskAccount)
        except Exception as e:
            await message.channel.send(f'Error: {e}')
            return
        taskAccountList.add(newTaskAccount)
        taskAccountList.updateLastUpdated(newTaskAccount, time())
        await message.channel.send(f'Added account "{nickname}"')
    elif(command == 'addofficial'):
        if(len(result) < 3):
            await message.channel.send('Error: You need to add task accounts with the syntax !addofficial [[spreadsheetUrl]] [[nickname]]')
            return
        spreadsheetId = result[1].strip()
        nickname = result[2]
        for res in result[3:]:
            nickname += ' ' + res
        
        if(getTaskAccountFromNickname(nickname)):
            await message.channel.send(f'Account {nickname} already exists')
            return

        newTaskAccount = taskAccount(spreadsheetId, nickname, True)
        try:
            sheet.updateTaskAccount(newTaskAccount)
        except Exception as e:
            await message.channel.send(f'Error: {e}')
            return
        taskAccountList.add(newTaskAccount)
        taskAccountList.updateLastUpdated(taskAccount, time())
        await message.channel.send(f'Added account "{nickname}"')
    elif(command == 'update'):
        if(len(result) < 2):
            await message.channel.send('Error: You need to update accounts with the syntax !update [[nickname]]')
        nickname = result[1]
        for res in result[2:]:
            nickname += ' ' + res
        taskAccountToUpdate = getTaskAccountFromNickname(nickname)
        if not taskAccountToUpdate:
            await message.channel.send(f'There is no registered account with the nickname "{nickname}"!')
            return
        sheet.updateTaskAccount(taskAccountToUpdate)
        taskAccountList.updateLastUpdated(taskAccountToUpdate, time())
        await message.channel.send(f'Updated account "{nickname}"')
        await message.channel.send(taskAccountToUpdate.getAccountInfo())

    elif(command == 'info'):
        nickname = result[1]
        for res in result[2:]:
            nickname += ' ' + res
        taskAccountToGetInfoFrom = getTaskAccountFromNickname(nickname)
        if not taskAccountToGetInfoFrom:
            await message.channel.send(f'There is no registered account with the nickname "{nickname}"!')
            return
        await message.channel.send(taskAccountToGetInfoFrom.getAccountInfo())

    elif(command == 'leaderboard' or command == 'leaderboards'):
        await message.channel.send('The leaderboards can be found at https://docs.google.com/spreadsheets/d/1Pb4p4qFPaJ2nA7ABwxVzazF2pYDiIVpoGHH-BolKtJY')

    elif (command == 'help' or command == 'h' or command == 'commands' or command == 'options'):
        if(len(result) == 1):
            await message.channel.send('Available commands: !add, !addofficial !update, !info, !leaderboards, !help,')
        elif(len(result) == 2):
            if(result[1] == 'add'):
                await message.channel.send('"add" allows you to add your account to the leaderboards! \n\
                    Syntax: !add [[spreadsheetUrl]] [[nickname]]. I recommend that you set your nickname as your RS name \
                    but it is not required'.replace("                        ",""))
            elif(result[1] == 'addofficial'):
                await message.channel.send('"addofficial" allows you to add your official taskaccount to the leaderboards! \n\
                    Syntax: !addofficial [[spreadsheetUrl]] [[nickname]]. I recommend that you set your nickname as your RS name \
                    but it is not required'.replace("                        ",""))
            elif(result[1] == 'update'):
                await message.channel.send('"update" will force an update on the leaderboards for your account \n\
                    Syntax: !update [[nickname]]'.replace("                        ",""))
            elif(result[1] == 'info'):
                await message.channel.send('"info" will give you information about a specific task account \n\
                    Syntax: !info [[nickname]]'.replace("                        ",""))
            elif(result[1] == 'leaderboards'):
                await message.channel.send('"leaderboards" will provide a link to the leaderboards \n\
                    Syntax: !info [[nickname]]'.replace("                        ",""))
        else:
            await(message.channel.send('Unrecognized help command'))

def getTaskAccountFromNickname(nickname):
    for taskAccount in taskAccountList.taskAccounts:
        if(taskAccount.nickname == nickname):
            return taskAccount

    return None

discordBotToken = ''
with open('discordbot_token.txt', 'r') as token:
    discordBotToken = token.read()

for taskAcc in sheet.loadKnownTaskAccounts():
    taskAccountList.add(taskAcc)
client.run(discordBotToken)
