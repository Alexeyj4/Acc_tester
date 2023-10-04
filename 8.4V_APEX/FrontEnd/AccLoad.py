title="Тестер АКБ АПЕКС v1.0"

slot_label_font="Arial" #шрифт номера ячейки
slot_label_font_size=36 #и размер его
meas_label_font="Arial" #шрифт показаний
meas_label_font_size=20 #и размер его
log_window_height=20 #высота окна журнала (когда без графиков)
log_window_width=15 #ширина окна журнала (когда без графиков)
log_window_height_c=20 #высота окна журнала (когда с графиками)
log_window_width_c=15 #ширина окна журнала (когда с графиками)


meas_threshold=0.08 #порог для фильтрации помех
cnvs_width=150 #размер полотна для рисования графиков
cnvs_heigth=55 #размер полотна для рисования графиков

from tkinter import *
from tkinter import scrolledtext
from tkinter import messagebox
from tkinter import Canvas
import serial
from functools import partial
import time
import configparser

config = configparser.ConfigParser()  # создаём объекта парсера
try:
    config.read("settings.ini")  # читаем конфиг
    num_of_slots=int(config['settings']['num_of_slots'])
    port=config["settings"]["port"]
    amper_hour_min_norma=float(config["settings"]["amper_hour_min_norma"])
    amper_hour_max_norma=float(config["settings"]["amper_hour_max_norma"])
    Umin_norma=float(config["settings"]["Umin_norma"])
    Umax_norma=float(config["settings"]["Umax_norma"])
    Imin_norma=float(config["settings"]["Imin_norma"])
    Imax_norma=float(config["settings"]["Imax_norma"])
    draw_charts=int(config["settings"]["draw_charts"])
    charts_scale=int(config["settings"]["charts_scale"])
    
except:
    messagebox.showerror("Ошибка","Ошибка в ini-файле")
    

window = Tk()
window.title(title)

window.title(title+" - "+port)

frm=[]
lbl_name=[]
lbl_u=[]
lbl_i=[]
stx=[]
lbl_status=[]
btn=[]
cnvs=[]

umin=[]
umax=[]
imin=[]
imax=[]

slot_status=[]
slot_start_time=[]

cnvs_current_y=[] #current y (time) coordinates for each slot

interval_trigger=[] #interval trigger to fix 10 minutes interval to print measure in log screen
for n in range(0,num_of_slots):
    interval_trigger.append(0)
    cnvs_current_y.append(0)

def reset_slot(slot_num):
    umin[slot_num]=127
    umax[slot_num]=0
    imin[slot_num]=127
    imax[slot_num]=0
    slot_status[slot_num]='standby'
    lbl_status[slot_num].config(text="Ожидание",background='white')

def reset_cnvs(slot_num):
    cnvs_current_y[slot_num]=0
    cnvs[slot_num].delete('all')
    cnvs[slot_num].create_rectangle(2,2,cnvs_width,cnvs_heigth)

def reset_press(slot_num):
    stx[slot_num].delete('1.0', END)
    reset_slot(slot_num)
    if draw_charts==1:
        reset_cnvs(slot_num)
    pass

def readser(): #read string from serial and delete escape symbols
    received_string=ser.readline()
    
    if received_string=='':
        return ''
    res_string=''
    i=0
    
    while(received_string[i]!=13 and received_string[i]!=10):    #!= \r \n
        res_string=res_string+chr(received_string[i])
        i=i+1
    return res_string

try:
    ser = serial.Serial(port,9600)
except:
    messagebox.showerror("Ошибка!","Не удалось открыть COM-порт "+port)

for i in range(0,num_of_slots):

    umin.append(127)
    umax.append(0)
    imin.append(127)
    imax.append(0)
    slot_start_time.append(time.time());

    slot_status.append('standby'); #standby/discharge/complete
    
    
    frm.append(Frame(window))

    lbl_name.append(Label(frm[i],text=str(i+1),font=(slot_label_font,slot_label_font_size)))
    lbl_name[i].pack()

    lbl_u.append(Label(frm[i],text="U=",font=(meas_label_font,meas_label_font_size)))
    lbl_u[i].pack()

    lbl_i.append(Label(frm[i],text="I=",font=(meas_label_font,meas_label_font_size)))
    lbl_i[i].pack()

    if draw_charts==1:
        cnvs.append(Canvas(frm[i],width=cnvs_width,height=cnvs_heigth))
        cnvs[i].pack()
    if draw_charts==1:
        stx.append(scrolledtext.ScrolledText(frm[i],width = log_window_width_c,height = log_window_height_c))
    else:
        stx.append(scrolledtext.ScrolledText(frm[i],width = log_window_width,height=log_window_height))
    stx[i].pack()

    lbl_status.append(Label(frm[i],text="Не работает",font='bold'))
    lbl_status[i].pack()

    btn.append(Button(frm[i],text="Сброс",command=partial(reset_press, i))) 
    btn[i].pack()
    
    frm[i].pack(side=LEFT)
  

