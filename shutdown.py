from sys import exit
from tkinter import Tk,StringVar,Canvas,Label,Button
from os import system
import platform

class shutdown:

    def __init__(self) -> None:
        self.root= Tk()
        self.root.title("Apagado PC")
        self.root.geometry('380x230+500+150')
        self.text = StringVar()
        self.text.set("      Se apagará en     ")
        
        self.canvas()
        self.label()
        self.button_time()
        self.accept_button()
        self.cancel_button()

        self.countdown(20)

        self.root.mainloop()
    
    def canvas(self):
        self.canvas1 = Canvas(self.root, width = 380, height = 230, bg = 'lightsteelblue2', relief = 'raised')
        self.canvas1.pack()

    def label(self):
        self.label1 = Label(self.root, text='El computador se apagará en:', bg = 'lightsteelblue2')
        self.label1.config(font=('helvetica', 20))
        self.canvas1.create_window(180, 60, window=self.label1)

    def button_time(self):
        self.label2 = Label(self.root, textvariable=self.text, bg='lightsteelblue2')
        self.label2.config(font=('helvetica', 20))
        self.canvas1.create_window(180, 100, window=self.label2)

    def update_button(self,val,t):
        self.text.set(f"      {val}     ")
        self.root.after(1000, lambda:self.countdown(t-1))

    def countdown(self,t):
        if t+1:
            _, secs = divmod(t, 60)
            timeformat = "{:02d}".format(secs)
            self.update_button(timeformat, t)
        else:
            self.update_button("Bye :)", 0)

    def accept_button(self):
        self.button = Button(text="      Aceptar     ", command=shutdown_pc, bg='green', fg='white', font=('helvetica', 12, 'bold'))
        self.canvas1.create_window(180, 140, window=self.button)

    def cancel_button(self):
        self.exitButton = Button(self.root, text='       Cancelar     ',command=no_shutdown_pc, bg='brown', fg='white', font=('helvetica', 12, 'bold'))
        self.canvas1.create_window(180, 180, window=self.exitButton)


def shutdown_pc ():
    sistema = platform.system()
    if sistema == "Windows":
        system("""shutdown /s /t 10 /c "Trate de cerrar todo, tiene 10 segundos" """)
        exit()
    else:
        system("""shutdown -P +1 "Trate de cerrar todo, tiene 60 segundos" """)
        exit()

def no_shutdown_pc ():
    exit()
    
shutdown()