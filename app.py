from datetime import date, datetime
from os import environ
from re import U
from flask import Flask, render_template, request, url_for, redirect, abort, flash, session, jsonify
from mysql.connector import connection
from werkzeug.wrappers.response import ResponseStream
import pandas as pd
import numpy as np
import sys
from itertools import cycle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

import mysql.connector

midb = mysql.connector.connect(
    host="localhost",
    user='root',
    password='1234',
    database='1ta',
)

app.secret_key = 'my secret key'

cursor = midb.cursor(dictionary=True)


#------------ HOME ------------------
@app.route('/')
def index():
    cursor.execute("SELECT * FROM tarea")
    tareas = cursor.fetchall()
    return render_template('lista_tarea.html', data=tareas)




#------------ TAREAS --------------------
#------------AGREGAR --------------

@app.route('/creartarea', methods=['POST', 'GET'])
def creartarea():
    if request.method == 'POST':
        cursor.execute("SELECT * FROM tarea")
        tareas = cursor.fetchall()
        cursor.execute("select * from unidadtrabajo")
        unidades = cursor.fetchall()
        mayor = 0
 
        for tarea in tareas:
            if mayor == 0:
                mayor = tarea['id']
            else:
                mayor = tarea['id'] if tarea['id'] > mayor else mayor

        id = mayor + 1
        titulo = request.form.get('titulo', type=str)
        detalle = request.form.get('detalle', type=str)
        fechaentrada = request.form.get('fechaentrada', type=str)
        estado = request.form.get('estado', type=str)
        observacion = ''
        unidadtrabajo = request.form.get('unidadtrabajo', type=str)
        solicitante = request.form['solicitante']
        encargado = request.form.get('encargado', type=str)

        if solicitante == None or solicitante == '':
            flash('Tarea creada con exito!')
            return render_template('formulario_tarea.html', data=unidades)
        else:
            sql = "INSERT INTO tarea (id, titulo, detalle, fechaentrada, estado, observacion, unidadtrabajo, solicitante, encargado) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            values = (id, titulo, detalle, fechaentrada, estado, observacion, unidadtrabajo, solicitante, encargado)
            cursor.execute(sql,values)
            midb.commit()
            return render_template('formulario_tarea.html', data=unidades)

    elif request.method == 'GET':
        cursor.execute("select * from unidadtrabajo")
        unidades = cursor.fetchall()
        return render_template('formulario_tarea.html', data=unidades)

#---------------ELIMINAR---------------
@app.route('/eliminartarea/<int:id>')
def eliminar_tarea(id):
    cursor.execute('DELETE FROM tarea WHERE id = {0}'.format(id))
    midb.commit()
    flash('Tarea eliminada con exito!')
    return redirect(url_for('index'))

#----------- EDITAR --------------
@app.route('/editartarea/<int:id>')
def editar_tarea(id):
    cursor.execute('SELECT * FROM tarea WHERE id = {0}'.format(id))
    tarea = cursor.fetchone()
    return render_template('editar_tarea.html', data=tarea)

@app.route('/actualizaT/<id>', methods=['POST'])
def actualiza_tarea(id):
    if request.method == 'POST':
        fechasalida = request.form['fechasalida']
        estado = request.form['estado']
        observacion = request.form['observacion']
        encargado = request.form['encargado']
        
        if fechasalida == '':

            cursor.execute(
            """
            UPDATE tarea
            SET estado = %s,
                observacion = %s,
                encargado = %s
            WHERE id = %s
            """, (estado, observacion, encargado, id)
            )
        else:
            cursor.execute(
            """
            UPDATE tarea
            SET fechasalida = %s,
                estado = %s,
                observacion = %s,
                encargado = %s
            WHERE id = %s
            """, (fechasalida, estado, observacion, encargado, id)
            )


        midb.commit()
    flash('Tarea actualizada con exito!')
    return redirect(url_for('index'))

# ----------- FILTRAR --------------
@app.route('/filtrar', methods=['POST'])
def filtrar_tarea():
    if request.method == 'POST':
        estado = request.form['estado']
        if estado != 'total':
            cursor.execute("SELECT * FROM tarea WHERE estado = '%s'" %estado)
            tareas = cursor.fetchall()
            redirect(url_for('index'))
            return render_template('lista_tarea.html', data=tareas, estado=estado)
        else:
            cursor.execute("SELECT * FROM tarea")
            tareas = cursor.fetchall()
            redirect(url_for('index'))
            return render_template('lista_tarea.html', data=tareas)

