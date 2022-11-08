
"""
Created on Thu Oct 20 15:10:55 2022

@author: jpcam
"""
import seaborn as sns
import pandas as pd
import json
import matplotlib.pyplot as plt
import streamlit as st
import psycopg2 as pg
import logging
import sshtunnel
from sshtunnel import SSHTunnelForwarder
import datetime
import psycopg2.extras






# FUNCAO

def connectBd():

#create tunnel

    ssh_tunnel = SSHTunnelForwarder(
        (st.secrets["ssh_host"], st.secrets["ssh_port"]),
        ssh_username = st.secrets["ssh_username"],
        ssh_private_key= key,
        remote_bind_address = (st.secrets["host"],5432),
        local_bind_address = ('localhost', 123)
    )
#start tunnel

    ssh_tunnel.start()

#connect database

    conn = pg.connect(
        host= ssh_tunnel.local_bind_host,
        port= ssh_tunnel.local_bind_port,
        user= st.secrets["user"],
        password= st.secrets["password"],
        database= st.secrets["dbname"]
    )

    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    #executa a query para achar a data do grafico

    try:
        cur.execute("""
                select alarms.dispatched_at, alarms.ignored_at, frames.detections, alarms.evaluation_positive, alarms.inserted_at from frames
                join alarms on alarms.id = frames.alarm_id
                join cameras on alarms.camera_id = cameras.id where cameras.id= %s and alarms.inserted_at between %s and %s
                """,
            (camera_id, date_1, date_2))
        row = cur.fetchall()

    except psycopg2.errors.InvalidTextRepresentation :
        row = None

    conn.close()
    ssh_tunnel.close()


    return row



def removerNA(coluna):
    x = df.dropna(subset= coluna)
    x = x[2]
    x=x.dropna()
    x = x.apply(lambda x: [obj['probability'] for obj in x if obj['class'] == 1 ])

    a = [round(j * 2, 1) / 2 for i in x for j in i]

    try:
        print(a[0])
        a = filter(lambda x: max >= x >= min, a)
    except:
        a = None

    return a,x

# ALERTAS DISPACHADOS

def getData(va,min):

    df_dispatched = df.dropna(subset=0)

    dispatched, x = removerNA(df,0)

    # ALERTAS IGNORADOS

    ignored = removerNA(df,1)[0]


    # FEEDBACKS

    try:
        keys = list(x.keys())

        df_feedbacks = df_dispatched.dropna(subset="evaluation_positive")
        df_feedbacks = df_feedbacks["evaluation_positive"]

        positive_feedback = []
        negative_feedback = []


        cont = 0
        frame_id = []


        for i in x:
            row = keys[cont]
            for j in i:
                if j >min:
                    try:
                        if df_feedbacks.loc[row] == True:
                            #Adiciona os numeros na lista feedback postivo
                            positive_feedback.append(j)
                            #Adiciona os frames positivos na lista
                            frame_id.append(df.loc[row,"id-2"])

                        else:
                            negative_feedback.append(j)
                    except:
                        pass
            cont += 1

        #ARREDONDA OS VALORES

        positive_feedback= [round(i, 2) for i in positive_feedback]
        negative_feedback= [round(i, 2) for i in negative_feedback]



    # RETIRAR FRAME ID DOS FEEDBACKS POSITIVOS

        st.write("Frame id com feedback positivo: ",frame_id)

    except:
        negative_feedback = None
        positive_feedback = None


    return negative_feedback, positive_feedback, ignored, dispatched


# MONTAR GRAFICO

def createPlot(negative_feedback,positive_feedback,ignored,dispatched):
    fig = plt.figure(figsize=(9, 7))

    x = sns.histplot(data=(negative_feedback, positive_feedback, ignored, dispatched), multiple="layer",
                     element="poly", palette="Set1", bins=9, binrange=(min, min + 0.4),
                     )

    plt.title("ALARMES")
    plt.legend(labels=("Alarmes Despachados", "Alarmes Ignorados", "FeedBacks Positivos", "FeedBacks Negativos"))
    st.pyplot(fig)




camera_id = st.text_input("Insira Câmera ID: ")

min = st.number_input("Insira valor mínimo de confiabilidade: ", value= 0.3)
max = min + 0.4
date_1 = str(st.date_input("Insira data inicial: ", value=None))
time_1 = str(st.time_input("Insira horário: ", key='1', value=datetime.time(0,0)))
date_2 = str(st.date_input("Insira data final: ", value=None))
time_2 = str(st.time_input("Insira horário: ", key='2', value=datetime.time(0,0)))








if camera_id != None:
    if st.button('Enviar'):
        date_1 = (date_1 + " " + time_1)
        date_2 = (date_2 + " " + time_2)

        row = connectBd()
        if row!= None:


            df = pd.DataFrame(row)

            try:
                x, y, w, z = getData(df, min)
                createPlot(x, y, w, z)
            except KeyError:
                st.write("Erro!!! Não existem alarmes")

        else:

             st.write("Erro!!! Câmera inválida")











