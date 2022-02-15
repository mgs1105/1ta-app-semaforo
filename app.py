from datetime import date, datetime
from os import environ
from re import I, U
from flask import Flask, render_template, request, url_for, redirect, abort, flash, session, jsonify, g
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
import mysql.connector

class User:
    def __init__(self, id, rut, password, unidad):
        self.id = id
        self.rut = rut
        self.password = password
        self.unidad = unidad

    def __repr__(self):
        return f'{self.rut}'


app = Flask(__name__)

midb = mysql.connector.connect(
    host="localhost",
    user='root',
    password='1234',
    database='1ta',
)
app.secret_key = 'my secret key'

cursor = midb.cursor(dictionary=True)

@app.before_request
def before_request():
    g.user = None
     
    users = []
    cursor.execute("SELECT * FROM personal")
    personas = cursor.fetchall()
    for p in personas:
        users.append(User(id=p['id'], rut=p['rut'], password=p['password'], unidad=p['unidadtrabajo']))
    
    if 'user_id' in session:
        user = [x for x in users if x.id == session['user_id']]
        g.user = user

#---------- HOME -----------
@app.route('/')
def index():
    session.pop('user_id', None)
    return render_template('home.html')

#---------------- LOGIN ----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session.pop('user_id', None)
       
        users = []
        cursor.execute("SELECT * FROM personal")
        personas = cursor.fetchall()
        for p in personas:
            users.append(User(id=p['id'], rut=p['rut'], password=p['password'], unidad=p['unidadtrabajo']))

        rut = request.form['rut']
        password = request.form['password']
        
        cursor.execute("SELECT * FROM personal WHERE rut = '%s'" %rut)
        personal = cursor.fetchone()

        if personal != None:
            user = [x for x in users if x.rut == rut][0]
            if user and user.password == password:
                session['user_id'] = user.id
                return redirect(url_for('usuario_lista'))
        
            flash('Las credenciales ingresadas son incorrectas')
            return redirect(url_for('index'))
        else:
            flash('Las credenciales ingresadas son incorrectas')
            return redirect(url_for('index'))

    else:
        session.pop('user_id', None)
        return render_template('home.html')


#-------------------- ALERTA LOGOUT COMUN -----------------------
@app.route('/alerta_cerrar_sesion', methods=['POST', 'GET'])
def logout():
    flash("¿Seguro que desea cerrar sesion?")
    return render_template('usuario_lista_tarea.html')


#-------------------- ALERTA LOGOUT INFORMATICO -----------------------
@app.route('/alerta_cerrar_sesion_i', methods=['POST', 'GET'])
def logout_info():
    flash("¿Seguro que desea cerrar sesion?")
    return render_template('lista_tarea.html')


#-------------------- CERRAR SESION -----------------------
@app.route('/cerrar_sesion', methods=['POST', 'GET'])
def cerrar_sesion():
    if request.method == 'POST':
        return redirect(url_for('index'))



#--------------------------------------------------------
#--------------- PAGINAS USUARIO COMUN ------------------
#--------------------------------------------------------



#--------------------- LISTA TAREAS ---------------------
@app.route('/usuario_lista',  methods=['GET','POST'])
def usuario_lista():
    if not g.user:
        return redirect(url_for('login'))

    cursor.execute("SELECT * FROM personal WHERE rut = '%s'" %g.user[0])
    per = cursor.fetchone()
    if per['unidadtrabajo'] == 'Informatica':
        return redirect(url_for('listatarea'))
    else:
        n = per['nombre']
        a = per['apellido']
        solicitante = n + ' ' + a
        cursor.execute("SELECT * FROM tarea WHERE solicitante = '%s'" %solicitante)
        tareas = cursor.fetchall()
        return render_template('usuario_lista_tarea.html', data=tareas)

#---------------ELIMINAR---------------
@app.route('/usuario_eliminartarea/<int:id>', methods=['POST'])
def usuario_eliminar_tarea(id):
    if request.method == 'POST':
        cursor.execute('DELETE FROM tarea WHERE id = {0}'.format(id))
        midb.commit()
        return redirect(url_for('usuario_lista'))


# ------------ ALERTA ELIMINAR -----------------
@app.route('/usuario_alerta_eliminar_tarea/<int:id>')
def usuario_alerta_eliminar_tarea(id):
    cursor.execute('SELECT * FROM tarea WHERE id = {0}'.format(id))
    tarea = cursor.fetchone()
    titulo = tarea['titulo']
    flash("%s" %id)
    return render_template('usuario_lista_tarea.html', titulo=titulo)


