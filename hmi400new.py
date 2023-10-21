# -*- coding: utf-8 -*-
"""
Created on Sun May 29 11:52:29 2022
auto-py-to-exe
@author: sasa
"""

import wx
import snap7
from snap7 import util
import time
import threading
import win32api
import datetime
import os
import shutil

#whole window class
class sasaOverlay(wx.Frame):
    def __init__(self):
        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP |
                  wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, title='sasa hmi', style = style,size=(1920, 1080),pos=(0,0))
        self.SetTransparent(255)
        self.Show(True)
        self.SetIcon(wx.Icon('favicon.ico', wx.BITMAP_TYPE_ICO))        
        self.HomeScreen = HomeScreen(self)
        global oldScreen
        oldScreen=self.HomeScreen
        self.HomeScreen.Hide() 
        self.Robot1Screen = RobotScreen(self)
        self.Robot2Screen = RobotScreen(self)
        self.Menu = Menu(self)
        self.Menu.Hide()
        self.Digits = Digits(self)
        self.Digits.Hide()
        self.PasswordPanel = PasswordPanel(self) 
        

#for screenchange        
oldScreen=0       
def showHide(screen,btn):
    f.Menu.homeBtn.SetBackgroundColour(btnColor)
    f.Menu.robot1Btn.SetBackgroundColour(btnColor)
    f.Menu.robot2Btn.SetBackgroundColour(btnColor)
    f.HomeScreen.Hide()
    f.Robot1Screen.Hide()
    f.Robot2Screen.Hide()
    screen.Show()
    btn.SetBackgroundColour(green)
    global oldScreen
    oldScreen=screen                        
    
#sidemenu class    
class Menu(wx.Panel):
    def __init__(self, frame):
        wx.Panel.__init__(self, frame)
        self.SetBackgroundColour(backColor)
                
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add((1920,1080))
        self.SetSizer(main_sizer)
        self.Fit()
        
        self.homeBtn = myBtn(self,label='Домашний экран',pos=(1536-btnSize[0],0),size=(btnSize))        
        self.homeBtn.Bind(wx.EVT_BUTTON, self.homeClick) 
               
        self.robot1Btn = myBtn(self,label='Робот 400',pos=(1536-btnSize[0],btnSize[1]),size=(btnSize))        
        self.robot1Btn.Bind(wx.EVT_BUTTON, self.robot1Click) 
        
        self.robot2Btn = myBtn(self,label='Робот 500',pos=(1536-btnSize[0],btnSize[1]*2),size=(btnSize))        
        self.robot2Btn.Bind(wx.EVT_BUTTON, self.robot2Click) 
        
        self.online = OnlineTextCtrl(self,value='Соединение активно', pos=(1536-btnSize[0],btnSize[1]*4),                                     
                                     size=(btnSize), style=wx.ALIGN_LEFT | wx.BORDER_NONE)  
        self.online.SetBackgroundColour(backColor)
        self.online.SetForegroundColour(wx.Colour(22,222,22))
        
        text=PlainText(self, label='Всего циклов', pos=(1536-btnSize[0],btnSize[1]*5),
                       size=(btnSize),style=wx.ALIGN_CENTER) 
        self.cycleCountAll=PlainText(self, label='0', pos=(1536-btnSize[0],btnSize[1]*6),
                       size=(btnSize),style=wx.ALIGN_CENTER) 
        text=PlainText(self, label='Циклов за смену', pos=(1536-btnSize[0],btnSize[1]*7),
                       size=(btnSize),style=wx.ALIGN_CENTER) 
        self.cycleCount=PlainText(self, label='0', pos=(1536-btnSize[0],btnSize[1]*8),
                       size=(btnSize),style=wx.ALIGN_CENTER)
        
        btn=myBtn(self, label='Сброс смены', pos=(1536-btnSize[0],btnSize[1]*9),
                       size=(btnSize))
        btn.Bind(wx.EVT_BUTTON, self.resetCycleAct)
        self.resetCycle=False
        self.TOCount=PlainText(self, label='До ТО 4 мес', pos=(1536-btnSize[0],btnSize[1]*10),
                       size=(btnSize),style=wx.ALIGN_CENTER)
        self.TOCountBtn=myBtn(self, label='Сброс ТО', pos=(1536-btnSize[0],btnSize[1]*11),
                       size=(btnSize))
        self.TOCountBtn.Bind(wx.EVT_BUTTON, self.resetTOAct) 
        self.TOCountBtn.Disable()
        self.resetTO=False
        
        btn = myBtn(self,label='Показать инструкцию', pos=(1536-btnSize[0],863-btnSize[1]*4),size=(btnSize))        
        btn.Bind(wx.EVT_BUTTON, self.showManual)
        self.archiveBtn = myBtn(self,label='Показать архив', pos=(1536-btnSize[0],863-btnSize[1]*3),size=(btnSize))        
        self.archiveBtn.Bind(wx.EVT_BUTTON, self.showArchive)
        self.archiveBtn.Disable()
        btn = myBtn(self,label='Выход', pos=(1536-btnSize[0],863-btnSize[1]*2),size=(btnSize))        
        btn.Bind(wx.EVT_BUTTON, self.logoutBtn)
        btn = myBtn(self,label='Закрыть', pos=(1536-btnSize[0],863-btnSize[1]),size=(btnSize))        
        btn.Bind(wx.EVT_BUTTON, self.exitBtn)
    
    def homeClick(self, event): showHide(f.HomeScreen,self.homeBtn)
    def robot1Click(self, event): showHide(f.Robot1Screen,self.robot1Btn)
    def robot2Click(self, event): showHide(f.Robot2Screen,self.robot2Btn)
    def resetCycleAct(self, event): self.resetCycle=True
    def resetTOAct(self, event): self.resetTO=True

    def exitBtn(self, event):
        updateFile()
        global looping
        looping=False
        time.sleep(1.7)
        f.Close(force=True)
    def logoutBtn(self, event): 
        global logout
        logout=True
    def showArchive(self, event):
        f.Iconize(True)
        os.startfile("C:/Users/Administrator/Desktop/hmi/archive")
    def showManual(self, event):
        f.Iconize(True)
        os.startfile("C:/Users/Administrator/Desktop/hmi/manual.pdf")
    

