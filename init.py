import discord
from discord_slash import SlashCommand
from discord_slash.utils import manage_commands
from time import time
from asyncio import sleep
from discord.ext import tasks
from discord.ext import commands
import googleapiclient.errors

import gsheet
from taskAccount import *
from taskAccountList import taskAccountList

client = commands.Bot(intents = discord.Intents.default(), command_prefix='&')
slash = SlashCommand(client, sync_commands=True)
channelName = 'bot-command'

sheet = gsheet.gsheet()

maxChecksPerCycle = 50
maxUpdatesPerCycle = 5
taskAccountList = taskAccountList()

guild_ids = [594378237417881600, 569436224457146388]

@tasks.loop(minutes=5)
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

@slash.slash(
    name = "add",
    description = "Add a new account to the leaderboards",
    options = [manage_commands.create_option(
        name = "accountName",
        description = "Name of the account",
        option_type = 3,
        required = True
    ),
    manage_commands.create_option(
        name = "isTaskAccount",
        description = "Is the account an official task account?",
        option_type = 5,
        required = True
    ),
        manage_commands.create_option(
        name = "spreadsheetUrl",
        description = "Link to the account's generatetask spreadsheet",
        option_type = 3,
        required = True
    )],
    guild_ids = guild_ids
)
async def _add(ctx, accountName: str, isTaskAccount: bool, spreadsheetUrl: str):
    await ctx.respond()

    response = ""
    if(getTaskAccountFromNickname(accountName)):
        response = f'Account {accountName} already exists'
        await ctx.send(response)
        return

    newTaskAccount = taskAccount(spreadsheetUrl, accountName, isTaskAccount)
   
    try:
        sheet.updateTaskAccount(newTaskAccount)
        taskAccountList.add(newTaskAccount)
        taskAccountList.updateLastUpdated(newTaskAccount, time())
        response = f'Added account "{accountName}"' 
    except googleapiclient.errors.HttpError as err:
        if '403' in str(err.content):
            msg = 'The bot does not have viewing rights to your sheet. Please make your sheet visible to the public or give view rights to '
            msg = msg + '"generatetaskleaderboards@quickstart-1561791519322.iam.gserviceaccount.com"'
            response = msg
        else:
            response = 'An error happened while adding your sheet, try again later or contact Sarasun#3674 (Torgasun) on discord for support'
            print(err)

    await ctx.send(response)

@slash.slash(
    name = "modifyAccount",
    description = "Change an account's name, taskAccount status or spreadsheet link",
    options = [manage_commands.create_option(
        name = "currentAccountName",
        description = "Name of the account currently",
        option_type = 3,
        required = True
    ),
    manage_commands.create_option(
        name = "newAccountName",
        description = "Name you want to change the account to",
        option_type = 3,
        required = True
    ),
    manage_commands.create_option(
        name = "isTaskAccount",
        description = "Is the account an official task account?",
        option_type = 5,
        required = True
    ),
    manage_commands.create_option(
        name = "spreadsheetUrl",
        description = "Link to the new spreadsheet",
        option_type = 3,
        required = True
    )],
    guild_ids = guild_ids
)
async def _modifyAccount(ctx, oldAccountName: str, newAccountName: str, isTaskAccount: bool, spreadsheetUrl: str):
    await ctx.respond()

    taskAccount = getTaskAccountFromNickname(oldAccountName)
    response = ""
    if(taskAccount):
        taskAccount.isOfficial = isTaskAccount
        taskAccount.spreadsheetUrl = spreadsheetUrl
        taskAccount.nickname = newAccountName
    else:
        response = f'Account {oldAccountName} does not exist'
        await ctx.send(response)
        return

    try:
        sheet.deleteAccount(oldAccountName)
        sheet.updateTaskAccount(taskAccount)
        taskAccountList.updateLastUpdated(taskAccount, time())
        response = f'Modified account "{oldAccountName}"' 
    except googleapiclient.errors.HttpError as err:
        if '403' in str(err.content):
            msg = 'The bot does not have viewing rights to your new sheet. Please make it visible to the public or give view rights to '
            msg = msg + '"generatetaskleaderboards@quickstart-1561791519322.iam.gserviceaccount.com"'
            response = msg
        else:
            response = 'An error happened while modifying your sheet, try again later or contact Sarasun#3674 (Torgasun) on discord for support'
            print(err)

    await ctx.send(response)