#------------- FORMULARIO TAREA DE USUAIOS ---------------------------
@app.route('/usuario_formulario', methods=['POST', 'GET'])
def usuario_formulario():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        cursor.execute('SELECT * FROM tarea;')
        tareas = cursor.fetchall()
        cursor.execute("SELECT * FROM personal WHERE rut = '%s'" %g.user[0])
        usuario = cursor.fetchone()
        mayor = 0

        for tarea in tareas:
            if mayor == 0:
                mayor = tarea['id']
            else:
                mayor = tarea['id'] if tarea['id'] > mayor else mayor

        id = mayor + 1
        titulo = request.form.get('titulo', type=str).capitalize()
        detalle = request.form.get('detalle', type=str).capitalize()
        fechaentrada = request.form.get('fechaentrada', type=str)
        estado = 'Ingresada'
        observacion = ''
        unidadtrabajo = usuario['unidadtrabajo']
        solicitante = usuario['nombre'] + ' ' + usuario['apellido']
        encargado = ''

        if solicitante == None or solicitante == '':
            flash('¡Tarea creada con exito!')
            return render_template('usuario_formulario_tarea.html')
        else:
            sql = 'INSERT INTO tarea (id, titulo, detalle, fechaentrada, estado, observacion, unidadtrabajo, solicitante, encargado) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            values = (id, titulo, detalle, fechaentrada, estado, observacion, unidadtrabajo, solicitante, encargado)
            cursor.execute(sql,values)
            midb.commit()
            flash('¡Tarea creada con exito!')
            return render_template('usuario_formulario_tarea.html')
    
    if request.method == 'GET':
            cursor.execute('SELECT * FROM unidadtrabajo;')
            unidades = cursor.fetchall()
            return render_template('usuario_formulario_tarea.html', data=unidades)    


@app.route('/filtro_usuario', methods=['GET', 'POST'])
def filtro_usuario():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        cursor.execute("SELECT * FROM personal WHERE rut = '%s'" %g.user[0])
        usuario = cursor.fetchone()
        solicitante = usuario['nombre'] + ' ' + usuario['apellido']
        opcion = request.form.get('opcion', type=str)

        if opcion == 'total':
            cursor.execute("SELECT * FROM tarea WHERE solicitante = '%s'" %solicitante)
            tareas = cursor.fetchall()
            return jsonify(tareas)
        else:
            lista_tareas = []
            cursor.execute("SELECT * FROM tarea WHERE estado = '%s'" %opcion)
            tareas = cursor.fetchall()
            for tareas_filtradas in tareas:
                if tareas_filtradas['solicitante'] == solicitante:
                    lista_tareas.append(tareas_filtradas)
            return jsonify(lista_tareas)


#----------------------------------------------------
#------------ PAGINAS USUARIO INFORMATICO -------------
#----------------------------------------------------




#------------ TAREAS --------------------
#------------ LISTA TAREAS --------------------
@app.route('/listatarea')
def listatarea():
    if not g.user:
        return redirect(url_for('login'))
    
    cursor.execute('SELECT * FROM tarea;')
    tareas = cursor.fetchall()
    return render_template('lista_tarea.html',  data=tareas)

#------------AGREGAR --------------
@app.route('/creartarea', methods=['POST', 'GET'])
def creartarea():
    if not g.user:
        return redirect(url_for('login'))
    
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
            sql = "INSERT INTO tarea (id, titulo, detalle, fechaentrada, estado, observacion, unidadtrabajo, solicitante, encargado, colores) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
            values = (id, titulo, detalle, fechaentrada, estado, observacion, unidadtrabajo, solicitante, encargado)
            cursor.execute(sql,values)
            midb.commit()
            flash('Tarea creada con exito!')
            return render_template('formulario_tarea.html', data=unidades)

    elif request.method == 'GET':
        cursor.execute("select * from unidadtrabajo")
        unidades = cursor.fetchall()
        return render_template('formulario_tarea.html', data=unidades)

#---------------ELIMINAR---------------
@app.route('/eliminartarea/<int:id>', methods=['POST'])
def eliminar_tarea(id):
    if request.method == 'POST':
        cursor.execute('DELETE FROM tarea WHERE id = {0}'.format(id))
        midb.commit()
        return redirect(url_for('listatarea'))

