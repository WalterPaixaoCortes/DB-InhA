# -*- coding: utf-8 -*-
import sys
import traceback
import datetime
import time
import os
import logging
import MySQLdb

import labio.configWrapper
import labio.argParseWrapper
import labio.logWrapper
import labio.dbWrapper

from xml.etree import ElementTree
from bs4 import *

from components import PDB
from components.PubMed import *

from suds.client import Client

#----------------------------------------------------------------------------------------------------------------------#


def retrieve_structures(cfg,log):
    final_list = None
    try:
        resList = []
        for item in cfg.pdbQueries:
            res = PDB.execute_advanced_query(log, cfg.pdbAdvancedSearchURL,item)
            resList.append(res.split('\n'))
                                
        log.info('Intersecting results...')
        final_list = list(eval(PDB.merge_results(resList)))
        final_list = filter(len,final_list)
    except:
        log.error(traceback.format_exc())
    
    return final_list

def save_structures(cfg,log,db,listItem):
    try:
        if cfg.FullReload:
            db.executeCommand(cfg.sqlTruncateCandidate)
        
        for item in listItem:
            log.info('Saving Candidate: %s...' % item)
            if PDB.get_file(cfg,log,item):
                pdb = PDB.parse_header(cfg,item)
                db.executeCommand(cfg.sqlInsertCandidate,(item, MySQLdb.escape_string(PDB.get_content()), 
                                                                MySQLdb.escape_string(pdb['name']), 
                                                                MySQLdb.escape_string(pdb['author']), 
                                                                pdb['deposition_date'], 
                                                                pdb['release_date'], '0', 
                                                                pdb['resolution'], 
                                                                pdb['head'], 
                                                                pdb['structure_method'], 
                                                                pdb['compound']['1']['chain'] if 'chain' in pdb['compound']['1'] else '' , 
                                                                pdb['compound']['1']['ec_number'] if 'ec_number' in pdb['compound']['1'] else '', 
                                                                pdb['source']['1']['organism_taxid'] if 'organism_taxid' in pdb['source']['1'] else '',
                                                                pdb['source']['1']['organism_scientific'] if 'organism_scientific' in pdb['source']['1'] else '',
                                                                pdb['source']['1']['expression_system_taxid'] if 'expression_system_taxid' in pdb['source']['1'] else '',
                                                                pdb['source']['1']['expression_system'] if 'expression_system' in pdb['source']['1'] else ''))

                db.commit()
    except:
        log.error(traceback.format_exc())
        db.rollback()

def build_training_set(cfg,log,db,pm):
    try:
        listAdded = []
            
        if cfg.FullReload:
            db.executeCommand(cfg.sqlTruncateTrainingSet)

        log.info('Getting Reference articles...')
        candidates = db.getData(cfg.sqlSelectCandidates).fetchall()

        for addFile in candidates:
            key = addFile[0]
            f = PDB.parse_prody(cfg,key)
            if f.status == 'Imported' and (f.journal.pmid not in listAdded) and f.journal.pmid != "":
                article = pm.get_pubmed_article(f.journal.pmid)
                pm.save_pubmed_article(f.journal.pmid,article,'Training')
                listAdded.append(f.journal.pmid)

        db.commit()
    except:
        log.error(traceback.format_exc())
        db.rollback()
        raise Exception('Training Set was not built.')

def search_literature(cfg,log,db,pm):
    try:
        if cfg.FullReload:
            db.executeCommand(cfg.sqlTruncateLiterature)
        
        result = pm.search_pubmed()
        
        if result:
            log.info('Number of entries: %s...' % result['Count'])
            for item in result['IdList']:
                try:
                    resCount = db.getData(cfg.sqlCountLiterature % (item))
                    row = resCount.fetchall()
                    if row[0][0] == 0:
                        article = pm.get_pubmed_article(item)
                        if not pm.save_pubmed_article(item, article, 'Literature'):
                            print(article)
                    resCount.close()
                except:
                    log.error(traceback.format_exc())
            db.commit()
        else:
            log.info('No PubMed literature found.')
    except:
        db.rollback()
        log.error(traceback.format_exc())
        raise Exception('Literature not added.')