#clases for screens     
locksStatus=[]
errorsBlocks=[]
errorList=[]
maxErrors=14
class HomeScreen(wx.Panel):
    def __init__(self, frame):
        wx.Panel.__init__(self, frame)
        self.SetBackgroundColour(backColor)
        self.main=self.main()
        self.locks=self.locks()
        self.errors=self.errors()
        
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add((1230,1080))
        self.SetSizer(main_sizer)
        self.Fit()
        
    def main(self):
        self.autoMode=False
        self.autoModeBtn = myBtn(self,label='Авто режим',pos=(0,0),size=(btnSize))        
        self.autoModeBtn.Bind(wx.EVT_BUTTON, self.autoModeClick) 
        
        self.manualMode=False
        self.manualModeBtn = myBtn(self,label='Ручной режим',pos=(0,btnSize[1]),size=(btnSize))        
        self.manualModeBtn.Bind(wx.EVT_BUTTON, self.manualModeClick)
        
        self.resetMode=False
        self.resetModeBtn = myBtn(self,label='Сброс последовательности',pos=(0,btnSize[1]*2),size=(btnSize))        
        self.resetModeBtn.Bind(wx.EVT_BUTTON, self.resetClick) 
        
        self.removeMode=False
        self.removeModeBtn = myBtn(self,label='Убрать трубу',pos=(0,btnSize[1]*3),size=(btnSize))        
        self.removeModeBtn.Bind(wx.EVT_BUTTON, self.removeClick) 
        
        self.skipMode=False
        self.skipModeBtn = myBtn(self,label='Пропустить трубу',pos=(0,btnSize[1]*4),size=(btnSize))        
        self.skipModeBtn.Bind(wx.EVT_BUTTON, self.skipClick) 
        
        self.pauseMode=False
        self.resumeMode=False
        self.pauseBtn = myBtn(self,label='Пауза',pos=(0,btnSize[1]*5),size=(btnSize))        
        self.pauseBtn.Bind(wx.EVT_BUTTON, self.pauseClick) 
        
        self.gotoOperPos=False
        self.operPosBtn = myBtn(self,label='Поставить роботов удобно',pos=(0,btnSize[1]*7),size=(btnSize))        
        self.operPosBtn.Bind(wx.EVT_BUTTON, self.operPosClic) 
        
        self.reverseSearch=False
        self.reverseSearchBtn = myBtn(self,label='Обратный поиск',pos=(0,btnSize[1]*8),size=(btnSize))
        self.reverseSearchBtn.Bind(wx.EVT_BUTTON, self.toggleReverseSearch) 
  
        
    def autoModeClick(self, event): 
        self.autoMode=True
        self.manualMode=False
    def manualModeClick(self, event): 
        self.manualMode=True
        self.autoMode=False
        
    def resetClick(self, event): self.resetMode=True      
    def removeClick(self, event): self.removeMode=True
    def skipClick(self, event): 
        if self.skipMode==True: self.skipMode=False
        else: self.skipMode=True
        
    def pauseClick(self, event):
        if f.HomeScreen.pauseBtn.GetLabel()=='Пауза': self.pauseMode=True
        elif f.HomeScreen.pauseBtn.GetLabel()=='Возобновить': self.resumeMode=True
    
    def operPosClic(self, event): self.gotoOperPos=True 
    
    def toggleReverseSearch(self, event):
        if self.reverseSearch==True: 
            self.reverseSearch=False
        else: 
            self.reverseSearch=True
     
        
    def locks(self):
        locksStartX=350
        locksStartY=0
        lockBtnSize=(200,60)
         
        self.opened1=False
        self.opened2=False
        self.opened3=False
        self.closed1=False
        self.closed2=False
        self.closed3=False
        
        self.open1 = myBtn(self,label='Закрыть зажим 1',pos=(locksStartX,locksStartY),
                    size=(lockBtnSize))        
        self.open1.Bind(wx.EVT_BUTTON, self.openLock1)         
        self.close1 = myBtn(self,label='Открыть зажим 1',pos=(locksStartX,locksStartY+lockBtnSize[1]),
                    size=(lockBtnSize))        
        self.close1.Bind(wx.EVT_BUTTON, self.closeLock1) 
        
        self.open2 = myBtn(self,label='Закрыть зажим 2',pos=(locksStartX+lockBtnSize[0]+2,locksStartY),
                    size=(lockBtnSize))        
        self.open2.Bind(wx.EVT_BUTTON, self.openLock2)        
        self.close2 = myBtn(self,label='Открыть зажим 2',pos=(locksStartX+lockBtnSize[0]+2,locksStartY+lockBtnSize[1]),
                    size=(lockBtnSize))        
        self.close2.Bind(wx.EVT_BUTTON, self.closeLock2) 
        
        self.open3 = myBtn(self,label='Закрыть зажим 3',pos=(locksStartX+lockBtnSize[0]*2+4,locksStartY),
                    size=(lockBtnSize))        
        self.open3.Bind(wx.EVT_BUTTON, self.openLock3)         
        self.close3 = myBtn(self,label='Открыть зажим 3',pos=(locksStartX+lockBtnSize[0]*2+4,locksStartY+lockBtnSize[1]),
                    size=(lockBtnSize))        
        self.close3.Bind(wx.EVT_BUTTON, self.closeLock3)
        
        for i in range(3):
            text=wx.StaticText(self, label='Закрыто', pos=(locksStartX+(lockBtnSize[0]+2)*i,locksStartY+lockBtnSize[1]*2),
                               size=(lockBtnSize[0],lockBtnSize[1]-25),style=wx.ALIGN_CENTER)
            text.SetBackgroundColour(btnColor) 
            text.SetForegroundColour(btnTextColor) 
            text.SetFont( wx.Font(22, fontFamily, 0, 90, underline = False,
               faceName =""))
            locksStatus.append(text)
            
            
    def openLock1(self, event): self.opened1=True
    def openLock2(self, event): self.opened2=True
    def openLock3(self, event): self.opened3=True
    def closeLock1(self, event): self.closed1=True
    def closeLock2(self, event): self.closed2=True
    def closeLock3(self, event): self.closed3=True        
        
    def errors(self):
        errorsStartX=350
        errorsStartY=250
        self.status=ErrorTextCtrl(self, value='Этап работы', pos=(errorsStartX,errorsStartY-80),
                       size=(621,80),style=wx.ALIGN_LEFT | wx.BORDER_NONE | wx.TE_MULTILINE)   
        self.status.SetBackgroundColour(backColor)
        for i in range(maxErrors):
            text=ErrorTextCtrl(self, value=str(i), pos=(errorsStartX,errorsStartY+40*i),
                           size=(830,28),style=wx.ALIGN_LEFT | wx.BORDER_NONE)   
            text.SetBackgroundColour(red)
            errorsBlocks.append(text)  
            

#class for number input
digitEdit=0       
class Digits(wx.Panel):
    def __init__(self, frame):
        wx.Panel.__init__(self, frame)
        self.SetBackgroundColour(backColor)
        self.digits=self.digits()
        
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add((1920,1080))
        self.SetSizer(main_sizer)
        self.Fit()
        
        
    def digits(self):  
        digitStartX=1236
        digitStartY=200
        n=1
        for i in range(3):
            for j in range(3):
                btn = digitBtn(self,label=str(n),pos=(digitStartX+100*j,digitStartY+100*i),size=(100,100))        
                n=n+1
        btn = digitBtn(self,label='0',pos=(digitStartX,digitStartY+300),size=(100,100))        
        btn = myBtn(self,label='C',pos=(digitStartX+100,digitStartY+300),size=(100,100))        
        btn.Bind(wx.EVT_BUTTON, self.removeDigit)
        btn = myBtn(self,label='X',pos=(digitStartX+200,digitStartY+300),size=(100,100))        
        btn.Bind(wx.EVT_BUTTON, self.exitDigits)
        global digitEdit
        digitEdit=PlainTextCtrl(self, value='0', pos=(digitStartX,digitStartY+400),
                               size=(300,50), style=wx.TE_CENTRE | wx.BORDER_NONE)
        digitEdit.Unbind(wx.EVT_SET_FOCUS)
        btn = myBtn(self,label='OK',pos=(digitStartX,digitStartY+450),size=(300,100))  
        btn.Bind(wx.EVT_BUTTON, self.confirmDigits)
    
    def removeDigit(self, event):
        slicer=len(digitEdit.GetLabel())-1
        if slicer>0:
            digitEdit.SetLabel(digitEdit.GetLabel()[0:slicer])
        else:digitEdit.SetLabel('0')

    def exitDigits(self, event):
        digitEdit.SetLabel('0')
        f.Digits.Hide()
        f.Menu.Show()
    def confirmDigits(self, event):
        currentTextEdit.SetLabel(digitEdit.GetLabel())
        digitEdit.SetLabel('0')
        f.Digits.Hide()
        f.Menu.Show()
        

#clases for screens     
toolOptions=['РПМ ','Длинна ','Диаметр ','Рабочаяя часть ','Тип ','Программа ','Скорость движения ',
             'Глубина работы ','Количество кругов ']           