# ------------ ALERTA ELIMINAR -----------------
@app.route('/alerta_eliminar_tarea/<int:id>')
def alerta_eliminar_tarea(id):
    cursor.execute('SELECT * FROM tarea WHERE id = {0}'.format(id))
    tarea = cursor.fetchone()
    titulo = tarea['titulo']
    flash("%s" %id)
    return render_template('lista_tarea.html', titulo=titulo)

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
        observacion = request.form['observacion'].capitalize()
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
    flash('¡Tarea actualizada con exito!')
    return redirect(url_for('listatarea'))


#----------- FILTRO DINAMICO -------------------
@app.route('/filtrodinamico', methods=['POST', 'GET'])
def filtrodinamico():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        opcion = request.form.get('opcion', type=str)
        if opcion == 'total':
            cursor.execute("SELECT * FROM tarea")
            tareas = cursor.fetchall()
            return jsonify(tareas)
        else:    
            cursor.execute("SELECT * FROM tarea WHERE estado = '%s'" %opcion)
            tareas = cursor.fetchall()
            return jsonify(tareas)



# ----------- BUSCAR PERSONAL POR UNIDAD --------------
@app.route('/buscar', methods=['POST', 'GET'])
def buscar():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        unidad = request.form.get('unidad', type=str)
        cursor.execute("SELECT * FROM personal WHERE unidadtrabajo = '%s'" %unidad)
        personal = cursor.fetchall()
        return jsonify(personal)
         




#----------UNIDAD DE TRABAJO---------------
#----------- AGREGAR  --------------
@app.route('/unidadtrabajo', methods=['GET','POST'])
def crearunidadtrabajo():
    if not g.user:
        return redirect(url_for('login'))

    if request.method == 'POST':
        cursor.execute('SELECT * FROM unidadtrabajo')
        unidades = cursor.fetchall()

        mayor = 0
        for unidad in unidades:
            if mayor == 0:
                mayor = unidad['id']
            else:
                mayor = unidad['id'] if unidad['id'] > mayor else mayor
        
        id = mayor + 1
        nombre = request.form['nombre'].capitalize()

        cursor.execute('SELECT * FROM unidadtrabajo')
        uni = cursor.fetchall()

        i = 0
        for u in uni:
            if u['nombre'] == nombre:
                i += 1

        if i == 1:
            flash('La unidad de trabajo ya existe')    
            return redirect(url_for('crearunidadtrabajo'))
        else:  
            sql = "insert into unidadtrabajo (id, nombre) values (%s, %s)"
            values = (id, nombre)
            cursor.execute(sql, values)
            midb.commit()
            flash('¡Unidad de trabajo creada con exito!')
            return redirect(url_for('crearunidadtrabajo'))

    elif request.method == 'GET':
        cursor.execute('select * from unidadtrabajo')
        unidades = cursor.fetchall()
        return render_template('unidad_trabajo.html', data=unidades)
        
#----------- ELIMINAR --------------
@app.route('/eliminarunidad/<int:id>', methods=['POST'])
def eliminar_unidad(id):
    if request.method == 'POST':
        cursor.execute('DELETE FROM unidadtrabajo WHERE id = {0}'.format(id))
        midb.commit()
        return redirect(url_for('crearunidadtrabajo'))

#------------------ BUSCAR UNIDAD ---------------
@app.route('/buscar_unidad/<int:id>')
def buscar_unidad(id):
    cursor.execute("SELECT * FROM unidadtrabajo WHERE id = {0}".format(id))
    unidad = cursor.fetchone()
    nombreU = unidad['nombre']
    cursor.execute("SELECT * FROM personal WHERE unidadtrabajo = '%s'" %nombreU)
    personas = cursor.fetchall()
    if len(personas) != 0:
        flash("No se puede eliminar la unidad de trabajo, existe personal asociado a ella")
        return redirect(url_for('crearunidadtrabajo'))
    else:
        flash("%s" %id)
        return render_template('unidad_trabajo.html', nombre=nombreU)
        



