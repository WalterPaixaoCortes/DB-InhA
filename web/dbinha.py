# -*- coding: utf-8 -*-
#----------------------------------------------------------------------------------------------------------------------
# Imports 
#----------------------------------------------------------------------------------------------------------------------
from flask import Flask, render_template, request, ext

import traceback
import labio.configWrapper
import labio.dbWrapper 
import smtplib
from flask.ext.babel import format_datetime, Babel
#----------------------------------------------------------------------------------------------------------------------
# Inicializacao 
#----------------------------------------------------------------------------------------------------------------------

app = Flask('dbinha')
babel = Babel(app)

#----------------------------------------------------------------------------------------------------------------------
# Views 
#----------------------------------------------------------------------------------------------------------------------
@app.route ('/')
@app.route ('/Home')

def index():
	estruturas = list_structures()
	return render_template ('index.html',structures=estruturas)

@app.route ('/pesquisa/<pdbid>')
def pesquisa_detalhe(pdbid='1ENY'):
	strut = get_structure(pdbid)
	originator = get_related_articles(pdbid,'Originator')
	articles = get_related_articles(pdbid,'List')
	ligands = get_ligands(pdbid)
	goterms = get_go_terms(pdbid)
	return render_template ('pesquisa_detalhe.html',strut=strut,originator=originator,articles=articles,ligands=ligands,goterms=goterms)  

@app.route ('/pesquisa2/<pdbid>')
def pesquisa_detalhe2(pdbid='1ENY'):
	strut = get_structure(pdbid)
	originator = get_related_articles(pdbid,'Originator')
	articles = get_related_articles(pdbid,'List')
	ligands = get_ligands(pdbid)
	goterms = get_go_terms(pdbid)
	return render_template ('pesquisa_detalhe2.html',strut=strut,originator=originator,articles=articles,ligands=ligands,goterms=goterms)  

@app.route ('/pesquisa/')
def pesquisa():
	struts = search_structures()
	return render_template ('pesquisa.html',struts=struts)  

@app.route ('/palavras/')
def palavras():
	struts = list_words()
	return render_template ('palavras.html',words=struts)  

@app.route ('/artigos/')
def artigos():
	struts = list_articles()
	return render_template ('artigos.html',struts=struts)  

@app.route ('/equipe/')
def equipe():
    return render_template ('equipe.html')

@app.route ('/sobre/')
def sobre():
    return render_template ('equipe.html')

@app.route ('/citacao/')
def citacao():
    return render_template ('equipe.html')

@app.route ('/ajuda/')
def ajuda():
    return render_template ('equipe.html')

@app.route ('/fale_conosco/')
def fale_conosco():
    return render_template ('fale_conosco.html',messages=None) 

@app.route ('/visualizar/')
def visualizar():
    return render_template ('visualizar.html',messages=None)     

@app.route ('/send/email', methods=['POST'])
def send_email():
	results = 'Email enviado com sucesso.'
	try:
		sendemail(request.form['email'],['labio.dev@gmail.com'],None,'%s - Enviado por %s' % (request.form['assunto'],request.form['name']),request.form['message'])
	except:
		results = traceback.format_exc()

	return render_template ('fale_conosco.html',messages={'main':results})  

#--------------------------------------------------------------------------------------------------------
# Other Routines
#--------------------------------------------------------------------------------------------------------
def sendemail(from_addr, to_addr_list, cc_addr_list,
              subject, message,
              login='labio.dev', password='Labio602',
              smtpserver='smtp.gmail.com:587'):
    header  = 'From: %s\n' % from_addr
    header += 'To: %s\n' % ','.join(to_addr_list)
    
    if cc_addr_list:
    	header += 'Cc: %s\n' % ','.join(cc_addr_list)
    
    header += 'Subject: %s\n\n' % subject
    message = header + "Email from: " + from_addr + "\n\n" + message
 
    server = smtplib.SMTP(smtpserver)
    server.starttls()
    server.login(login,password)
    problems = server.sendmail(from_addr, to_addr_list, message)
    server.quit()

def list_structures():
	results = None
	try:
		fileConfig = labio.configWrapper.load_configuration('db.config')
		if fileConfig.isLoaded:
			db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()

			if db2.isDatabaseOpen():
				cursor = db2.getData(fileConfig.sqlSelectStructures)
				row = cursor.fetchall ()
				cursor.close ()
				db2.close ()
				results = row
			else:
				app.logger.error('Database not opened.')
		else:
			app.logger.error('Configuration File Not Found.')
	except:
		app.logger.error(traceback.format_exc())

	resp = results

	return resp

