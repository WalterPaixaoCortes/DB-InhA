# -*- coding: utf-8 -*-
import sys
from prody import *
import traceback

__name__ = "Models"


class Serializer():
    def to_json(self,o):
        return str(self)      

class Journal(Serializer):
    def __init__(self):
        self.publisher = ""
        self.reference = ""
        self.title = ""
        self.issn = ""
        self.editors = []
        self.authors = []
        self.pmid = ""
    
    def __repr__(self):
        return "{'publisher':%r, 'reference':%r, 'title':%r, 'issn':%r, 'pmid':%r, 'editors':[%s], 'authors':[%s]}" % (self.publisher, self.reference, self.title, self.issn, self.pmid, ','.join(str(a) for a in self.editors), ','.join(str(a) for a in self.authors))

class PdbChemical(Serializer):
    def __init__(self):
        self.residueName = ""
        self.chain = ""
        self.residueNumber = 0
        self.insertionCode = ""
        self.numberOfAtoms = 0
        self.description = ""
        self.name = ""
        self.synonyms = []
        self.formula = ""
        self.pdbentry = ""

    def __repr__(self):
        return "{'residueName':%r, 'chain':%r, 'residueNumber':%d, 'insertionCode':%r, 'numberOfAtoms':%d, 'description':%r, 'name':%r', 'pdbentry': %r, 'formula':%r, synonyms':[%s]}" % (self.residueName, self.chain, self.residueNumber, self.insertionCode, self.numberOfAtoms, self.description, self.name, self.pdbentry, self.formula, ','.join(str(a) for a in self.synonyms))

class Compound(Serializer):
    def __init__(self):
        self.name = ""
        self.fragment = ""
        self.engineered = False
        self.mutation = False
        self.chid = ""
        self.synonyms = []
        self.ec = []
        self.seqres = ""
        self.pdbentry = ""
        self.dbrefs = []
        self.seqmod = []

    def __repr__(self):
        return "{'name':%r, 'fragment':%r, 'engineered':%s, 'mutation':%s, 'chid':%r, 'seqres':%r, 'pdbentry': %r, 'synonyms':[%s], 'ec':[%s], 'dbrefs':[%s], 'seqmod':[%s]}" % (self.name, self.fragment, self.engineered, self.mutation, self.chid, self.seqres, self.pdbentry, ','.join(str(a) for a in self.synonyms),','.join(str(a) for a in self.ec),','.join(str(a) for a in self.dbrefs),','.join(str(a) for a in self.seqmod))
        
class DbRef(Serializer):
    def __init__(self):
        self.accession = ""
        self.database = ""
        self.dbabbr = ""
        self.idcode = ""
        self.first = ()
        self.last = ()
        self.diff = []
        
    def __repr__(self):
        return "{'accession':%r, 'database':%r, 'dbabbr':%r, 'idcode':%r, 'first':(%s), 'last':(%s), 'diff':[%s]}" % (self.accession, self.database, self.dbabbr, self.idcode, ','.join(str(a) for a in self.first),','.join(str(a) for a in self.last),','.join(str(a) for a in self.diff))

        
class PdbAtom(Serializer):
    def __init__(self):
        self.serial = 0
        self.name = ""
        self.altloc = ""
        self.resname = ""
        self.chid = ""
        self.resnum = 0
        self.icode = ""
        self.coords = []
        self.occupancy = 0
        self.beta = 0
        self.element = ""
        self.charge = ""
        self.rectype = ""
        self.acsindex = 0

    def __repr__(self):
        return "{'serial':%d, 'name':%r, 'altloc':%r, 'resname':%r, 'chid':%r, 'resnum':%d, 'icode':%r, 'occupancy': %d, 'beta':%d, 'element':%r, 'charge':%r, 'rectype':%r, 'acsindex':%d, 'coords':[%s]}" % (self.serial, self.name, self.altloc, self.resname, self.chid, self.resnum, self.icode, self.occupancy, self.beta, self.element, self.charge, self.rectype, self.acsindex, ','.join(str(a) for a in self.coords))
    
