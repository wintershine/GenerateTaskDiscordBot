from sortedcontainers import SortedKeyList

def sortFunc(taskAccount):
    return taskAccount.lastUpdated

class taskAccountList():

    taskAccounts = SortedKeyList(key = sortFunc)

    def add(self, taskAccount):
        self.taskAccounts.add(taskAccount)

    def remove(self, taskAccount):
        self.taskAccounts.remove(taskAccount)

    def getOldestUpdatedAccounts(self, n):
        numberOfAccounts = len(list(self.taskAccounts.islice()))
        if(numberOfAccounts == 0):
            return list()
        elif(numberOfAccounts > n):
            return list(self.taskAccounts.islice(0,n))
        else:
            return list(self.taskAccounts.islice(0,numberOfAccounts))

    def updateLastUpdated(self, taskAccount, lastUpdated):
        # We have to remove the account and put it back into the list because lastUpdated is also the sorting key
        self.taskAccounts.remove(taskAccount)
        taskAccount.lastUpdated = lastUpdated
        self.taskAccounts.add(taskAccount)