@slash.slash(
    name = "deleteAccount",
    description = "Removes an account from the leaderboards",
    options = [manage_commands.create_option(
        name = "accountName",
        description = "Name of the account",
        option_type = 3,
        required = True)],
    guild_ids = guild_ids
)
async def _deleteAccount(ctx, accountName: str):
    await ctx.respond()

    taskAccount = getTaskAccountFromNickname(accountName)
    if(taskAccount):
        sheet.deleteAccount(accountName)
        taskAccountList.remove(taskAccount)
        await ctx.send(f'Account "{accountName}" was removed from the leaderboards')
    else:
        await ctx.send(f'Account "{accountName}" does not exist')
        return

@slash.slash(
    name = "update",
    description = "Updates the leaderboards for an account",
    options = [manage_commands.create_option(
        name = "accountName",
        description = "Name of the account",
        option_type = 3,
        required = True
    )],
    guild_ids = guild_ids
)
async def _update(ctx, accountName: str):
    await ctx.respond()

    response = ""
    taskAccountToUpdate = getTaskAccountFromNickname(accountName)
    if not taskAccountToUpdate:
        response = f'There is no registered account with the nickname "{accountName}"!'
        await ctx.send(response)
        return
    sheet.updateTaskAccount(taskAccountToUpdate)
    taskAccountList.updateLastUpdated(taskAccountToUpdate, time())
    response = f'Updated account "{accountName}"\n'
    response = response + taskAccountToUpdate.getAccountInfo()

    await ctx.send(response)

@slash.slash(
    name = "latest",
    description = "Updates a user's spreadsheet to the latest version",
    options = [manage_commands.create_option(
        name = "accountName",
        description = "Name of the account",
        option_type = 3,
        required = True
    )],
    guild_ids = guild_ids
)
async def _latest(ctx, accountName: str):
    await ctx.respond()

    response = ""
    try:
        taskAccountToUpdate = getTaskAccountFromNickname(accountName)
        if taskAccountToUpdate is None:
            response = f'There is no registered account with the nickname "{accountName}"!'
            await ctx.send(response)
            return
        remainingTasks = sheet.updateSpreadsheetToLatestVersion(taskAccountToUpdate.spreadsheetUrl)

        response = 'Your sheet was updated to the latest version!\n'
        if(remainingTasks):
            remainingTasksWarning = 'These tasks could not be filled into the new sheet. This means they got changed, renamed or removed:\n'
            for remainingTask, count in remainingTasks.items():
                remainingTasksWarning = remainingTasksWarning + f'{remainingTask} - {count} time(s)\n' 
            remainingTasksWarning = remainingTasksWarning + 'You will have to manually fill them in if applicable\n'
            response = response + remainingTasksWarning
        response = response + 'Remember that if there were changes to the tier you are currently on, it is possible you might have to change the hidden "info" tab'
    except googleapiclient.errors.HttpError as err:
        if '403' in str(err.content):
            response = 'The bot does not have edit rights to your sheet. Please give edit rights to "generatetaskleaderboards@quickstart-1561791519322.iam.gserviceaccount.com" '
            response = response + 'if you want it to update your sheet to the latest version.'
    
    await ctx.send(response)

@slash.slash(
    name = "leaderboards",
    description = "Posts a link to the leaderboards",
    guild_ids = guild_ids
)
async def _leaderboards(ctx):
    await ctx.respond()
    await ctx.send('The leaderboards can be found at https://docs.google.com/spreadsheets/d/1Pb4p4qFPaJ2nA7ABwxVzazF2pYDiIVpoGHH-BolKtJY')

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