# ----------- BUSCAR PERSONAL POR UNIDAD --------------
@app.route('/buscar', methods=['POST', 'GET'])
def buscar():
    if request.method == 'POST':
        unidad = request.form.get('unidad', type=str)
        cursor.execute("SELECT * FROM personal WHERE unidadtrabajo = '%s'" %unidad)
        personal = cursor.fetchall()
        return jsonify(personal)
         





#----------UNIDAD DE TRABAJO---------------
#----------- AGREGAR  --------------
@app.route('/unidadtrabajo', methods=['GET','POST'])
def crearunidadtrabajo():
    if request.method == 'POST':

        cursor.execute('select * from unidadtrabajo')
        unidades = cursor.fetchall()
        mayor = 0

        for unidad in unidades:
            if mayor == 0:
                mayor = unidad['id']
            else:
                mayor = unidad['id'] if unidad['id'] > mayor else mayor
        
        id = mayor + 1
        nombre = request.form['nombre']
        sql = "insert into unidadtrabajo (id, nombre) values (%s, %s)"
        values = (id, nombre)
        cursor.execute(sql, values)
        midb.commit()
        flash('Unidad agregada satisfactoriamente!')
        return redirect(url_for('crearunidadtrabajo'))

    elif request.method == 'GET':
        cursor.execute('select * from unidadtrabajo')
        unidades = cursor.fetchall()
        return render_template('unidad_trabajo.html', data=unidades)
        
#----------- ELIMINAR --------------
@app.route('/eliminarunidad/<int:id>')
def eliminar_unidad(id):
    cursor.execute("SELECT * FROM unidadtrabajo WHERE id = {0}". format(id))
    c = cursor.fetchall()
    cursor.execute("Select * FROM personal")
    p = cursor.fetchall()

    for unidad in c:
        unidadp = unidad['nombre']

    i = 0

    for personal in p:
        if unidadp == personal['unidadtrabajo']:
            i = 1

    if i == 0:
        cursor.execute('DELETE FROM unidadtrabajo WHERE id = {0}'.format(id))
        midb.commit()
        flash('Unidad de trabajo eliminada con exito!')
        return redirect(url_for('crearunidadtrabajo'))
    else:
        flash('No se puede eliminar la unidad de trabajo, hay usuarios asociados a ella')
        return redirect(url_for('crearunidadtrabajo'))






#----------- PERSONAL --------------
#----------- AGREGAR  --------------

@app.route('/personal', methods=['GET','POST'])
def crearpersonal():
    if request.method == 'POST':
        cursor.execute('select * from personal')
        lista_personal = cursor.fetchall()
        cursor.execute('select * from unidadtrabajo')
        unidades = cursor.fetchall()
        mayor = 0

        for personal in lista_personal:
            if mayor == 0:
                mayor = personal['id']
            else:
                mayor = personal['id'] if personal['id'] > mayor else mayor
        
        id = mayor + 1
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        cuerpo_rut = request.form['rut']
        unidadtrabajo = request.form['unidadtrabajo']
        digito = request.form['digito']
        
        i = 0
        lista_digito = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'k', 'K']
        for d in lista_digito:
            if d == digito:
                i += 1

        if i == 1:
            rut = cuerpo_rut + '-' + digito
            sql = "insert into personal (id, nombre, apellido, rut, unidadtrabajo) values (%s, %s, %s, %s, %s)"
            values = (id, nombre, apellido, rut, unidadtrabajo)
            cursor.execute(sql, values)
            midb.commit()
            flash('Personal agregado con exito!')
            return redirect(url_for('crearpersonal'))
        else:
            flash('Digito verificador incorrecto')
            return redirect(url_for('crearpersonal'))

    elif request.method == 'GET':
        cursor.execute('select * from unidadtrabajo')
        unidades = cursor.fetchall()
        cursor.execute('select * from personal')
        lista_p = cursor.fetchall()
        # print(lista_personal)
        return render_template('personal.html', data=unidades, data2=lista_p)
        