class RobotScreen(wx.Panel):
    def __init__(self, frame):
        wx.Panel.__init__(self, frame)
        
        self.SetBackgroundColour(backColor)
        self.doorControl=self.doorControl()
        self.toolTable=self.toolTable()
        self.legend=self.legend()
        self.other=self.other()
        
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.Add((1200,1080))
        self.SetSizer(main_sizer)
        self.Fit()
        self.Hide()
        
    def doorControl(self):
        self.robotClosed=False
        self.closeRobot = myBtn(self,label='Закрыть дверь робота',pos=(0,0),size=(btnSize))
        self.closeRobot.Bind(wx.EVT_BUTTON, self.closeDoorRobot) 
        
        self.operOpened=False
        self.openOper = myBtn(self,label='Открыть дверь оператора',pos=(0,btnSize[1]),size=(btnSize))
        self.openOper.Bind(wx.EVT_BUTTON, self.openDoorOper) 
        
        self.operClosed=False
        self.closeOper = myBtn(self,label='Закрыть дверь оператора',pos=(0,btnSize[1]*2),size=(btnSize))
        self.closeOper.Bind(wx.EVT_BUTTON, self.closeDoorOper)  
        
        self.robotOpened=False
        self.openRobot = myBtn(self,label='Открыть дверь робота',pos=(0,btnSize[1]*3),size=(btnSize))
        self.openRobot.Bind(wx.EVT_BUTTON, self.openDoorRobot)  
    
    def closeDoorRobot(self, event): self.robotClosed=True
    def openDoorOper(self, event): self.operOpened=True
    def closeDoorOper(self, event): self.operClosed=True
    def openDoorRobot(self, event): self.robotOpened=True
               
            
    def other(self): 
        self.resetedRobot=False 
        self.resetBtn = myBtn(self,label='Сброс плк робота',pos=(0,btnSize[1]*5),size=(btnSize))
        self.resetBtn.Bind(wx.EVT_BUTTON, self.resetRobotPlc) 
        
        self.resetedSpindle=False
        self.resetSpindleBtn = myBtn(self,label='Сброс ошибок шпинделя',pos=(0,btnSize[1]*6),size=(btnSize)) 
        self.resetSpindleBtn.Bind(wx.EVT_BUTTON, self.resetSpindleError)   
        
        self.openedSpindle=False
        self.startedSpindle=False
        self.spindleStart = myBtn(self,label='Пуск шпинделя',pos=(0,btnSize[1]*7),size=(btnSize))
        self.spindleStart.Bind(wx.EVT_BUTTON, self.startSpindle) 
        
        self.openedSpindle=False
        self.spindleOpen = myBtn(self,label='Открыть шпиндель',pos=(0,btnSize[1]*8),size=(btnSize))
        self.spindleOpen.Bind(wx.EVT_BUTTON, self.openSpindle) 
        
        self.goHomeSignal=False
        self.goHomeBtn = myBtn(self,label='Отъехать домой',pos=(0,btnSize[1]*9),size=(btnSize))
        self.goHomeBtn.Bind(wx.EVT_BUTTON, self.goHomeClick)
        
        self.modeT1=False
        self.changeModeBtn = myBtn(self,label='Включить Т1',pos=(0,btnSize[1]*10),size=(0,0))
        self.changeModeBtn.Bind(wx.EVT_BUTTON, self.ChangeModeClick)
        
        self.workInside=True
        self.workInsideBtn = myBtn(self,label='Обрабатывать внутри',pos=(520,0),size=(btnSize))
        self.workInsideBtn.Bind(wx.EVT_BUTTON, self.toggleWorkInside) 
        self.workInsideBtn.SetBackgroundColour(green)
        
        self.workOutside=True
        self.workOutsideBtn = myBtn(self,label='Обрабатывать снаружи',pos=(520+btnSize[0],0),size=(btnSize))
        self.workOutsideBtn.Bind(wx.EVT_BUTTON, self.toggleWorkOutside) 
        self.workOutsideBtn.SetBackgroundColour(green)
        
        self.calcToolwear=True
        self.calcToolwearBtn = myBtn(self,label='Расчет износа',pos=(520,btnSize[1]),size=(btnSize))
        self.calcToolwearBtn.Bind(wx.EVT_BUTTON, self.toggleCalcToolwear) 
        self.calcToolwearBtn.SetBackgroundColour(green)
    
    def toggleWorkInside(self, event):
        if self.workInside==True: 
            self.workInside=False
            self.workInsideBtn.SetBackgroundColour(btnColor)
        else: 
            self.workInside=True
            self.workInsideBtn.SetBackgroundColour(green)
    def toggleWorkOutside(self, event):
        if self.workOutside==True: 
            self.workOutside=False
            self.workOutsideBtn.SetBackgroundColour(btnColor)
        else: 
            self.workOutside=True
            self.workOutsideBtn.SetBackgroundColour(green)
            
    def toggleCalcToolwear(self, event):
        if self.calcToolwear==True: 
            self.calcToolwear=False
        else: 
            self.calcToolwear=True
        
    def resetRobotPlc(self, event): self.resetedRobot=True         
    def resetSpindleError(self, event): self.resetedSpindle=True
    def openSpindle(self, event):
        if self.openedSpindle==True: 
            self.openedSpindle=False
            self.spindleOpen.SetBackgroundColour(btnColor)
        else: 
            self.openedSpindle=True
            self.spindleOpen.SetBackgroundColour(yellow)
    def startSpindle(self, event):
        global startSpindle1
        if self.startedSpindle==True: 
            self.startedSpindle=False
            self.spindleStart.SetBackgroundColour(btnColor)
        else: 
            self.startedSpindle=True
            self.spindleStart.SetBackgroundColour(yellow)
    def goHomeClick(self, event): self.goHomeSignal=True
    def ChangeModeClick(self, event): 
        if self.modeT1==True: self.modeT1=False
        else: self.modeT1=True

        
    def toolTable(self):
        self.toolToShow=0
        self.toolButtonList=[]
        self.toolNewParams=[]
        self.toolCurrentParams=[]
        self.toolServiced=False
        self.savedTool=False  
        self.toolfailed=False 
        toolStartX=550
        toolsStartY=170
        
        column1W=290
        column2W=150
        rowH=35  
        
        text=PlainText(self, label='Выбор инструмента', pos=(toolStartX+60,toolsStartY-50),
                       size=(310,rowH),style=wx.ALIGN_CENTER)        
        for i in range(10):
            btn = toolBtn(self,label=str(i+1),pos=(toolStartX-45+53*i,toolsStartY),size=(45,45)) 
            self.toolButtonList.append(btn)                       
                    
        
        text=PlainText(self, label='Значения ', pos=(toolStartX-80,toolsStartY+120+(rowH+13)*-1),
                       size=(column1W,rowH),style=wx.ALIGN_RIGHT)        
        text=PlainText(self, label='Текущие', pos=(toolStartX-70+column1W,toolsStartY+120+(rowH+13)*-1),
                       size=(column2W,rowH),style=wx.ALIGN_CENTER)        
        text=PlainText(self, label='Новые', pos=(toolStartX-68+column1W+column2W,toolsStartY+120+(rowH+13)*-1),
                               size=(column2W,rowH), style=wx.ALIGN_CENTER)
        for i in range(9):
            text=PlainText(self, label=toolOptions[i], pos=(toolStartX-80,toolsStartY+120+(rowH+13)*i),
                           size=(column1W,rowH),style=wx.ALIGN_RIGHT)            
            text=PlainText(self, label='0', pos=(toolStartX-70+column1W,toolsStartY+120+(rowH+13)*i),
                           size=(column2W,rowH),style=wx.ALIGN_CENTER)
            text.SetBackgroundColour(pink)
            self.toolCurrentParams.append(text)             
            textEdit=PlainTextCtrl(self, value='0', pos=(toolStartX-68+column1W+column2W,toolsStartY+120+(rowH+13)*i),
                                   size=(column2W,rowH), style=wx.TE_CENTRE | wx.BORDER_NONE, name='1'+str(i))
            self.toolNewParams.append(textEdit)
            
        btn = myBtn(self,label='Инструмент обслужен',pos=(toolStartX-120,750),size=(230,btnSize[1]))
        btn.Bind(wx.EVT_BUTTON, self.toolService)  
        
        self.saveBtn = myBtn(self,label='Сохранить инструмент',pos=(toolStartX+230-120,750),size=(230,btnSize[1]))
        self.saveBtn.Bind(wx.EVT_BUTTON, self.saveTool)   
        
        btn = myBtn(self,label='Сбой инструмента',pos=(toolStartX+230*2-120,750),size=(230,btnSize[1]))
        btn.Bind(wx.EVT_BUTTON, self.toolFault) 

    def toolService(self, event): self.toolServiced=True
    def saveTool(self, event): self.savedTool=True         
    def toolFault(self, event): self.toolfailed=True
    
    def legend(self):
        legendStartX=5
        legendStartY=630
        
        legendTexts=[' Инструмент в роботе (в шкафу пустая)',' В ячейке есть инструмент',
                     ' Ячейка пуста',' В ячейке изношенный инструмент',' Инструмент в роботе изношен'] 
        legendColors=[lightblue,green,yellow,red,pink]
        
        text=PlainText(self, label='Значение цветов', pos=(legendStartX,legendStartY),
                       size=(310,30),style=wx.ALIGN_CENTER)        
        for i in range(5):
            text=PlainText(self, label=legendTexts[i], pos=(legendStartX,legendStartY+40+i*31),
               size=(390,27),style=wx.ALIGN_LEFT) 
            text.SetFont( wx.Font(16, fontFamily, 0, 90, underline = False,
               faceName ="")) 
            text.SetBackgroundColour(legendColors[i])                     
                    