#----------- PERSONAL --------------
#----------- AGREGAR  --------------
@app.route('/personal', methods=['GET','POST'])
def crearpersonal():
    if not g.user:
        return redirect(url_for('login'))

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
        nombre = request.form['nombre'].capitalize()
        apellido = request.form['apellido'].capitalize()
        rut = request.form['rut']
        unidadtrabajo = request.form['unidadtrabajo']
        password = request.form['password']
        repetir_password = request.form['repetir-password']


        cursor.execute('SELECT * FROM personal')
        personas = cursor.fetchall()    

        #Validar rut

        i = 0
        
        if rut.count('-') != 1 or rut.count('k') > 1:
            i = 2
        else:
            if len(rut) == 10:
                
                if rut.find('k') == -1 or rut.find('k') == 9:
                    if rut.find('-') != 8:
                        i = 2
                else:
                    i = 2

            elif len(rut) == 9:
                if rut.find('k') == -1 or rut.find('k') == 8:
                    if rut.find('-') != 7:
                        i = 2
                else:
                    i = 2
            else:
                i = 2
        
        for p in personas:
            if p['rut'] == rut:
                i += 1


        if i == 1:
            flash('El personal que se intenta agregar ya existe')
            return redirect(url_for('crearpersonal'))
        if i == 2:
            flash('El rut no es valido')
            return redirect(url_for('crearpersonal'))
        elif password != repetir_password:
            flash('Los password no coinciden')
            return redirect(url_for('crearpersonal'))
        else:
            sql = "insert into personal (id, nombre, apellido, rut, unidadtrabajo, password) values (%s, %s, %s, %s, %s, %s)"
            values = (id, nombre, apellido, rut, unidadtrabajo, password)
            cursor.execute(sql, values)
            midb.commit()
            flash('¡Personal agregado con exito!')
            return redirect(url_for('crearpersonal'))

    elif request.method == 'GET':
        cursor.execute('select * from unidadtrabajo')
        unidades = cursor.fetchall()
        cursor.execute('select * from personal')
        lista_p = cursor.fetchall()
        return render_template('personal.html', data=unidades, data2=lista_p)
        
#----------- ELIMINAR --------------        
@app.route('/eliminarpersonal/<int:id>',  methods=['POST'])
def eliminar_personal(id):
    if request.method == 'POST':
        cursor.execute('DELETE FROM personal WHERE id = {0}'.format(id))
        midb.commit()
        return redirect(url_for('crearpersonal'))

# ------------ ALERTA ELIMINAR -----------------
@app.route('/alertaeliminar/<int:id>')
def alerta_eliminar(id):
    cursor.execute('SELECT * FROM personal WHERE id = {0}'.format(id))
    personal = cursor.fetchone()
    n = personal['nombre']
    a = personal['apellido']
    nombre = n + ' ' + a 
    flash("%s" %id)
    return render_template('personal.html', nom=nombre)

#----------- EDITAR --------------
@app.route('/editarpersonal/<int:id>')
def editar_personal(id):
    cursor.execute('SELECT * FROM personal WHERE id = {0}'.format(id))
    personal = cursor.fetchone()
    cursor.execute('SELECT * FROM unidadtrabajo')
    unidades = cursor.fetchall()
    
    p = 0
    while p < len(unidades):
        if personal['unidadtrabajo'] == unidades[p]['nombre']:
            unidades.remove(unidades[p])
        p += 1

    return render_template('editar_personal.html', data=personal, data2=unidades)

@app.route('/actualizaP/<id>', methods=['POST'])
def actualiza_personal(id):
    if request.method == 'POST':
        
        password = request.form['password']
        repetir_password = request.form['repetir_password']
        unidadtrabajo = request.form['unidadtrabajo']

        if password != repetir_password:
            flash('Los password no coinciden')
            return redirect(url_for('editar_personal', id=id))

        elif password == '' or repetir_password == '':
            cursor.execute(
            """
            UPDATE personal
            SET unidadtrabajo = %s
            WHERE id = %s
            """, (unidadtrabajo, id)
            )
            midb.commit()
            flash('¡Personal actualizado con exito!')
            return redirect(url_for('crearpersonal'))
            
        elif password == repetir_password:
            cursor.execute(
            """
            UPDATE personal
            SET unidadtrabajo = %s,
                password = %s
            WHERE id = %s
            """, (unidadtrabajo, password, id)
            )
            midb.commit()
            flash('¡Personal actualizado con exito!')
            return redirect(url_for('crearpersonal'))





#----------- REPORTE --------------
#----------- LISTAR  --------------
@app.route('/reportes', methods=['POST', 'GET'])
def listarreporte():

    if not g.user:
        return redirect(url_for('login'))
            
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