class PdbInfo(Serializer):
    def __init__(self):
        self.status = "Created"
        self.identifier = ""
        self.version = ""
        self.classification = ""
        self.deposition_date = ""
        self.title = ""
        self.resolution = 0
        self.experiment = ""
        self.space_group = ""
        self.authors = []
        self.journal = Journal()
        self.chemicals = []
        self.compounds = []
        self.atomcoords = []

    def __repr__(self):
        return "{'identifier':%r, 'version':%r, 'classification':%r, 'deposition_date':%r, 'title':%r, 'resolution':%d, 'experiment':%r, 'space_group': %r, 'journal':%s, 'authors':[%s], 'chemicals':[%s], 'compounds':[%s], 'atomcoords':[%s]}" % (self.identifier, self.version, self.classification, self.deposition_date, self.title, self.resolution, self.experiment, self.space_group, self.journal, ','.join(str(a) for a in self.authors),','.join(str(a) for a in self.chemicals),','.join(str(a) for a in self.compounds),','.join(str(a) for a in self.atomcoords))

    def isCreated(self):
        return (self.status == "Created")

    def importData(self, atoms, header):
        #self.status = 'Not Imported'
        try:
            if self.isCreated() and 'identifier' in header:
                self.identifier = header["identifier"]
                self.version = header["version"]
                self.classification = header["classification"]
                self.deposition_date = header["deposition_date"]
                self.title = header["title"]
                self.resolution = header["resolution"]
                self.experiment = header["experiment"]
                self.space_group = header["space_group"]
                
                if header["authors"]:
                    self.authors.extend(header["authors"])
                    
                self.journal.publisher = header["reference"]["publisher"]
                self.journal.reference = header["reference"]["reference"]
                self.journal.title = header["reference"]["title"]
                
                if header["reference"]["editors"]:
                    self.journal.editors.extend(header["reference"]["editors"])
                
                if header["reference"]["authors"]:
                    self.journal.authors.extend(header["reference"]["authors"])
                
                if 'issn' in header["reference"]:
                    self.journal.issn = header["reference"]["issn"]

                if "pmid" in header["reference"]:
                    self.journal.pmid = header["reference"]["pmid"]
                
                if header["chemicals"]:
                    for chem_item in header["chemicals"]:
                        item = PdbChemical()
                        item.residueName = chem_item.resname
                        item.residueNumber = chem_item.resnum
                        item.name = chem_item.name
                        item.chain = chem_item.chain
                        item.insertionCode = chem_item.icode
                        item.numberOfAtoms = chem_item.natoms
                        item.description = chem_item.description
                        
                        if chem_item.synonyms:
                            item.synonyms.extend(chem_item.synonyms)
        
                        item.formula = chem_item.formula
                        item.pdbentry = chem_item.pdbentry
                        self.chemicals.append(item)
                    
                if header["polymers"]:
                    for pol_item in header["polymers"]:
                        itemC = Compound()
                        itemC.chid = pol_item.chid
                        itemC.fragment = pol_item.fragment
                        itemC.name = pol_item.name
                        itemC.pdbentry = pol_item.pdbentry
                        itemC.seqres = pol_item.sequence
                        
                        if pol_item.synonyms:
                            itemC.synonyms.extend(pol_item.synonyms)
                            
                        if pol_item.modified:
                            itemC.seqmod.extend(pol_item.modified)
                        
                        itemC.engineered = pol_item.engineered
                        itemC.mutation = pol_item.mutation
                        
                        if pol_item.ec:
                            itemC.ec.extend(pol_item.ec)
                            
                        if pol_item.dbrefs:
                            for db_item in pol_item.dbrefs:
                                itemD = DbRef()
                                itemD.accession = db_item.accession
                                itemD.database = db_item.database
                                itemD.dbabbr = db_item.dbabbr
                                itemD.idcode = db_item.idcode
                                itemD.first = db_item.first
                                itemD.last = db_item.last
                                
                                if db_item.diff:
                                    itemD.diff.extend(db_item.diff)
                                    
                                itemC.dbrefs.append(itemD)
                                
                        self.compounds.append(itemC)
                        
                if atoms:
                    for itemA in iter(atoms):
                        at = PdbAtom()
                        at.acsindex = itemA.getACSIndex()
                        at.serial = itemA.getSerial()
                        at.name = itemA.getName()
                        at.altloc = itemA.getAltloc()
                        at.resname = itemA.getResname()
                        at.chid = itemA.getChid()
                        at.resnum = itemA.getResnum()
                        at.icode = itemA.getIcode()
                        at.coords = itemA.getCoords()
                        at.occupancy = itemA.getOccupancy()
                        at.beta = itemA.getBeta()
                        at.element = itemA.getElement()
                        at.charge = itemA.getCharge()
                        
                        if at.resname in ('NAD','HOH'):
                            at.rectype = 'HETATM'
                        else:
                            at.rectype = 'ATOM'
                            
                        self.atomcoords.append(at)
                    
                self.status = "Imported"
        except:
            self.status = 'Not Imported'
            print(traceback.format_exc())