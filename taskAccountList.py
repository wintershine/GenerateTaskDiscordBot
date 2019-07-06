# The point of this class is to provide a list that has a sort() method and a rotate() method
# without having to create and reassign a new list

class taskAccountList():

    taskAccounts = []

    def __init__(self, taskAccounts = []):
        self.taskAccounts = taskAccounts

    def sort(self, reverse):
        self.taskAccounts.sort(key = self.sortFunc, reverse = reverse)

    def sortFunc(self, taskAccount):
        return taskAccount.lastUpdated

    def add(self, taskAccount):
        self.taskAccounts.append(taskAccount)

    def rotate(self, n):
        self.taskAccounts = self.taskAccounts[n:] + self.taskAccounts[:n]