#clases for passwordscreen 
class PasswordPanel(wx.Panel):
    def __init__(self, frame):
        wx.Panel.__init__(self, frame)
        self.SetBackgroundColour(backColor)
        self.buttons()
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add((1920,1080))
        self.SetSizer(main_sizer)
        self.Fit()

    def buttons(self):
        global text
        startX=500
        startY=180
        n=1
        font = wx.Font(80, fontFamily, 0, 90, underline = False,
           faceName ="")
        self.passwordText = wx.TextCtrl(self, value="", pos=(startX,startY+420),
         size=(420,120))
        self.passwordText.SetFont(font)
        font = wx.Font(52, fontFamily, 0, 90, underline = False,
           faceName ="")
       
        for i in range(3):
            for j in range(3):
                btn = passwordBtn(self,label=str(n),pos=(startX+140*j,startY+140*i),size=(140,140))
                btn.SetFont(font)
                
                n=n+1
        btn = passwordBtn(self,label='C',pos=(startX+140*3,startY+140*1),size=(140,140))
        btn.SetFont(font)

#classes for btns texts and inputs
currentTextEdit=0
class PlainTextCtrl(wx.TextCtrl): 
    def __init__(self,*a,**k):  
        wx.TextCtrl.__init__(self,*a,**k)
        self.SetBackgroundColour(btnColor)
        self.SetForegroundColour(btnTextColor)
        self.Bind(wx.EVT_SET_FOCUS, self.spawnDigits) 
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter) 
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.SetFont( wx.Font(22, fontFamily, 0, 90, underline = False,
           faceName =""))
    def spawnDigits(self,event):
        global currentTextEdit
        f.Digits.Show()
        f.Menu.Hide()
        currentTextEdit=self
    def OnEnter(self,event):
        self.SetBackgroundColour(green) 
    def OnLeave(self,event):
        self.SetBackgroundColour(btnColor)
        f.Robot1Screen.spindleStart.SetFocus()

class OnlineTextCtrl(wx.TextCtrl): 
    def __init__(self,*a,**k):  
        wx.TextCtrl.__init__(self,*a,**k)
        self.SetBackgroundColour(btnColor)
        self.SetForegroundColour(btnTextColor)
        self.SetFont( wx.Font(18, fontFamily, 0, 90, underline = False,
           faceName =""))

        
class PlainText(wx.StaticText): 
    def __init__(self,*a,**k):  
        wx.StaticText.__init__(self,*a,**k)
        self.SetBackgroundColour(btnColor)
        self.SetForegroundColour(btnTextColor) 
        self.SetFont( wx.Font(22, fontFamily, 0, 90, underline = False,
           faceName =""))
        
        
class ErrorTextCtrl(wx.TextCtrl): 
    def __init__(self,*a,**k):  
        wx.TextCtrl.__init__(self,*a,**k)
        self.SetBackgroundColour(btnColor)
        self.SetForegroundColour(btnTextColor)
        self.SetFont( wx.Font(18, fontFamily, 0, 90, underline = False,
           faceName =""))
    def onFocus(self,event):
        self.SetBackgroundColour(red)
    def OnEnter(self,event):
        self.SetBackgroundColour(green) 
    def OnLeave(self,event):
        self.SetBackgroundColour(btnColor)
        
        
class myBtn(wx.Button):    
    def __init__(self,*a,**k):        
        wx.Button.__init__(self,*a,**k)
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnEnter) 
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.SetBackgroundColour(btnColor)
        self.SetForegroundColour(btnTextColor)                 
        self.SetFont(wx.Font(14, fontFamily, 0, 90, underline = False,
           faceName =""))
    
    
    def OnEnter(self,event):
        self.SetForegroundColour(wx.Colour(1,1,1)) 
        global reportLen
        global errReport
        errReport=errReport+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+' Нажата кнопка '+self.GetLabel()+';\n'
        reportLen=reportLen+1 
    def OnLeave(self,event):
        self.SetForegroundColour(btnTextColor)
            
class digitBtn(myBtn):
    def __init__(self,*a,**k):        
        myBtn.__init__(self,*a,**k)
        self.Bind(wx.EVT_BUTTON, self.addDigit) 

    def addDigit(self, event):
        if int(digitEdit.GetLabel())==0:
            digitEdit.SetLabel(self.GetLabel())
        else:
            digitEdit.SetLabel(digitEdit.GetLabel()+self.GetLabel())
        
        if int(digitEdit.GetLabel())>30000:
            digitEdit.SetLabel('30000')
        elif int(digitEdit.GetLabel())<0:
            digitEdit.SetLabel('0')
            
word=''   
password='444444' 
mypass='199121'
level=1
class passwordBtn(myBtn):
    def __init__(self,*a,**k):        
        myBtn.__init__(self,*a,**k)
        self.Bind(wx.EVT_BUTTON, self.addDigit) 

    def addDigit(self, event):
        global word
        global level
        word=word+self.GetLabel()
        f.PasswordPanel.passwordText.SetValue(word)
        if word==password:
            f.PasswordPanel.passwordText.SetValue('')
            f.PasswordPanel.Hide()
            oldScreen.Show()
            f.Menu.Show()
            thread2 = threading.Thread(target=idleCatcher)
            thread2.start()  
            level=1
            word=''
        elif word==mypass:
            f.PasswordPanel.passwordText.SetValue('')
            f.PasswordPanel.Hide()
            oldScreen.Show()
            f.Menu.Show()
            thread2 = threading.Thread(target=idleCatcher)
            thread2.start() 
            level=2
            word=''
        elif word=='235876':
            f.PasswordPanel.passwordText.SetValue('')
            f.PasswordPanel.Hide()
            oldScreen.Show()
            f.Menu.Show()
            thread2 = threading.Thread(target=idleCatcher)
            thread2.start() 
            level=3
            word=''
            
        elif len(word)>=6:
            word=''
            f.PasswordPanel.passwordText.SetValue(word)
        elif self.GetLabel()=='C':
            word=''
            f.PasswordPanel.passwordText.SetValue(word)

allowUpdate=False
class toolBtn(myBtn):
    def __init__(self,*a,**k):        
        myBtn.__init__(self,*a,**k)
        self.Bind(wx.EVT_BUTTON, self.pickTool) 
        self.SetFont(wx.Font(23, fontFamily, 0, 90, underline = False,
           faceName =""))

    def pickTool(self,event):
        global allowUpdate
        allowUpdate=True
        oldScreen.toolToShow=int(self.GetLabel())
        
        