def rank_literature(cfg,log,db):
    e = None
    try:
        if cfg.FullReload:
            db.executeCommand(cfg.sqlTruncateWords)
        
        client = Client(cfg.MedLineRankURL)
        
        log.info('Preparing Training Set...')
        trainingCursor = db.getData(cfg.sqlSelectTrainingSet).fetchall()
        trainingList = []
        for line in trainingCursor:
            trainingList.append(line[0])
        trainingSet = cfg.pubmedDelimiter.join(trainingList)

        log.info('Preparing Articles to Rank...')
        testingCursor = db.getData(cfg.sqlSelectTestingSet).fetchall()
        testingList = []
        for line in testingCursor:
            testingList.append(line[0])
        testingSet = cfg.pubmedDelimiter.join(testingList)

        log.info('Calling the Web Service...')
        html = client.service.rank('list',trainingSet,'medline','','list',testingSet)

        fw = open(os.path.join(cfg.extractFilesFolder,cfg.pubmedRankFile), "w")
        if cfg.pubmedFindString in html:
            fw.write(html)
        else:
            fw.write(html.decode('base64'))
        fw.close()

        e = ElementTree.parse(os.path.join(cfg.extractFilesFolder,cfg.pubmedRankFile)).getroot()

        if e is not None:
            log.info('Updating articles...')
            for abstract in e.findall(cfg.rankAbstracts):
                db.executeCommand(cfg.sqlUpdateLiterature,(abstract.get('rank'),abstract.find('pvalue').text,abstract.find('link').text,abstract.find('pmid').text))

            log.info('Saving word list...')
            for abstract in e.findall(cfg.rankWords):
                db.executeCommand(cfg.sqlInsertWords,(abstract.get('rank'),abstract.find('value').text,abstract.find('weight').text))

        db.commit()
    except:
        log.error(traceback.format_exc())
        db.rollback()

def relate_structures(cfg,log,db, pm):
    try:
        log.info('Merging Training and Result Sets...')
        rows = db.getData(cfg.sqlCopyTrainingSetIntoLiterature).fetchall()
        for row in rows:
            article = pm.get_pubmed_article(row['pubmed_id'])
            pm.save_pubmed_article(row['pubmed_id'], article, 'Literature')
        
        if cfg.FullReload:
            db.executeCommand(cfg.sqlTruncateRel)

        candidates = db.getData(cfg.sqlSelectCandidates).fetchall()

        for addFile in candidates:
            key = addFile['pdbID']
            f = PDB.parse_prody(cfg,key)
            if f.journal.pmid != "":
                db.executeCommand(cfg.sqlInsertRel, (addFile['pdbID'], f.journal.pmid, 'Originator'))
                log.info('Opening article to find references to structures...')
                fileName = pm.get_related_pubmed_articles(f.journal.pmid)
                for item in fileName[0]['LinkSetDb'][0]['Link']:
                    db.executeCommand(cfg.sqlInsertRel, (addFile['pdbID'], item['Id'], 'Related'))

        db.commit()
    except:
        db.rollback()
        log.error(traceback.format_exc())
        raise Exception('Training Set was not built.')

def retrieve_ligands(cfg,log,db):
    try:
        if cfg.FullReload:
            db.executeCommand(cfg.sqlTruncateLigands)

        structs = db.getData(cfg.sqlSelectCandidates).fetchall()

        for strut in structs:
            json_string = PDB.get_ligands(cfg,strut[0])
            if json_string and json_string['structureId'] and json_string['structureId']['ligandInfo']:
                if type(json_string['structureId']['ligandInfo']['ligand']) == dict:
                    item = json_string['structureId']['ligandInfo']['ligand']
                    db.executeCommand(cfg.sqlInsertLigand,(strut[0], item['@chemicalID'], item['chemicalName'],item['@type'],item['formula'],item['@molecularWeight']))
                else:
                    for item in json_string['structureId']['ligandInfo']['ligand']:
                        db.executeCommand(cfg.sqlInsertLigand,(strut[0], item['@chemicalID'], item['chemicalName'],item['@type'],item['formula'],item['@molecularWeight']))

        db.commit()
    except:
        log.error(traceback.format_exc())
        db.rollback()

