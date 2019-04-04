import sys
import traceback
import datetime
import time
import os
import urllib as urllib2
import json
import xml2json
import optparse
import requests

from Bio.PDB import *
from pdbextract.Models import *
from prody import *

__html = ''

def execute_advanced_query(log, searchUrl, searchQuery):
    result = None
    try:
        #req = urllib2.Request(searchUrl,data=searchQuery.encode('utf-8'))
        #f = urllib2.urlopen(req)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        result = requests.post(searchUrl,data=searchQuery.encode('utf-8'), headers=headers)
        #f.read().decode('utf-8')

        if result.content:
            log.info("Found number of PDB entries: %s" % (result.content.count('\n')))
        else:
            log.info('No PDB entries found.') 
    except:
        log.error(traceback.format_exc())
    
    return result.content

def merge_results(resultSets):        
    strSet = ""
    firstSet = True
    for item in resultSets:
        if firstSet:
            strSet = "set(" + str(item) + ")"
            firstSet = False
        else:
            strSet = strSet + " & set(" + str(item) + ")"

    return strSet

def parse(cfg,item):
    pdbp = PDBParser()
    struct = pdbp.get_structure(item,os.path.join(cfg.extractFilesFolder,item + ".txt"))
    return struct

def parse_header(cfg,item):
    pdbp = parse(cfg,item)
    header = pdbp.header
    if 'compound' in header.keys():
        if '1' in header['compound'].keys():
            if 'ec_number' in header['compound']['1'].keys():
                pass
            else:
                header['compound']['1']['ec_number'] = None
        else:
            header['compound']['1']['ec_number'] = None
    else:
        header['compound']['1']['ec_number'] = None

    if 'source' in header.keys():
        if '1' in header['source'].keys():
            if 'expression_system' in header['source']['1'].keys():
                pass
            else:
                header['source']['1']['expression_system'] = None
                header['source']['1']['expression_system_taxid'] = None
        else:
            header['source']['1']['expression_system'] = None
            header['source']['1']['expression_system_taxid'] = None
            header['source']['1']['organism_scientific'] = None
            header['source']['1']['organism_taxid'] = None
    else:
        header['source']['1']['expression_system'] = None
        header['source']['1']['expression_system_taxid'] = None
        header['source']['1']['organism_scientific'] = None
        header['source']['1']['organism_taxid'] = None

    return header

def parse_prody(cfg,item):
    f = PdbInfo()
    atoms, header = parsePDB(os.path.join(cfg.extractFilesFolder,item + ".txt"), header=True)
    f.importData(atoms,header)
    return f

def parse_header_prody(cfg,item):
    f = PdbInfo()
    atoms, header = parsePDB(os.path.join(cfg.extractFilesFolder,item + ".txt"), header=True)
    return header

def get_ligands(cfg,item):
    try:
        req = requests.get('http://www.rcsb.org/pdb/rest/ligandInfo?structureId=%s' % item)
        #urllib2.Request('http://www.rcsb.org/pdb/rest/ligandInfo?structureId=%s' % item)
        #f = urllib2.urlopen(req)
        result = req.content #f.read()
        json_string = json.loads(xml2json.xml2json(result, optparse.Values({"pretty": False})))
        return json_string
    except:
        print(traceback.format_exc())
        return None

def get_go_terms(cfg,item):
    try:
        req = requests.get('http://www.rcsb.org/pdb/rest/goTerms?structureId=%s' % item)
        #urllib2.Request('http://www.rcsb.org/pdb/rest/goTerms?structureId=%s' % item)
        #f = urllib2.urlopen(req)
        result = req.content #f.read()
        json_string = json.loads(xml2json.xml2json(result,optparse.Values({"pretty": False}),0))
        return json_string
    except:
        return None

def get_file(cfg,log,item):
    try:
        __html = requests.get(cfg.pdbGetIdURL.format(item))
        f = open(os.path.join(cfg.extractFilesFolder,item + ".txt"), "w")
        f.write(__html.content.decode('utf-8'))
        f.close()
        return True
    except:
        log.error(traceback.format_exc())
        __html = ''
        return False

def get_content():
    return __html

def get_genbank_info(cfg,log,item):
    html = None
    try:
        html = requests.get(cfg.gbGetIdURL.format(item))
        #urllib2.urlopen(cfg.gbGetIdURL.format(item)).read()
        f = open(os.path.join(cfg.extractFilesFolder,item + ".xml"), "w")
        f.write(html.content)
        f.close()
    except:
        log.error(traceback.format_exc())

    return html.content

def get_pathways_info(cfg,log,item):
    html = None
    try:
        html = requests.get(cfg.keggGetURL % item)
        #urllib2.urlopen(cfg.keggGetURL % item).read()
    except:
        log.error(traceback.format_exc())

    return html.content
    