#error archive functions
errReport=''  
archiveName='archive/'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+'.dat'
archiveNameBack='C:/sys/backup/'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+'.dat'
def updateFile():
    global errReport
    filereport = open(archiveName, 'a', encoding='utf-8')
    filereport.write(errReport)
    filereport.close()
    filereport = open(archiveNameBack, 'a', encoding='utf-8')
    filereport.write(errReport)
    filereport.close()
    errReport=''

def clearDisk():    
    reportList = os.listdir('C:/Users/Administrator/Desktop/hmi/archive')
    reportListBack = os.listdir('C:/sys/backup/')
    reportsCount=len(reportList)
    deleteReportsCount=100
    if reportsCount>deleteReportsCount: reportsCount=deleteReportsCount
    for i in range(reportsCount):
        adress="C:/Users/Administrator/Desktop/hmi/archive/"+reportList[i]
        if os.path.exists(adress): os.remove(adress)
    reportsCount=len(reportListBack)
    if reportsCount>deleteReportsCount: reportsCount=deleteReportsCount
    for i in range(reportsCount):
        adressBack="C:/sys/backup/"+reportListBack[i]
        if os.path.exists(adressBack): os.remove(adressBack)
    
reportLen=0
def addToReport(errNum,state):
    global reportLen
    global errReport
    errReport=errReport+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+state+'Ошибка номер '+str(errNum)+': '+errList[errNum]+';\n'
    
    reportLen=reportLen+1
    if reportLen>10000: 
        updateFile()
        global archiveName
        global archiveNameBack
        archiveName='archive/'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+'.dat'
        archiveNameBack='C:/sys/backup/'+datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")+'.dat'
        reportLen=0
        total, used, free = shutil.disk_usage("/")
        if free<10000000000: clearDisk()


#siemens interface
lastIstep=0                    
ticks=0
def lifebit():  
    global ticks
    ticks=ticks+1    
    time.sleep(0.2)
   
    mainpageIntoPLC = client.db_read(1001, 0, 16)
    mainpageOutofPLC = client.db_read(1000, 0, 14)
    
    lockingDeviceIntoPLC = client.db_read(1007, 0, 2)
    lockingDeviceOutofPLC = client.db_read(1006, 0, 2)
    
    robot1IntoPLC = client.db_read(1003, 0, 42)
    robot1OutofPLC = client.db_read(1002, 0, 42)
    
    robot2IntoPLC = client.db_read(1005, 0, 42)
    robot2OutofPLC = client.db_read(1004, 0, 42)
    
    errorsOutofPLC = client.db_read(1101, 0, 16)
#istep
    def printIstep(text,color):
        f.HomeScreen.status.SetValue(str(util.get_int(mainpageOutofPLC, 2))+' Этап: '+text)
        f.HomeScreen.status.SetBackgroundColour(color)
        global lastIstep
        if iStep!=lastIstep:
            global errReport            
            errReport=errReport+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+' Этап работы: '+text+';\n'
            lastIstep=iStep
            
    iStep=util.get_int(mainpageOutofPLC, 2) 
    if   iStep==0:printIstep('Ожидание нажатия кнопки старт',yellow)
    elif iStep==1:printIstep('Авто режим выключен',yellow)
    elif iStep==2:printIstep('Труба разжимается, сброс последовательности',yellow)
    elif iStep==100:printIstep('Роботы едут домой 1',green)
    elif iStep==105:printIstep('Роботы едут домой 2',green)
    
    elif iStep==101:printIstep('Робот 400 едет домой 1',green)
    elif iStep==102:printIstep('Робот 400 едет домой 2',green)
    elif iStep==103:printIstep('Робот 500 едет домой 1',green)
    elif iStep==104:printIstep('Робот 500 едет домой 2',green)
    elif iStep==106:printIstep('Роботы едут в удобную для оператора позицию 2',green)
    elif iStep==107:printIstep('Роботы едут в удобную для оператора позицию 2',green)
    
    elif iStep==110:printIstep('Ожидание разрешения от Тестрона',yellow)
    elif iStep==200:printIstep('Ожидание трубы на датчике и разрешения от Тестрона',yellow)
    elif iStep==600:printIstep('Зажим трубы, смена инструмента, поиск трубы 1',green)
    elif iStep==650:printIstep('Зажим трубы, смена инструмента, поиск трубы 2',green)
    elif iStep==655:printIstep('Зажим трубы, смена инструмента, поиск трубы 3',green)
    elif iStep==700:printIstep('Обработка трубы изнутри 1',green)
    elif iStep==705:printIstep('Обработка трубы изнутри 2',green)
    elif iStep==710:printIstep('Смена инструмента, обработка фаски 1',green)
    elif iStep==715:printIstep('Смена инструмента, обработка фаски 2',green)
    elif iStep==800:printIstep('Разжим трубы',yellow)
    elif iStep==801:printIstep('Роботы едут домой 1',green)
    elif iStep==802:printIstep('Роботы едут домой 2',green)
    elif iStep==900:printIstep('Труба готова к отправке с рабочей позиции',yellow)
#errors alarms     
    alarmBit=0
    alarmBite=0
    global errorList  
    errorList=[]
    for i in range(0,127):        
        booler=util.get_bool(errorsOutofPLC, alarmBite, alarmBit)
        if booler==True: 
            newErrList[i]=1
            curError=[i,errListColors[i],errList[i]]
            errorList.append(curError)
        else: newErrList[i]=0
        alarmBit=alarmBit+1
        if alarmBit>7:
            alarmBit=0
            alarmBite=alarmBite+1
        if newErrList[i]>lastErrList[i]:
            addToReport(i,' ПОЯВИЛОСЬ  ')
        elif newErrList[i]<lastErrList[i]:
            addToReport(i,' исчезло    ')
        lastErrList[i]=newErrList[i]    
    
    def printError(i):
        if i<maxErrors:
            #errType=errTypes[errorList[i][1]]
            errorsBlocks[i].SetLabel('Сообщение '+str(errorList[i][0])+'. '+errorList[i][2])
            errorsBlocks[i].SetBackgroundColour(errorList[i][1])
 
    for i in range(len(errorList)):
       printError(i)
    for i in range(len(errorList),maxErrors):
       errorsBlocks[i].SetLabel('')
       errorsBlocks[i].SetBackgroundColour(backColor)
    if ticks>22:
        ticks=0
        updateFile()
    if level==1: f.Menu.archiveBtn.Disable()
    else: f.Menu.archiveBtn.Enable()
#lifebit
    if (util.get_bool(mainpageOutofPLC, 4, 0)==True): 
        util.set_bool(mainpageIntoPLC, 5, 2,False)
        f.Menu.online.SetLabel('Соединение активно')
        global onlineTimerOn
        onlineTimerOn=0
    else: 
        util.set_bool(mainpageIntoPLC, 5, 2,True)
        f.Menu.online.SetLabel('')
        global onlineTimerOff
        onlineTimerOff=0

#cycles
    if f.Menu.resetCycle==True: util.set_bool(mainpageIntoPLC, 5, 7,True) 
    elif f.Menu.resetCycle==False: util.set_bool(mainpageIntoPLC, 5, 7,False)
    
    if f.Menu.resetTO==True: util.set_bool(mainpageIntoPLC, 6, 0,True) 
    elif f.Menu.resetTO==False: util.set_bool(mainpageIntoPLC, 6, 0,False)
    
    if (util.get_bool(mainpageOutofPLC, 4, 7)==True): f.Menu.resetCycle=False
    if (util.get_bool(mainpageOutofPLC, 5, 0)==True): f.Menu.resetTO=False
    
    if level==3: f.Menu.TOCountBtn.Enable()
    else: f.Menu.TOCountBtn.Disable()
    
    f.Menu.cycleCount.SetLabel(str(util.get_int(mainpageOutofPLC, 6)))
    f.Menu.cycleCountAll.SetLabel(str(util.get_int(mainpageOutofPLC, 8)))
    f.Menu.TOCount.SetLabel("До ТО "+str(365-util.get_int(mainpageOutofPLC, 10))+" Дней")
    