def loop1():
    if ser.inWaiting()==0:
        window.title(title+" - "+port+" - Ожидание")
    else:
        window.title(title+" - "+port+" - Измерение")
        while ser.inWaiting()>0:
            received=readser()
            
            if received=='slot':            
                slot_c=readser()
                
                if len(slot_c)==1 and slot_c!='' and int(slot_c)>=0 and int(slot_c)<num_of_slots:
                    slot_i=int(slot_c)
                    try:
                        u=float(readser())
                        i=float(readser())
                        skip=0
                    except: #error in received data
                        stx[slot_i].insert(INSERT,'......\n')
                        skip=1
                        

                    if skip==0:
                        lbl_u[slot_i]['text']='U='+str(u)       #real-time output U and I
                        lbl_i[slot_i]['text']='I='+str(i)
                        if draw_charts==1:            #отрисовка графиков (когда включены. Задаётся в настройках)
                            if int(cnvs_current_y[slot_i])!=(int(cnvs_current_y[slot_i]+1/charts_scale)): #пропуск шагов для отрисовки (иначе перегружается система и не хватит места в окне). Коэффициент задаётся в настройках
                                cnvs[slot_i].create_line(int(cnvs_current_y[slot_i]), 50 , int(cnvs_current_y[slot_i]), 50-u*5)
                            cnvs_current_y[slot_i]+=1/charts_scale
    
                        if u>meas_threshold or i>meas_threshold:        #есть ток или напряжение

                            if slot_status[slot_i]=='standby':
                                slot_start_time[slot_i]=time.time()
                                stx[slot_i].insert(INSERT,'Начало разряда:\n')
                                minutes=str(time.localtime(time.time()).tm_min)
                                if draw_charts==1:
                                    reset_cnvs(slot_i)
                                
                                if len(minutes)==1: minutes='0'+minutes
                                stx[slot_i].insert(INSERT,str(time.localtime(time.time()).tm_hour)+':'+minutes+'\n')
                                lbl_status[slot_i].config(text="Разряд",background='yellow')
                                slot_status[slot_i]='discharge'
                                
                            
                            if slot_status[slot_i]=='discharge':

                                minutes=str(time.localtime(time.time()).tm_min)
                                if len(minutes)==1: minutes='0'+minutes                                
                                if minutes[1]=='0' and interval_trigger[slot_i]==0:                                         #check 10 min interval for print in log screen
                                    stx[slot_i].insert(INSERT,str(u)+'В/'+str(i)+'А '+str(time.localtime(time.time()).tm_hour)+':'+minutes+'\n')                                    
                                    interval_trigger[slot_i]=1
                                if minutes[1]!='0': interval_trigger[slot_i]=0 
                                
                                if u<umin[slot_i]:
                                    umin[slot_i]=u
                                if u>umax[slot_i]:
                                    umax[slot_i]=u                                
                                if i<imin[slot_i]:
                                    imin[slot_i]=i
                                if i>imax[slot_i]:
                                    imax[slot_i]=i                                
                        else:                                       #нет тока или напряжения                      

                            if slot_status[slot_i]=='discharge':
                                stx[slot_i].insert(INSERT,'Конец разряда:\n')                                
                                minutes=str(time.localtime(time.time()).tm_min)                                
                                if len(minutes)==1: minutes='0'+minutes
                                stx[slot_i].insert(INSERT, str(time.localtime(time.time()).tm_hour)+':'+minutes+'\n')
                                
                                stx[slot_i].insert(INSERT,"Umin="+str(umin[slot_i])+'\n')
                                stx[slot_i].insert(INSERT,"Umax="+str(umax[slot_i])+'\n')
                                stx[slot_i].insert(INSERT,"Imin="+str(imin[slot_i])+'\n')
                                stx[slot_i].insert(INSERT,"Imax="+str(imax[slot_i])+'\n')
                                stx[slot_i].insert(INSERT,'Время разряда:\n')
                                t_dsch_sec=time.time()-slot_start_time[slot_i]                                
                                stx[slot_i].insert(INSERT,str(round(t_dsch_sec/60,2))+' мин\n')                                
                                stx[slot_i].insert(INSERT,'Ёмкость:\n')
                                ah=round(t_dsch_sec/3600*((imin[slot_i]+imax[slot_i])/2),2)
                                stx[slot_i].insert(INSERT,str(ah)+'А-ч')

                                log_file = open('log.txt','a') #здесь записывается в журнал (текстовый файл):
                                log_file.write('\n'+"Ячейка:")
                                log_file.write(str(slot_i+1)+'\n')
                                log_file.write("Текущее время:")
                                minutes=str(time.localtime(time.time()).tm_min)                                
                                if len(minutes)==1: minutes='0'+minutes
                                log_file.write(str(time.localtime(time.time()).tm_hour)+':'+minutes+'\n')                                
                                log_file.write("Umin="+str(umin[slot_i])+'\n')
                                log_file.write("Umax="+str(umax[slot_i])+'\n')
                                log_file.write("Imin="+str(imin[slot_i])+'\n')
                                log_file.write("Imax="+str(imax[slot_i])+'\n')
                                log_file.write('Время разряда:\n')
                                t_dsch_sec=time.time()-slot_start_time[slot_i]                                
                                log_file.write(str(round(t_dsch_sec/60,2))+' мин\n')                                
                                log_file.write('Ёмкость:\n')
                                ah=round(t_dsch_sec/3600*((imin[slot_i]+imax[slot_i])/2),2)
                                log_file.write(str(ah)+'А-ч'+'\n')                                
                                log_file.close()


                                

                                ok=1
                                if ah<amper_hour_min_norma: ok=0
                                if ah>amper_hour_max_norma: ok=0
                                if umin[slot_i]<Umin_norma: ok=0
                                if umax[slot_i]>Umax_norma: ok=0
                                if imin[slot_i]<Imin_norma: ok=0
                                if imax[slot_i]>Imax_norma: ok=0

                                reset_slot(slot_i)
                                if ok==1:   
                                    slot_status[slot_i]='complete'
                                    lbl_status[slot_i].config(text="Годен!",background='green')
                                else:
                                    slot_status[slot_i]='complete'
                                    lbl_status[slot_i].config(text="Не годен!",background='red')
                                
              

    
    

    window.after(100, loop1)
    
loop1()

window.mainloop()