def list_articles():
	results = None
	try:
		fileConfig = labio.configWrapper.load_configuration('db.config')
		if fileConfig.isLoaded:
			db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()

			if db2.isDatabaseOpen():
				cursor = db2.getData(fileConfig.sqlSelectArticles)
				row = cursor.fetchall ()
				cursor.close ()
				db2.close ()
				results = row
			else:
				app.logger.error('Database not opened.')
		else:
			app.logger.error('Configuration File Not Found.')
	except:
		app.logger.error(traceback.format_exc())

	resp = results

	return resp

def list_words():
	results = None
	try:
		fileConfig = labio.configWrapper.load_configuration('db.config')
		if fileConfig.isLoaded:
			db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()

			if db2.isDatabaseOpen():
				cursor = db2.getData(fileConfig.sqlGetWords)
				row = cursor.fetchall ()
				cursor.close ()
				db2.close ()
				results = row
			else:
				app.logger.error('Database not opened.')
		else:
			app.logger.error('Configuration File Not Found.')
	except:
		app.logger.error(traceback.format_exc())

	resp = results

	return resp

def search_structures():
	results = None
	try:
		fileConfig = labio.configWrapper.load_configuration('db.config')
		if fileConfig.isLoaded:
			db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()

			if db2.isDatabaseOpen():
				cursor = db2.getData(fileConfig.sqlSearchStructures)
				row = cursor.fetchall ()
				cursor.close ()
				db2.close ()
				results = row
			else:
				app.logger.error('Database not opened.')
		else:
			app.logger.error('Configuration File Not Found.')
	except:
		app.logger.error(traceback.format_exc())

	resp = results

	return resp

def get_structure(pdbid):
	results = None
	try:
		fileConfig = labio.configWrapper.load_configuration('db.config')
		if fileConfig.isLoaded:
			db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()

			if db2.isDatabaseOpen():
				cursor = db2.getData(fileConfig.sqlGetStructure,[pdbid])
				row = cursor.fetchall ()
				cursor.close ()
				db2.close ()
				results = row
			else:
				app.logger.error('Database not opened.')
		else:
			app.logger.error('Configuration File Not Found.')
	except:
		app.logger.error(traceback.format_exc())

	resp = results

	return resp

def get_related_articles(pdbid,rel_type):
	results = None
	try:
		fileConfig = labio.configWrapper.load_configuration('db.config')
		if fileConfig.isLoaded:
			db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()

			if db2.isDatabaseOpen():
				if rel_type == 'Originator':
					cursor = db2.getData(fileConfig.sqlGetRelatedArticlesOriginator,[pdbid])
				else:
					cursor = db2.getData(fileConfig.sqlGetRelatedArticles,[pdbid])
				row = cursor.fetchall ()
				cursor.close ()
				db2.close ()
				results = row
			else:
				app.logger.error('Database not opened.')
		else:
			app.logger.error('Configuration File Not Found.')
	except:
		app.logger.error(traceback.format_exc())

	resp = results

	return resp

def get_ligands(pdbid):
	results = None
	try:
		fileConfig = labio.configWrapper.load_configuration('db.config')
		if fileConfig.isLoaded:
			db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()

			if db2.isDatabaseOpen():
				cursor = db2.getData(fileConfig.sqlGetLigands,[pdbid])
				row = cursor.fetchall ()
				cursor.close ()
				db2.close ()
				results = row
			else:
				app.logger.error('Database not opened.')
		else:
			app.logger.error('Configuration File Not Found.')
	except:
		app.logger.error(traceback.format_exc())

	resp = results

	return resp

def get_go_terms(pdbid):
	results = None
	try:
		fileConfig = labio.configWrapper.load_configuration('db.config')
		if fileConfig.isLoaded:
			db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()

			if db2.isDatabaseOpen():
				cursor = db2.getData(fileConfig.sqlGetGoTerms,[pdbid])
				row = cursor.fetchall ()
				cursor.close ()
				db2.close ()
				results = row
			else:
				app.logger.error('Database not opened.')
		else:
			app.logger.error('Configuration File Not Found.')
	except:
		app.logger.error(traceback.format_exc())

	resp = results

	return resp

@app.template_filter('datetime')
def format_datetime2(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="MM/dd/y"
    return format_datetime(value, format)

#--------------------------------------------------------------------------------------------------------
# Caller
#--------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
	app.run(debug=True,port=8080)


