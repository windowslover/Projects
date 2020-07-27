#-------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      Jason
#
# Created:     18/08/2018
# Copyright:   (c) Jason 2018
# Licence:     <your licence>
#-------------------------------------------------------------------------------


from Tkinter import *

class Application(Frame):

    def __init__(self, master):
        Frame.__init__(self,master)
        self.grid()
        self.button_clicks = 0
        self.create_widgets()

    def create_widgets(self):

        self.label = Label(self, text = "Click button to run:                 ")
        self.label.grid(row = 0, column = 0)
        self.button = Button(self)
        self.button["text"] = "Total Clicks: 0"
        self.button["command"] = self.update_count
        self.button.grid(row = 0, column = 1)

    def update_count(self):
         self.button_clicks += 1
         self.button["text"] = "Total Clicks: " + str(self.button_clicks)


root = Tk()
root.title("My Program")
root.geometry("300x100")

app = Application(root)
root.mainloop()