def retrieve_go_terms(cfg,log,db):
    try:
        if cfg.FullReload:
            db.executeCommand(cfg.sqlTruncateGoTerms)

        structs = db.getData(cfg.sqlSelectCandidates).fetchall()

        for strut in structs:
            log.info('Getting GO terms for structure %s' % strut[0])
            json_string = PDB.get_go_terms(cfg,strut[0])
            if json_string and json_string['goTerms'] and json_string['goTerms']['term']:
                if type(json_string['goTerms']['term']) == dict:
                    item = json_string['goTerms']['term']
                    if '@synonyms' in json_string['goTerms']['term']:
                        db.executeCommand(cfg.sqlInsertGoTerms,(strut[0], item['@chainId'], item['@id'],item['detail']['@name'],item['detail']['@definition'],item['detail']['@synonyms'],item['detail']['@ontology']))
                    else:
                        db.executeCommand(cfg.sqlInsertGoTerms,(strut[0], item['@chainId'], item['@id'],item['detail']['@name'],item['detail']['@definition'],None,item['detail']['@ontology']))
                else:
                    for item in json_string['goTerms']['term']:
                        if '@synonyms' in json_string['goTerms']['term']:
                            db.executeCommand(cfg.sqlInsertGoTerms,(strut[0], item['@chainId'], item['@id'],item['detail']['@name'],item['detail']['@definition'],item['detail']['@synonyms'],item['detail']['@ontology']))
                        else:
                            db.executeCommand(cfg.sqlInsertGoTerms,(strut[0], item['@chainId'], item['@id'],item['detail']['@name'],item['detail']['@definition'],None,item['detail']['@ontology']))

        db.commit()
    except:
        log.error(traceback.format_exc())

def retrieve_genbank_info(cfg,log,db):
    try:
        structs = db.getData(cfg.sqlSelectCandidates).fetchall()
        html = None
        for item in structs:
            html = None
            try:
                html = PDB.get_genbank_info(cfg,log,item[0])
                tree = ElementTree.fromstring(html)
                gb_sequence = tree.findall('.//GBSeq/GBSeq_sequence')[0].text
                gb_taxonomy = tree.findall('.//GBSeq/GBSeq_taxonomy')[0].text
                gb_seq_length = tree.findall('.//GBSeq/GBSeq_length')[0].text
                gb_seqids = tree.findall('.//GBSeq/GBSeq_other-seqids/GBSeqid')
                gb_gi = None
                for node in gb_seqids:
                    if 'gi|' in node.text:
                        gb_gi = node.text.replace('gi|','')

                db.executeCommand(cfg.sqlUpdateGenBank,(gb_taxonomy, gb_sequence, gb_seq_length, gb_gi, item[0]))
                log.info('Updating information with GenBank data for structure  %s.' % item[0])
            except:
                log.info('No information found on GenBank for structure  %s.' % item[0])
                #if html is not None:
                #    raise
            time.sleep(2)

        db.commit()
    except:
        log.error(traceback.format_exc())

def retrieve_pathways(cfg,log,db):
    try:
        if cfg.FullReload:
            db.executeCommand(cfg.sqlTruncatePathway)

        structs = db.getData(cfg.sqlSelectCandidates).fetchall()
        html = None
        for item in structs:
            log.info('Finding pathway data for structure  %s.' % item[0])
            html = None
            try:
                html = PDB.get_pathways_info(cfg, log, item[1])
                soup = BeautifulSoup(html)
                links = soup.findAll('a')
                for link in  links:
                    if 'href' in link.attrs[0]:
                        if 'show_pathway' in link.attrs[0][1]:
                            db.executeCommand(cfg.sqlInsertPathway,(item[0],cfg.keggRootURL + link.attrs[0][1],link.contents[0]))
            except:
                raise

        db.commit()
    except:
        log.error(traceback.format_exc())

#----------------------------------------------------------------------------------------------------------------------#