#auto\manual           
    if f.HomeScreen.autoMode==True: util.set_bool(mainpageIntoPLC, 4, 4,True) 
    elif f.HomeScreen.autoMode==False: util.set_bool(mainpageIntoPLC, 4, 4,False)
    
    if f.HomeScreen.manualMode==True: util.set_bool(mainpageIntoPLC, 4, 5,True) 
    elif f.HomeScreen.manualMode==False: util.set_bool(mainpageIntoPLC, 4, 5,False)
    
    inAuto=util.get_bool(mainpageOutofPLC, 0, 0)==True
    inManual=util.get_bool(mainpageOutofPLC, 0, 1)==True
    if inAuto:
        f.HomeScreen.autoMode=False
        f.HomeScreen.autoModeBtn.SetBackgroundColour(green)
    else:f.HomeScreen.autoModeBtn.SetBackgroundColour(btnColor)
    
    if inManual:
        f.HomeScreen.manualMode=False
        f.HomeScreen.manualModeBtn.SetBackgroundColour(green)
    else:f.HomeScreen.manualModeBtn.SetBackgroundColour(btnColor)
#resetmode      
    if f.HomeScreen.resetMode==True: util.set_bool(mainpageIntoPLC, 4, 7,True) 
    elif f.HomeScreen.resetMode==False: util.set_bool(mainpageIntoPLC, 4, 7,False)
    
    if (util.get_bool(mainpageOutofPLC, 4, 1)==True): f.HomeScreen.resetMode=False
    if inAuto and util.get_bool(mainpageOutofPLC, 4, 4)==True: f.HomeScreen.resetModeBtn.Enable()
    else: f.HomeScreen.resetModeBtn.Disable()
#removemode    
    if f.HomeScreen.removeMode==True: util.set_bool(mainpageIntoPLC, 5, 1,True) 
    elif f.HomeScreen.removeMode==False: util.set_bool(mainpageIntoPLC, 5, 1,False)
    
    if (util.get_bool(mainpageOutofPLC, 4, 2)==True): f.HomeScreen.removeMode=False
    if inAuto and util.get_bool(mainpageOutofPLC, 4, 4)==True: f.HomeScreen.removeModeBtn.Enable()
    else: f.HomeScreen.removeModeBtn.Disable()
#skipmode     
    if f.HomeScreen.skipMode==True: util.set_bool(mainpageIntoPLC, 5, 3,True) 
    elif f.HomeScreen.skipMode==False: util.set_bool(mainpageIntoPLC, 5, 3,False)
    
    if util.get_bool(mainpageOutofPLC, 4, 3)==False and f.HomeScreen.skipMode==True:        
        f.HomeScreen.skipModeBtn.SetBackgroundColour(green)
    else:f.HomeScreen.skipModeBtn.SetBackgroundColour(btnColor) 
    if util.get_bool(mainpageOutofPLC, 4, 3)==True: f.HomeScreen.skipMode=False
    if inAuto: f.HomeScreen.skipModeBtn.Enable()
    else: f.HomeScreen.skipModeBtn.Disable()
#pause\resume
    if f.HomeScreen.pauseMode==True: util.set_bool(mainpageIntoPLC, 5, 4,True) 
    elif f.HomeScreen.pauseMode==False: util.set_bool(mainpageIntoPLC, 5, 4,False)
    
    if f.HomeScreen.resumeMode==True: util.set_bool(mainpageIntoPLC, 5, 5,True) 
    elif f.HomeScreen.resumeMode==False: util.set_bool(mainpageIntoPLC, 5, 5,False)
    
    if (util.get_bool(mainpageOutofPLC, 4, 4)==True): 
        f.HomeScreen.pauseMode=False
        f.HomeScreen.pauseBtn.SetLabel('Возобновить')
    elif (util.get_bool(mainpageOutofPLC, 4, 5)==True): 
        f.HomeScreen.resumeMode=False
        f.HomeScreen.pauseBtn.SetLabel('Пауза') 
#robots to oper position
    if f.HomeScreen.gotoOperPos==True: util.set_bool(mainpageIntoPLC, 5, 6,True) 
    elif f.HomeScreen.gotoOperPos==False: util.set_bool(mainpageIntoPLC, 5, 6,False)
    
    if (util.get_bool(mainpageOutofPLC, 4, 6)==True): f.HomeScreen.gotoOperPos=False
    if (util.get_bool(mainpageOutofPLC, 4, 4)==True) and inAuto:
        f.HomeScreen.operPosBtn.Enable()
    else: f.HomeScreen.operPosBtn.Disable()
    
#reverse search
    if f.HomeScreen.reverseSearch==True: util.set_bool(mainpageIntoPLC, 4, 2,True) 
    elif f.HomeScreen.reverseSearch==False: util.set_bool(mainpageIntoPLC, 4, 2,False)
    
    if (util.get_bool(mainpageOutofPLC, 0, 4)==True): 
        f.HomeScreen.reverseSearchBtn.SetBackgroundColour(green)
    else: f.HomeScreen.reverseSearchBtn.SetBackgroundColour(btnColor)
    
    if level==2: f.HomeScreen.reverseSearchBtn.Enable()
    else: f.HomeScreen.reverseSearchBtn.Disable()
    
#locks    
    if f.HomeScreen.opened1==True: util.set_bool(lockingDeviceIntoPLC, 0, 1,True) 
    elif f.HomeScreen.opened1==False: util.set_bool(lockingDeviceIntoPLC, 0, 1,False)
    
    if f.HomeScreen.opened2==True: util.set_bool(lockingDeviceIntoPLC, 0, 3,True) 
    elif f.HomeScreen.opened2==False: util.set_bool(lockingDeviceIntoPLC, 0, 3,False)
    
    if f.HomeScreen.opened3==True: util.set_bool(lockingDeviceIntoPLC, 0, 5,True) 
    elif f.HomeScreen.opened3==False: util.set_bool(lockingDeviceIntoPLC, 0, 5,False)
    
    if f.HomeScreen.closed1==True: util.set_bool(lockingDeviceIntoPLC, 0, 2,True) 
    elif f.HomeScreen.closed1==False: util.set_bool(lockingDeviceIntoPLC, 0, 2,False)
    
    if f.HomeScreen.closed2==True: util.set_bool(lockingDeviceIntoPLC, 0, 4,True) 
    elif f.HomeScreen.closed2==False: util.set_bool(lockingDeviceIntoPLC, 0, 4,False)
    
    if f.HomeScreen.closed3==True: util.set_bool(lockingDeviceIntoPLC, 0, 6,True) 
    elif f.HomeScreen.closed3==False: util.set_bool(lockingDeviceIntoPLC, 0, 6,False)
    
    if (util.get_bool(lockingDeviceOutofPLC, 0, 6)==True): f.HomeScreen.opened1=False
    if (util.get_bool(lockingDeviceOutofPLC, 1, 0)==True): f.HomeScreen.opened2=False
    if (util.get_bool(lockingDeviceOutofPLC, 1, 2)==True): f.HomeScreen.opened3=False
    if (util.get_bool(lockingDeviceOutofPLC, 0, 7)==True): f.HomeScreen.closed1=False
    if (util.get_bool(lockingDeviceOutofPLC, 1, 1)==True): f.HomeScreen.closed2=False
    if (util.get_bool(lockingDeviceOutofPLC, 1, 3)==True): f.HomeScreen.closed3=False
    
    if not inAuto or level==1:
        locksStatus[0].SetLabel('Работает')
        f.HomeScreen.open1.Disable()
        f.HomeScreen.close1.Disable()
        locksStatus[1].SetLabel('Только')
        f.HomeScreen.open2.Disable()
        f.HomeScreen.close2.Disable()
        locksStatus[2].SetLabel('В авто')
        f.HomeScreen.open3.Disable()
        f.HomeScreen.close3.Disable()
        
    elif level==2 and inAuto:    
        if (util.get_bool(lockingDeviceOutofPLC, 0, 0)==True):
            locksStatus[0].SetLabel('Закрыт')
            f.HomeScreen.open1.Disable()
            f.HomeScreen.close1.Enable()
        elif (util.get_bool(lockingDeviceOutofPLC, 0, 1)==True):
            locksStatus[0].SetLabel('Открыт')
            f.HomeScreen.close1.Disable()
            f.HomeScreen.open1.Enable()
        else: 
            locksStatus[0].SetLabel('Промежуточно')
            f.HomeScreen.open1.Disable()
            f.HomeScreen.close1.Disable()
        
        if (util.get_bool(lockingDeviceOutofPLC, 0, 2)==True):
            locksStatus[1].SetLabel('Закрыт')
            f.HomeScreen.open2.Disable()
            f.HomeScreen.close2.Enable()
        elif (util.get_bool(lockingDeviceOutofPLC, 0, 3)==True):
            locksStatus[1].SetLabel('Открыт')
            f.HomeScreen.close2.Disable()
            f.HomeScreen.open2.Enable()
        else: 
            locksStatus[1].SetLabel('Промежуточно')
            f.HomeScreen.open2.Disable()
            f.HomeScreen.close2.Disable()
        
        if (util.get_bool(lockingDeviceOutofPLC, 0, 4)==True):
            locksStatus[2].SetLabel('Закрыт')
            f.HomeScreen.open3.Disable()
            f.HomeScreen.close3.Enable()
        elif (util.get_bool(lockingDeviceOutofPLC, 0, 5)==True):
            locksStatus[2].SetLabel('Открыт')
            f.HomeScreen.close3.Disable()
            f.HomeScreen.open3.Enable()
        else: 
            locksStatus[2].SetLabel('Промежуточно')
            f.HomeScreen.open3.Disable()
            f.HomeScreen.close3.Disable()
        
  
    def robotdata(robot,database,databaseOut):
