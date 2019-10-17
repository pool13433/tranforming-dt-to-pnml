import Tkinter, Tkconstants, tkFileDialog, ScrolledText
import tkFont as font
import os
import tkMessageBox as dialog
import json

from Tkinter import * 
from PIL import ImageTk, Image
from datetime import datetime

from transform_logic import *
from input_validation import *

class TransformationUI(Frame):    

    def __init__(self, master=None):
        Frame.__init__(self, master)

        self.helvetica = font.Font(master,family='Helvetica', size=20, weight='bold')
        self.ubuntu12 = font.Font(master,family="Ubuntu Light", size= 12, weight=font.BOLD)   
        self.firacode12 = font.Font(master,family="Fira Code" , size=12 ,weight=font.BOLD)
        self.thsarabun12 = font.Font(master,family="TH SarabunPSK",size=14,weight=font.BOLD) 
        
        self.fontFamily = self.thsarabun12
        self.fontFamily['size'] = 16

        self.pack()
        self.createWidgets()

    def createWidgets(self):    

        self.makeLabelChoose(0,0)         
        self.makeBtnChoose(0,1)

        self.makeLabelFileInPath(1,0) 
        self.makeTxtbChoose(1,1)        

        #self.makeLabelProcessing(2,0)
        #self.makeImageLoading(2,1)

        self.makeLabelStartProcess(3,0)
        self.makeBtnStartProcess(3,1)

        self.makeLabelFinished(4,0)
        self.makeLabelProcessFinished(4,1)

        self.makeLabelFileOutPath(5,0)
        self.makeTxtbFileOut(5,1)

        self.makeTxtbConsole(6,1)

        self.makeBtnExit(7,1)
        
    # ****************** Label *********************        
    # #N, E, S, W, NE, NW, SE, and SW, 
    def makeLabelFinished(self,row,column):
        label_finished = Label(self,text = "Program Message:",font=self.fontFamily)
        label_finished['fg'] = "blue"
        label_finished.grid(row = row, column = column, sticky=E,pady = 2,padx = 5)    

    def makeLabelProcessing(self,row,column):
        label_process = Label(self,text = "Process Status:",font=self.fontFamily)
        label_process['fg'] = "blue"
        label_process.grid(row = row, column = column, sticky=E,pady = 2,padx = 5)    

    def makeLabelFileOutPath(self,row,column):
        label_out = Label(self,text = "Path File Output:",font=self.fontFamily)
        label_out['fg'] = "blue"
        label_out.grid(row = row, column = column, sticky=E,pady = 2,padx = 5)     

    def makeLabelFileInPath(self,row,column):
        label_in = Label(self,text = "Path File Input:",font=self.fontFamily)
        label_in['fg'] = "blue"
        label_in.grid(row = row, column = column, sticky=E,pady = 2,padx = 5)         

    def makeLabelChoose(self,row,column):
        label_choose = Label(self,text = "Choose File:",font=self.fontFamily)
        label_choose['fg'] = "blue"
        label_choose.grid(row = row, column = column, sticky=E,pady = 2,padx = 5)   
    def makeLabelStartProcess(self,row,column):
        label_choose = Label(self,text = "Start Process:",font=self.fontFamily)
        label_choose['fg'] = "blue"
        label_choose.grid(row = row, column = column, sticky=E,pady = 2,padx = 5)
    def makeLabelProcessFinished(self,row,column):      
        self.label_finished = Label(self,text = "Program Proscessing.",font=self.fontFamily)
        self.label_finished['fg'] = "black"
        self.label_finished.grid(row = row, column = column, sticky=W,pady = 2,padx = 5)   
    def setLabelProcessFinished(self,text):
        self.label_finished['text'] = text
    # ****************** Label *********************

    # ****************** Image *********************
    def makeImageLoading(self,row,column):
        imagefilename = "./images/box-loading.gif"
        #img_loading = ImageTk.PhotoImage(Image.open(imagefilename))        
        img_loading = PhotoImage(file=imagefilename, format="gif -index 2")
        label_loading =Label(self, image = img_loading,height = 90,width = 90)   
        label_loading.image = img_loading 
        label_loading.grid(row = row, column = column, sticky=W,pady = 10,padx = 10)           
    # ****************** Image *********************

    # ****************** Textbox *******************
    def makeTxtbFileOut(self,row,column):
        self.textbox_out = Entry(self,font=self.fontFamily)
        self.textbox_out.insert(END,'Result Out File after Processed.')
        self.textbox_out['width'] = 70        
        self.textbox_out['bg'] = '#eff0f1'
        self.textbox_out.pack({"side": "left"})        
        self.textbox_out.grid(row = row, column = column, sticky=W, pady = 2)
    def setTxtbFileOut(self,text):
        self.textbox_out.delete(0,END)
        self.textbox_out.insert(END,text)

    def makeTxtbConsole(self,row,column):        
        self.textbox_console = Text(self,font=self.fontFamily)
        self.textbox_console['width'] = 120        
        self.textbox_console['height'] = 9
        self.textbox_console['bg'] = '#eff0f1'
        #textbox_console.pack({"side": "left"})        
        self.textbox_console.grid(row = row, column = column, sticky=W, pady = 2)        
    def appendTxtbConsole(self,text,level='info'):
        self.textbox_console.insert(END,level+': '+text+'\n')
        self.textbox_console.see(END)

    def makeTxtbChoose(self,row,column):        
        self.textbox_choose = Entry(self,font=self.fontFamily)
        self.textbox_choose.insert(END,"")
        self.textbox_choose['width'] = 70        
        self.textbox_choose.pack({"side": "left"})        
        self.textbox_choose['bg'] = '#eff0f1'
        self.textbox_choose.grid(row = row, column = column, sticky=W, pady = 2)
    def setTxtbChooseVal(self,text = None):
        self.textbox_choose.delete(0,END)
        self.textbox_choose.insert(END,text)
    def getTxtbChooseVal(self):
        return self.textbox_choose.get()
    # ****************** Textbox *******************

    # ****************** Button *******************    
    def makeBtnChoose(self,row,column):        
        choose_file = Button(self,font=self.fontFamily)
        choose_file["text"] = "Choose file from directory"
        choose_file["fg"]   = "#ffffff"
        choose_file['bg'] = '#4267b2'
        choose_file['width'] = 25
        choose_file['height'] = 1
        choose_file["command"] =  self.commandBrowserFile
        #choose_file.pack({"side": "left"})
        choose_file.grid(row = row, column = column,sticky=W, pady = 2)

    def makeBtnStartProcess(self,row,column):
        start_process = Button(self,font=self.fontFamily)
        start_process["text"] = "Start Process"
        start_process["fg"]   = "#ffffff"
        start_process['bg'] = '#4267b2'
        start_process['width'] = 15
        start_process['height'] = 1
        start_process["command"] =  self.commandProcessTransforming
        #choose_file.pack({"side": "left"})
        start_process.grid(row = row, column = column,sticky=W, pady = 2)

    def makeBtnExit(self,row,column):     
        exit_program = Button(self,font=self.fontFamily)
        exit_program["text"] = "Exit Program."
        exit_program["fg"]   = "#ffffff"
        exit_program['bg'] = '#fa3e3e'
        exit_program['width'] = 15
        exit_program['height'] = 1
        exit_program["command"] =  self.commandExitProgram
        exit_program.grid(row = row, column = column,sticky=W, pady = 2)
    # ****************** Button *******************

    def commandExitProgram(self):
        result = dialog.askyesno("Confirm Sign out?","Do you want to confirm logging out?")
        if result:
            self.quit()

    def commandProcessTransforming(self):
        fullPathExcell = self.getTxtbChooseVal()         
        if fullPathExcell == '':
            dialog.showerror('Choose File from directory!','Cannot select file. Must select only xlsx file.')
        else:    
            print('fullPathExcell::=='+str(fullPathExcell))

            validate = InputValidation(fullPathExcell)
            validate.runValidateInput()
            messages = validate.read_messages()
            _error = messages['PROCESS_ERROR']['MESSAGE']['EN']
            resultValidates = validate.getValidtors()
            if len(resultValidates) > 0:
                for valid in resultValidates:
                    invalid_msg = json.dumps(valid,sort_keys=True,indent=3)
                    print('valid::=='+invalid_msg)
                    self.appendTxtbConsole(invalid_msg,'error')
                    self.setLabelProcessFinished(_error)
                dialog.showerror('Validate Input File Invalid','Input File Parameters Invalid!')
            else:            
                # handle output file
                now = datetime.now() # current date and time
                date_time = now.strftime("%Y%m%d_%H%M")
                dirFullPathPmnl = os.path.dirname(os.path.abspath(fullPathExcell))
                fillpathPnml = dirFullPathPmnl+'/outputs/result_tina_'+str(date_time)+'.pnml'
                print('fillpathPnml::=='+str(fillpathPnml))

                logic = TransformationLogic()
                logic.draw_decision_rawdata(fullPathExcell,fillpathPnml)
                #self.setLabelProcessFinished('Program Process Business Logic Successfully.')            
                self.setLabelProcessFinished(validate.get_message('PROCESS_SUCCESS'))
                self.setTxtbFileOut(fillpathPnml.replace("\\","/"))

                dialog.showinfo('Transform xls to pnml successfully.','Transform xls to pnml successfully.')
                self.appendTxtbConsole('Transform xls to pnml successfully.')

                print('export file successfully.')
                os.system(os.getcwd()+'/tina/bin/nd.exe')
                

    def commandBrowserFile(self):
        file = tkFileDialog.askopenfile(parent=self,mode='rb',title='Choose a file')
        if file != None:
            data = file.read()
            file_name = file.name
            print('file_name.find(\'.xlsx\')::=='+str(file_name.find('.xlsx')))            
            if file_name.find('.xlsx') == -1 or file_name.find('.xls') == -1:
                dialog.showerror('Select File Input Incorrect!','Cannot select file. Must select only xlsx file.')
                self.appendTxtbConsole('choose file fail')
                self.setTxtbChooseVal("")
            else:
                #print "I got %d bytes from this file." % len(data)                        
                self.setTxtbChooseVal(file_name)
                self.appendTxtbConsole('choose file success')
            file.close()
            
def disableWindowClose():
    pass

def setupApplication():
    root = Tk()
    root.title('Transformation Data to Tina tools')
    root.geometry("1200x600")
    root.resizable(width=False, height=False)
    root.protocol("WM_DELETE_WINDOW", disableWindowClose)

    #app = Application(master=root)
    app = TransformationUI()
    app.__init__(master=root)

    app.mainloop()

    root.destroy()
    return app
