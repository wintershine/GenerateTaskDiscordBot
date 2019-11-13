import discord
from time import time
from asyncio import sleep
from discord.ext import tasks
import googleapiclient.errors

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

    msg = message.content[1:]
    result = [x.strip() for x in msg.split(' ')]
    command = result[0]

    if(command == 'add'):
        await add(result, False, message)
    
    elif(command == 'addofficial'):
        await add(result, True, message)
        
    elif(command == 'update'):
        await update(result, message)

    elif(command == 'latest'):
        await latest(result, message)

    elif(command == 'info'):
        await info(result, message)
        
    elif(command == 'leaderboard' or command == 'leaderboards'):
       await leaderboard(message)

    elif (command == 'help' or command == 'h' or command == 'commands' or command == 'options'):
        await help(result, message)

def getTaskAccountFromNickname(nickname):
    for taskAccount in taskAccountList.taskAccounts:
        if(taskAccount.nickname == nickname):
            return taskAccount
    return None

# botCommands Functions
async def add(result, isOfficial, message):
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

    newTaskAccount = taskAccount(spreadsheetUrl, nickname, isOfficial)
   
    try:
        sheet.updateTaskAccount(newTaskAccount)
        taskAccountList.add(newTaskAccount)
        taskAccountList.updateLastUpdated(newTaskAccount, time())
        await message.channel.send(f'Added account "{nickname}"')
    except googleapiclient.errors.HttpError as err:
        if '403' in str(err.content):
            msg = 'The bot does not have viewing rights to your sheet. Please make your sheet visible to the public or give view rights to '
            msg = msg + '"generatetaskleaderboards@quickstart-1561791519322.iam.gserviceaccount.com"'
            await message.channel.send(msg)
        else:
            await message.channel.send('An error happened while adding your sheet, try again later')
            print(err)
    

async def update(result, message):
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

async def latest(result, message):
    try:
        if(len(result) < 2):
            await message.channel.send('Error: You need to update to the latest version with the syntax !latest [[nickname]]')
        nickname = result[1]
        for res in result[2:]:
            nickname += ' ' + res
        taskAccountToUpdate = getTaskAccountFromNickname(nickname)
        if not taskAccountToUpdate:
            await message.channel.send(f'There is no registered account with the nickname "{nickname}"!')
            return
        remainingTasks = sheet.updateSpreadsheetToLatestVersion(taskAccountToUpdate.spreadsheetUrl)

        await message.channel.send('Your sheet was updated to the latest version!')
        if(remainingTasks):
            remainingTasksWarning = 'These tasks could not be filled into the new sheet. This means they got changed, renamed or removed:\n'
            for remainingTask, count in remainingTasks.items():
                remainingTasksWarning = remainingTasksWarning + f'{remainingTask} - {count} time(s)\n' 
            await message.channel.send(remainingTasksWarning)
            remainingTasksWarning = remainingTasksWarning + 'You will have to manually fill them in if applicable'
        await message.channel.send('Remember that if there were changes to the tier you are currently on, it is possible you might have to change the hidden "info" tab')
    except googleapiclient.errors.HttpError as err:
        if '403' in str(err.content):
            msg = 'The bot does not have edit rights to your sheet. Please give edit rights to "generatetaskleaderboards@quickstart-1561791519322.iam.gserviceaccount.com" '
            msg = msg + 'if you want it to update your sheet to the latest version.'
            await message.channel.send(msg)

async def info(result, message):
    nickname = result[1]
    for res in result[2:]:
        nickname += ' ' + res
    taskAccountToGetInfoFrom = getTaskAccountFromNickname(nickname)
    if not taskAccountToGetInfoFrom:
        await message.channel.send(f'There is no registered account with the nickname "{nickname}"!')
        return
    await message.channel.send(taskAccountToGetInfoFrom.getAccountInfo())
    
async def leaderboard(message):
     await message.channel.send('The leaderboards can be found at https://docs.google.com/spreadsheets/d/1Pb4p4qFPaJ2nA7ABwxVzazF2pYDiIVpoGHH-BolKtJY')
        
async def help(result,message):
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

discordBotToken = ''
with open('discordbot_token.txt', 'r') as token:
    discordBotToken = token.read()

for taskAcc in sheet.loadKnownTaskAccounts():
    taskAccountList.add(taskAcc)
client.run(discordBotToken)