#doors
        if robot.robotOpened==True: util.set_bool(database, 20, 7,True) 
        elif robot.robotOpened==False: util.set_bool(database, 20, 7,False)
        
        if robot.operOpened==True: util.set_bool(database, 20, 6,True) 
        elif robot.operOpened==False: util.set_bool(database, 20, 6,False)
        
        if robot.robotClosed==True: util.set_bool(database, 21, 1,True) 
        elif robot.robotClosed==False: util.set_bool(database, 21, 1,False)
        
        if robot.operClosed==True: util.set_bool(database, 21, 0,True) 
        elif robot.operClosed==False: util.set_bool(database, 21, 0,False)
        
        if not inManual:
            robot.openOper.Disable()
            robot.closeOper.Disable()
            robot.openRobot.Disable()
            robot.closeRobot.Disable()  
        else:
            if (util.get_bool(databaseOut, 16, 2)==True): #operopened
                robot.openOper.Disable()
                robot.closeOper.Enable()
                robot.operOpened=False
            if (util.get_bool(databaseOut, 16, 3)==True): #robotopened
                robot.openRobot.Disable()
                robot.closeRobot.Enable()
                robot.robotOpened=False
            
            if (util.get_bool(databaseOut, 16, 5)==True) and (util.get_bool(databaseOut, 16, 4)==True): #bothClosed
                robot.openOper.Enable()
                robot.closeOper.Disable()
                robot.operClosed=False
                robot.openRobot.Enable()
                robot.closeRobot.Disable()
                robot.robotClosed=False  
            else:
                robot.openOper.Disable()
                robot.openRobot.Disable()
                
#reset robo        
        if robot.resetedRobot==True: util.set_bool(database, 20, 0,True) 
        elif robot.resetedRobot==False: util.set_bool(database, 20, 0,False)
        
        if (util.get_bool(databaseOut, 19, 2)==True): robot.resetedRobot=False
        if (util.get_bool(mainpageOutofPLC, 4, 4)==True):
            robot.resetBtn.Enable()
        else: robot.resetBtn.Disable()
#reset spindle        
        if robot.resetedSpindle==True: util.set_bool(database, 20, 1,True) 
        elif robot.resetedSpindle==False: util.set_bool(database, 20, 1,False)
        
        if (util.get_bool(databaseOut, 16, 0)==False): 
            robot.resetedSpindle=False
            robot.resetSpindleBtn.SetBackgroundColour(btnColor)
        else: robot.resetSpindleBtn.SetBackgroundColour(red)
#tool service         
        if robot.toolServiced==True: util.set_bool(database, 20, 3,True) 
        elif robot.toolServiced==False: util.set_bool(database, 20, 3,False)
        
        if (util.get_bool(databaseOut, 19, 5)==True): robot.toolServiced=False
#tool save         
        if robot.savedTool==True: util.set_bool(database, 21, 2,True) 
        elif robot.savedTool==False: util.set_bool(database, 21, 2,False)
        
        if (util.get_bool(databaseOut, 19, 3)==True): robot.savedTool=False
        
        if level==2: robot.saveBtn.Enable()
        else: robot.saveBtn.Disable()
#tool fail         
        if robot.toolfailed==True: util.set_bool(database, 21, 3,True) 
        elif robot.toolfailed==False: util.set_bool(database, 21, 3,False)
        
        if (util.get_bool(databaseOut, 19, 4)==True): robot.toolfailed=False
#open spindle          
        if robot.openedSpindle==True: util.set_bool(database, 20, 5,True) 
        elif robot.openedSpindle==False: util.set_bool(database, 20, 5,False)
        
        if util.get_bool(databaseOut, 16, 1):            
            robot.spindleOpen.SetBackgroundColour(green)
            
        elif robot.openedSpindle==True and not util.get_bool(databaseOut, 16, 1):             
            robot.spindleOpen.SetBackgroundColour(yellow)
            
        else:robot.spindleOpen.SetBackgroundColour(btnColor)
        if inManual and level==2: robot.spindleOpen.Enable()
        else: robot.spindleOpen.Disable()
            
#srart spindle          
        if robot.startedSpindle==True: util.set_bool(database, 20, 2,True) 
        elif robot.startedSpindle==False: util.set_bool(database, 20, 2,False)
        
        if util.get_bool(databaseOut, 24, 2):            
            robot.spindleStart.SetBackgroundColour(green)
            
        elif robot.startedSpindle==True and not util.get_bool(databaseOut, 24, 2):             
            robot.spindleStart.SetBackgroundColour(yellow)
            
        else:robot.spindleStart.SetBackgroundColour(btnColor)  
        if inManual: robot.spindleStart.Enable()
        else: robot.spindleStart.Disable()
#gohome        
        if robot.goHomeSignal==True: util.set_bool(database, 24, 0,True) 
        elif robot.goHomeSignal==False: util.set_bool(database, 24, 0,False)

        if (util.get_bool(databaseOut, 24, 0)==True): robot.goHomeSignal=False
        if (util.get_bool(mainpageOutofPLC, 4, 4)==True) and inAuto:
            robot.goHomeBtn.Enable()
        else: robot.goHomeBtn.Disable()
#t1\ext
        if robot.modeT1==True: util.set_bool(database, 24, 1,True) 
        elif robot.modeT1==False: util.set_bool(database, 24, 1,False)
        
        if (util.get_bool(databaseOut, 24, 1)==True): 
            robot.changeModeBtn.SetLabel('Включить EXT')
        elif (util.get_bool(databaseOut, 24, 1)==False): 
            robot.changeModeBtn.SetLabel('Включить T1')
#workModes
        if robot.workInside==True: util.set_bool(database, 24, 2,True) 
        elif robot.workInside==False: util.set_bool(database, 24, 2,False)
        if robot.workOutside==True: util.set_bool(database, 24, 3,True) 
        elif robot.workOutside==False: util.set_bool(database, 24, 3,False)