#----------- ELIMINAR --------------        
@app.route('/eliminarpersonal/<int:id>')
def eliminar_personal(id):
    cursor.execute('DELETE FROM personal WHERE id = {0}'.format(id))
    midb.commit()
    flash('Personal eliminado con exito!')
    return redirect(url_for('crearpersonal'))

#----------- EDITAR --------------
@app.route('/editarpersonal/<int:id>')
def editar_personal(id):
    cursor.execute('SELECT * FROM personal WHERE id = {0}'.format(id))
    personal = cursor.fetchone()
    cursor.execute('SELECT * FROM unidadtrabajo')
    unidades = cursor.fetchall()
    return render_template('editar_personal.html', data=personal, data2=unidades)

@app.route('/actualizaP/<id>', methods=['POST'])
def actualiza_personal(id):
    if request.method == 'POST':
        unidadtrabajo = request.form['unidadtrabajo']
        cursor.execute(
        """
        UPDATE personal
        SET unidadtrabajo = %s
        WHERE id = %s
        """, (unidadtrabajo, id)
        )
        midb.commit()
    flash('Personal actualizado con exito!')
    return redirect(url_for('crearpersonal'))







#----------- REPORTE --------------
#----------- LISTAR  --------------
@app.route('/reportes', methods=['POST', 'GET'])
def listarreporte():
    if request.method == 'POST':
        cursor.execute('SELECT * FROM tarea')
        tareas = cursor.fetchall()
        desde = request.form['desde']
        hasta = request.form['hasta']

        if hasta == '':
            hasta = datetime.now().date()

        i = 1
        lista_fecha = []
        lista_id = []

        while i <= len(tareas):
            for t in tareas:
                lista_fecha.append(t['fechaentrada'])
                lista_id.append(t['id'])
                i += 1


        df = pd.DataFrame({'Fechainicio':pd.to_datetime(lista_fecha), 'ident':lista_id})
        df = df.set_index(["Fechainicio"])
        filtro = df.loc[desde:str(hasta)]

        z = 0
        tareas_filtradas = []
        while z < len(filtro.index):
            id = int(filtro.values[z])
            cursor.execute("SELECT * FROM tarea WHERE id = '%s'" %id)
            c = cursor.fetchone()
            tareas_filtradas.append(c)
            z += 1
        
        
        total = len(tareas_filtradas)
        completa = []
        incompleta = []
        ingresada = []
        endesarrollo = []

        for tarea in tareas_filtradas:
            if tarea['estado'] == 'completa':
                completa.append(tarea)
            elif tarea['estado'] == 'incompleta':
                incompleta.append(tarea)
            elif tarea['estado'] == 'ingresada':
                ingresada.append(tarea)
            else:
                endesarrollo.append(tarea)

        c = len(completa)
        inc = len(incompleta)
        ing = len(ingresada)
        e = len(endesarrollo)

        reporte = [total, c, inc, ing, e]

        img=BytesIO()
        y = [total, c, inc, ing, e]
        x = ['Total', 'Completa', 'Incompleta', 'Ingresada', 'En desarrollo']

        plt.bar(x,y)
        
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        imgurl = base64.b64encode(img.getvalue()).decode('utf8')

        redirect(url_for('listarreporte'))
        return render_template('reportes.html', data=reporte, hasta=hasta, desde=desde, imgurl=imgurl)
    
    elif request.method == 'GET':
        cursor.execute('select * from tarea')
        tareas = cursor.fetchall()

        total = len(tareas)
        completa = []
        incompleta = []
        ingresada = []
        endesarrollo = []

        for tarea in tareas:
            if tarea['estado'] == 'completa':
                completa.append(tarea)
            elif tarea['estado'] == 'incompleta':
                incompleta.append(tarea)
            elif tarea['estado'] == 'ingresada':
                ingresada.append(tarea)
            else:
                endesarrollo.append(tarea)
        
        c = len(completa)
        inc = len(incompleta)
        ing = len(ingresada)
        e = len(endesarrollo)

        reporte = [total, c, inc, ing, e]

        img=BytesIO()
        y = [total, c, inc, ing, e]
        x = ['Total', 'Completa', 'Incompleta', 'Ingresada', 'En desarrollo']

        plt.bar(x,y)
        
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)
        imgurl = base64.b64encode(img.getvalue()).decode('utf8')

        return render_template('reportes.html', data=reporte, imgurl=imgurl)



if __name__ == '__main__':
    app.run(port = 8000, debug = True)