def Execute(cfgName):
    returnValue = 0

    print(datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S'))
    print("Loading Configuration... %s" % cfgName)

    fileConfig = labio.configWrapper.load_configuration(cfgName)

    if fileConfig.isLoaded:
        #Initializing the log system
        try:
            nlogging = labio.logWrapper.return_logging(fileConfig.log)
        except:
            returnValue = 1
            print(traceback.format_exc())

        if returnValue == 0:
            try:
                nlogging.info('Starting process...')
                #Connecting to the MySQL database
                db2 = labio.dbWrapper.dbGenericWrapper(fileConfig.database).getDB()
                
                if db2.isDatabaseOpen():
                    nlogging.info('Database opened.')
                    
                    nlogging.info('Starting Integration Objects.')
                    pmed = PubMed(fileConfig,nlogging,db2)

                    if fileConfig.Actions["retrieve_structures"] or fileConfig.RunAll:
                        nlogging.info('Retrieving PDB Structures...')
                        final_list = retrieve_structures(fileConfig,nlogging)
                        if final_list:                      
                            #nlogging.info('Number of structures found: %s' % (len(final_list)))
                            nlogging.info('Adding Candidates to the database...')
                            save_structures(fileConfig,nlogging,db2,final_list)
                        else:
                            nlogging.info('No PDB structures found.')

                    if fileConfig.Actions['retrieve_ligands'] or fileConfig.RunAll:
                        nlogging.info('Finding Ligands...')
                        retrieve_ligands(fileConfig,nlogging,db2)                

                    if fileConfig.Actions['retrieve_go_terms'] or fileConfig.RunAll:
                        nlogging.info('Finding related Gene Ontology terms...')
                        retrieve_go_terms(fileConfig,nlogging,db2)                

                    if fileConfig.Actions['retrieve_genbank_info'] or fileConfig.RunAll:
                        nlogging.info('Finding GenBank Data...')
                        retrieve_genbank_info(fileConfig,nlogging,db2)

                    if fileConfig.Actions['retrieve_pathways'] or fileConfig.RunAll:
                        nlogging.info('Finding Pathways...')
                        retrieve_pathways(fileConfig,nlogging,db2)

                    if fileConfig.Actions['refresh_list'] or fileConfig.RunAll:
                        nlogging.info('Refreshing list of OA articles')
                        pmed.retrieve_file_list()

                    if fileConfig.Actions["build_training_set"] or fileConfig.RunAll:
                        if pmed.is_pubmed_online():
                            nlogging.info('Building Training Set...')
                            build_training_set(fileConfig,nlogging,db2,pmed)
                        else:
                            raise Exception('Pubmed services are not online.')

                    if fileConfig.Actions["search_literature"] or fileConfig.RunAll:
                        if pmed.is_pubmed_online():
                            nlogging.info('Searching articles...')
                            search_literature(fileConfig,nlogging,db2,pmed)
                        else:
                            raise Exception('Pubmed services are not online.')

                    if fileConfig.Actions['rank_literature'] or fileConfig.RunAll:
                        nlogging.info('Ranking articles...')
                        rank_literature(fileConfig,nlogging,db2)
                        
                    if fileConfig.Actions['relate_structures'] or fileConfig.RunAll:
                        nlogging.info('Relating Articles to Structures...')
                        relate_structures(fileConfig,nlogging,db2,pmed)

                    if fileConfig.Actions['Test'] and not(fileConfig.RunAll):
                        pmed = pmed.get_pubmed_article('25714709')
                        print(pmed)
                                                
                    db2.commit()
                    nlogging.info('Database closed.')
                    db2.close()
                else:
                    raise Exception('Database not opened.')

                nlogging.info('Ending process...')
            except:
                returnValue = 1
                nlogging.error('Unexpected error: %s' % traceback.format_exc())
                nlogging.info('Execution aborted due to errors. Please see the log file for more details.')
        else:
            returnValue = 1
    else:
        returnValue = 1

    return returnValue

#----------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':
    exitCode = 0
    try:
        if len(sys.argv) < 2:
             cfgName = sys.argv[0].replace(".py",".config")
             print(cfgName)
        else:
             cfgName = sys.argv[1]

        exitCode = Execute(cfgName)
    except:
        print(traceback.format_exc())
        exitCode = 1

    sys.exit(exitCode)