#calc toolwear
        if robot.calcToolwear==True: util.set_bool(database, 24, 4,True) 
        elif robot.calcToolwear==False: util.set_bool(database, 24, 4,False)
        
        if (util.get_bool(databaseOut, 24, 4)==True): 
            robot.calcToolwearBtn.SetBackgroundColour(green)
        else: robot.calcToolwearBtn.SetBackgroundColour(btnColor)
        
        if level==2: robot.calcToolwearBtn.Enable()
        else: robot.calcToolwearBtn.Disable()
#robot tooltoshow          
        if robot.toolToShow>10 or robot.toolToShow<1:
            util.set_int(database, 18, 0) 
        else: util.set_int(database, 18, robot.toolToShow)
        
        bit1=6
        bite1=16
        bit2=0
        bite2=18
        toolInRobo=util.get_int(databaseOut, 22)-1
        for i in range(10):  
            if (util.get_bool(databaseOut, bite1, bit1)==True):
                robot.toolButtonList[i].SetBackgroundColour(green)
                if (util.get_bool(databaseOut, bite2, bit2)==True):
                    robot.toolButtonList[i].SetBackgroundColour(red)
                    
            else: robot.toolButtonList[i].SetBackgroundColour(yellow)
            
            if i==toolInRobo:
                robot.toolButtonList[i].SetBackgroundColour(lightblue)
                if (util.get_bool(databaseOut, bite2, bit2)==True):
                    robot.toolButtonList[i].SetBackgroundColour(pink)
                    
            if robot.toolToShow>0 and robot.toolToShow<=10:
                if robot.toolToShow-1==i:
                    robot.toolButtonList[i].SetSize(45,60)
                else: robot.toolButtonList[i].SetSize(45,45)
            
            bit1=bit1+1
            if bit1>7:
                bite1=bite1+1
                bit1=0
                
            bit2=bit2+1
            if bit2>7:
                bite2=bite2+1
                bit2=0 
             
#toolparams         
        util.set_int(database, 16, int(robot.toolNewParams[0].GetLabel()))#rpm
        util.set_int(database, 2, int(robot.toolNewParams[1].GetLabel()))#length
        util.set_int(database, 0, int(robot.toolNewParams[2].GetLabel()))#diam
        util.set_int(database, 14, int(robot.toolNewParams[3].GetLabel()))#workdepth
        util.set_int(database, 4, int(robot.toolNewParams[4].GetLabel()))#type
        util.set_int(database, 6, int(robot.toolNewParams[5].GetLabel()))#forceset
        util.set_int(database, 10, int(robot.toolNewParams[6].GetLabel()))#speed
        util.set_int(database, 22, int(robot.toolNewParams[7].GetLabel()))#maxdepth
        util.set_int(database, 8, int(robot.toolNewParams[8].GetLabel()))#forcecontact
        
        robot.toolCurrentParams[0].SetLabel(str(util.get_int(databaseOut, 0)))#rpm
        robot.toolCurrentParams[1].SetLabel(str(util.get_int(databaseOut, 4)))#length
        robot.toolCurrentParams[2].SetLabel(str(util.get_int(databaseOut, 2)))#diam
        robot.toolCurrentParams[3].SetLabel(str(util.get_int(databaseOut, 14)))#workdepth
        robot.toolCurrentParams[4].SetLabel(str(util.get_int(databaseOut, 6)))#type
        robot.toolCurrentParams[5].SetLabel(str(util.get_int(databaseOut, 8)))#forceset
        robot.toolCurrentParams[6].SetLabel(str(util.get_int(databaseOut, 12)))#speed
        robot.toolCurrentParams[7].SetLabel(str(util.get_int(databaseOut, 20)))#maxdepth        
        robot.toolCurrentParams[8].SetLabel(str(util.get_int(databaseOut, 10)))#forcecontact
        
        if allowUpdate==True:            
            robot.toolNewParams[0].SetLabel(str(util.get_int(databaseOut, 0)))
            robot.toolNewParams[1].SetLabel(str(util.get_int(databaseOut, 4)))
            robot.toolNewParams[2].SetLabel(str(util.get_int(databaseOut, 2)))
            robot.toolNewParams[3].SetLabel(str(util.get_int(databaseOut, 14)))
            robot.toolNewParams[4].SetLabel(str(util.get_int(databaseOut, 6)))
            robot.toolNewParams[5].SetLabel(str(util.get_int(databaseOut, 8)))
            robot.toolNewParams[6].SetLabel(str(util.get_int(databaseOut, 12)))
            robot.toolNewParams[7].SetLabel(str(util.get_int(databaseOut, 20)))        
            robot.toolNewParams[8].SetLabel(str(util.get_int(databaseOut, 10)))
    
    global allowUpdate
    robotdata(f.Robot1Screen,robot1IntoPLC,robot1OutofPLC)
    robotdata(f.Robot2Screen,robot2IntoPLC,robot2OutofPLC)
    allowUpdate=False
    
    client.db_write(1001, 0, mainpageIntoPLC)
    client.db_write(1007, 0, lockingDeviceIntoPLC)
    client.db_write(1003, 0, robot1IntoPLC)
    client.db_write(1005, 0, robot2IntoPLC)


looping=True
def connection():
    client.connect('192.168.100.40',0,1)
    time.sleep(1) 
    while looping: lifebit()
    
onlineTimerOn=0
onlineTimerOff=0
def timers():
    global onlineTimerOn 
    global onlineTimerOff 
    while looping:
        time.sleep(1) 
        onlineTimerOn=onlineTimerOn+1
        onlineTimerOff=onlineTimerOff+1
        if onlineTimerOff>4 or onlineTimerOn>4:
            f.Menu.online.SetLabel('Разрыв связи')
            f.Menu.online.SetBackgroundColour(red)
        else: f.Menu.online.SetBackgroundColour(backColor)

logout=False
def idleCatcher():
    global logout
    lastInput=win32api.GetLastInputInfo()
    idleSeconds=0
    while idleSeconds<120 and logout==False:
       if lastInput==win32api.GetLastInputInfo():
           time.sleep(1) 
           idleSeconds=idleSeconds+1
       elif looping==False: break
       else:
           time.sleep(1) 
           idleSeconds=0
           lastInput=win32api.GetLastInputInfo()
    if looping:
        logout=False
        f.Menu.Hide()
        oldScreen.Hide()
        f.Digits.Hide()
        time.sleep(0.5)
        f.PasswordPanel.Show()
    
def openPassword(): 
    global password
    file=open('password.dat')
    for n,fileString in enumerate(file):
        password=fileString

def openErrors(): 
    for i in range(0,127): 
        errList.append('')
        lastErrList.append(0)
        newErrList.append(0)
        errListColors.append(red)
        
    file=open('400errors.dat', encoding='utf-8')
    for n,fileString in enumerate(file):
        pairs=fileString.rstrip('\n').split(':')
        errList[int(pairs[0])]=pairs[1]
        errListColors[int(pairs[0])]=colorList[int(pairs[2])]
        

#colors sizes fonts arrays init
btnSize=(250,50)
backColor=wx.Colour(1,15,40)
btnColor=wx.Colour(1,30,80)
btnTextColor=wx.Colour(211,211,211)

green=wx.Colour(11,151,11)
red=wx.Colour(131,11,11)
yellow=wx.Colour(141,91,31)
blue=wx.Colour(11,11,131)
lightblue=wx.Colour(11,111,111)
pink=wx.Colour(141,10,95)
colorList=[red,red,yellow,green]
errTypes=['Ошибка ','Сообщение ','Сообщение ']
fontFamily=wx.SWISS


lastErrList=[]
newErrList=[]
errList=[] 
errListColors=[] 
 
#open files
openErrors()
openPassword()

#start all threads and interface loop
f=0
client = snap7.client.Client()    
thread1 = threading.Thread(target=connection)
thread2 = threading.Thread(target=timers)

thread1.start()
thread2.start()
    
app = wx.App()
f = sasaOverlay()
app.MainLoop()

