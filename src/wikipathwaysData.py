import urllib.request as RE
import libchebipy
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ElementTree
import os
import zipfile
import time
from MetabolomicsData import MetabolomicsData

class wikipathwaysData(MetabolomicsData):
    
    '''
    The wikipathwaysData class actually gets information from wikipathways via number of xml files called gpml files. Each file represents 
    a biochemical pathway composed of metabolite and gene interactions. As a result, metabolites and genes can  be linked to pathways.
    
    The wikipathways files can be downloaded here: http://www.wikipathways.org/index.php/Download_Pathways​
    The reactome files can be downloaded here: http://www.wikipathways.org/index.php/Download_Pathways​
    
    The files have already been downloaded and placed in this package. The path to the files has been hardcoded into the function calls.
    
    This class only has two functions:
    
        - 1) getEverything
        - 2) writeToFiles
        
    Due to the nature of the structure of this database (a series of xml files) it makes more sense to get all the information at one time 
    from one function call and then, as in the other classes, write everything to sqls for the RaMP database. 
    
    
    
    '''
    
    def __init__(self):
        
        super().__init__()
        # key: ID for metabolites Value: Common Name (the only name in this database)
        self.metaboliteCommonName = dict()
        #key: ID for pathway, Value: pathway name
        self.pathwayDictionary = dict()
        
        #key: ID for pathway, category: various categories such as cellular process, metabolic process 
        self.pathwayCategory = dict()
        
        #key: gene, value: gene mapping
        self.geneInfoDictionary = dict()
        
        #key: metabolite, value: metabolite mapping
        self.metaboliteIDDictionary = dict()
        
        #key: pathwayID, value: list of genes
        self.pathwaysWithGenesDictionary = dict()
        
        #key: pathwayId, value: list of metabolites
        self.pathwayWithMetabolitesDictionary = dict()
        
        #empty for reactome
        self.metabolitesWithSynonymsDictionary = dict()
        
        #only not empty when a catalyzed class exists 
        #empty
        self.metabolitesLinkedToGenes = dict()
        
        #key: metabolite, value: list of pathways
        self.metabolitesWithPathwaysDictionary = dict()
        
        #key: current pathway, value: list of pathways linked to this pathway
        self.pathwayOntology = dict()
        
        #stays empty for this class
        self.biofluidLocation = dict()
        
        #stays empty for this class
        self.biofluid = dict()
        
        #stays empty for this class
        self.cellularLocation = dict()
        
        #stays empty for this class
        self.cellular = dict()
        
        #stays empty
        self.exoEndoDictionary = dict()
        self.exoEndo =dict()
        #tissue location stay empty
        self.tissue = dict()
        self.tissueLocation = dict()
        # show how id distributes
        # key database value: frequency
        
        self.metaboliteFromWhichDB = {
                                      "kegg_id":0,
                                      "hmdb_id":0,
                                      "CAS":0,
                                      "chebi_id":0,
                                      "pubchem_compound_id":0,
                                      "chemspider_id":0
                                      }

        self.setOfType = set()
        self.idSetFromGeneProducts = dict()
        self.idSetFromProtein = dict()
    def getDatabaseFiles(self):
        
        '''
        This function gets the files that make up wikipathways and place them to wikipathways folder.
        
        The data file is stored in the url: data.wikipathways.org/ in the order of published date
        
        '''
        
        path = "../misc/data/wikipathways/"
        url = "http://data.wikipathways.org/20180110/gpml/wikipathways-20180110-gpml-Homo_sapiens.zip"
        file = "wikipathways-20180110-gpml-Homo_sapiens.zip"
        existed = os.listdir(path)
        if self.check_path(path) and file not in existed:
            self.download_files(url, 
                                path+file)
            
            with zipfile.ZipFile(path + file,"r") as zip_ref:
                zip_ref.extractall(path)
        else:
            print("Already Downloaded ....")
        
        
    def getEverything(self):
        
        ''' This function gets all the necessary information from the gpml files and places it into dictionaries. 
        Unlike in other classes, only one function is required to get all the necessary information.
        The update date needs to be hardcoded to the url.
        Please make sure going to the website to see which one is the latest version for 
        wikipathways data.
        '''
        
        print("Call wikipathways getEverything......")  
        pathwikipathways = "../misc/data/wikipathways/"
      
        dictionaryOfFiles = dict()
        
        for filename in os.listdir(pathwikipathways):
            if ".zip" in filename:
                continue  # the original downloaded file is also in same path
                          # and not parsed to the later process
            fullpath = pathwikipathways + filename
            dictionaryOfFiles[fullpath] = "wikipathways"
          
        print("done ... for input files name.")  
        for filename in dictionaryOfFiles:
          
            tree = ET.parse(filename)
          
              
            root = tree.getroot()

           
            #how to get the pathwayID from filename
            last = filename.rfind('_')
            first = filename[:last].rfind('_')
            pathwayID = filename[first+1:last]
          
          
            #this keeps track of the current pathway. 
            #this is important later for placing pathways into the metaboliteswithpathways dictionary 
            currentpathway = pathwayID
          

          
          
            listOfGenes = []
            listOfMetabolites = []
            listOfPathwaysForOntology = []
          
            pathwayname = root.get("Name")
            self.pathwayDictionary[pathwayID] = pathwayname
          
            for child in root:
                childtag = child.tag.replace("{http://pathvisio.org/GPML/2013a}", "")
             
                if childtag == "Comment":
                    if child.get("Source") == "WikiPathways-category":
                        category = child.text
                        self.pathwayCategory[pathwayID] = category
                  
                #if a pathway category has not been found by this point defualt to NA
                if pathwayID not in self.pathwayCategory:
                    self.pathwayCategory[pathwayID] = "NA"
                      
                if childtag == "DataNode":
                    metaboliteorgene = child.get("TextLabel")
                    Attributetype = child.get("Type")
                  # child = DataNode
                  # child2 = Graphics or Xref
                    
                    for child2 in child:
                      
                        childtag = child2.tag
                        childtag = child2.tag.replace("{http://pathvisio.org/GPML/2013a}", "")
                        if childtag == "Xref":
                            database = child2.get("Database")
                            databaseID = child2.get("ID")
                            if Attributetype not in self.setOfType:
                                self.setOfType.add(Attributetype)
                            if Attributetype == "Protein":
                                geneMapping = {"kegg": "NA",
                                             "common_name": "NA",
                                             "Ensembl": "NA", 
                                             "HGNC": "NA", 
                                             "HPRD": "NA", 
                                             "NCBI-GeneID": "NA", 
                                             "NCBI-ProteinID": "NA", 
                                             "OMIM": "NA", 
                                             "UniProt": "NA", 
                                             "Vega": "NA", 
                                             "miRBase": "NA", 
                                             "HMDB_protein_accession": "NA",
                                             "Entrez" : "NA",
                                             "Enzyme Nomenclature": "NA"}
                                for key in geneMapping:
                                    geneMapping["common_name"] = metaboliteorgene
                                  
                                    if databaseID is not "" and database == "Entrez Gene": 
                                        geneMapping["Entrez"] = databaseID
                                    if databaseID not in listOfGenes:
                                        listOfGenes.append(databaseID)
                                      
                                      
                                    if databaseID is not "" and database == "Enzyme Nomenclature": 
                                        geneMapping["Enzyme Nomenclature"] = databaseID
                                        if databaseID not in listOfGenes:
                                            listOfGenes.append(databaseID)
                                      
                                      
                                    if databaseID is not "" and database == "Enzyme Nomenclature": 
                                        geneMapping["Ensembl"] = [databaseID]
                                        if databaseID not in listOfGenes:
                                            listOfGenes.append(databaseID)
                                      
                                      
                                    if databaseID is not "" and database == "Uniprot-TrEMBL": 
                                        geneMapping["UniProt"] = [databaseID]
                                        if databaseID not in listOfGenes:
                                            listOfGenes.append(databaseID)
                                
                                self.geneInfoDictionary[databaseID] = geneMapping
                            if Attributetype == "GeneProduct":
                                if database not in self.idSetFromGeneProducts:
                                    self.idSetFromGeneProducts[database] = set()
                                  
                                    self.idSetFromGeneProducts[database].add(databaseID)
                                geneMapping = {"kegg": "NA",
                                             "common_name": "NA",
                                             "Ensembl": "NA", 
                                             "HGNC": "NA", 
                                             "HPRD": "NA", 
                                             "NCBI-GeneID": "NA", 
                                             "NCBI-ProteinID": "NA", 
                                             "OMIM": "NA", 
                                             "UniProt": "NA", 
                                             "Vega": "NA", 
                                             "miRBase": "NA", 
                                             "HMDB_protein_accession": "NA",
                                             "Entrez" : "NA",
                                             "Enzyme Nomenclature": "NA"}
                                for key in geneMapping:
                                    geneMapping["common_name"] = metaboliteorgene
                                  
                                    if databaseID is not "" and database == "Entrez Gene": 
                                        geneMapping["Entrez"] = databaseID
                                    if databaseID not in listOfGenes:
                                        listOfGenes.append(databaseID)
                                      
                                      
                                    if databaseID is not "" and database == "Enzyme Nomenclature": 
                                        geneMapping["Enzyme Nomenclature"] = databaseID
                                        if databaseID not in listOfGenes:
                                            listOfGenes.append(databaseID)
                                      
                                      
                                    if databaseID is not "" and database == "Enzyme Nomenclature": 
                                        geneMapping["Ensembl"] = [databaseID]
                                        if databaseID not in listOfGenes:
                                            listOfGenes.append(databaseID)
                                      
                                      
                                    if databaseID is not "" and database == "Uniprot-TrEMBL": 
                                        geneMapping["UniProt"] = [databaseID]
                                        if databaseID not in listOfGenes:
                                            listOfGenes.append(databaseID)
                                self.geneInfoDictionary[databaseID] = geneMapping
                                      
                              
                                  
                              
                             
                              
                              
                          
                            if Attributetype == "Metabolite":
                              
                                metaboliteMapping = {
                                  "chebi_id": "NA", 
                                  "drugbank_id": "NA", 
                                  "drugbank_metabolite_id": "NA", 
                                  "phenol_explorer_compound_id": "NA", 
                                  "phenol_explorer_metabolite_id": "NA", 
                                  "foodb_id": "NA", 
                                  "knapsack_id": "NA", 
                                  "chemspider_id": "NA",
                                  "kegg_id": "NA",
                                  "biocyc_id": "NA",
                                  "bigg_id": "NA",
                                  "wikipidia": "NA",
                                  "nugowiki": "NA",
                                  "metagene": "NA",
                                  "metlin_id": "NA",
                                  "pubchem_compound_id": "NA",
                                  "het_id": "NA",
                                  "hmdb_id": "NA",
                                  "CAS": "NA"}
                              
                              
                                if database == "HMDB":
                                    # databaseID is the source ID 
                                    databaseID = databaseID.replace("HMDB","HMDB00")
                                    metaboliteMapping["hmdb_id"] = [databaseID]
                                    self.metaboliteIDDictionary[databaseID] = metaboliteMapping
                                    self.metaboliteCommonName[databaseID] = metaboliteorgene
                                    if databaseID not in listOfMetabolites:
                                        listOfMetabolites.append(databaseID)
                                        self.metaboliteFromWhichDB["hmdb_id"] +=1
                                
                                    self.metabolitesWithSynonymsDictionary[databaseID] = [metaboliteorgene]
                                  
                                  
                                if database == "CAS":
                                    metaboliteMapping["CAS"] = databaseID
                                    self.metaboliteIDDictionary[databaseID] = metaboliteMapping
                                  
                                    if databaseID not in listOfMetabolites:
                                        listOfMetabolites.append(databaseID)
                                        self.metaboliteFromWhichDB["CAS"] +=1
                                    self.metabolitesWithSynonymsDictionary[databaseID] = [metaboliteorgene]
                                    self.metaboliteCommonName[databaseID] = metaboliteorgene

                                  
                                if database == "ChEBI":
                                    #remove prefix
                                    databaseID = databaseID.replace("CHEBI:", "")
                                    #kegg makes a list of chebi ids since there are more than one. For consistency, and so both databases
                                    #can use the ID conversion class, we will also make a list of chebi ids here
                                    metaboliteMapping["chebi_id"] = [databaseID]
                                    self.metaboliteIDDictionary[databaseID] = metaboliteMapping
                                    self.metaboliteCommonName[databaseID] = metaboliteorgene

                                    if databaseID not in listOfMetabolites:
                                        listOfMetabolites.append(databaseID)
                                        self.metaboliteFromWhichDB["chebi_id"] += 1
                                      
                                    self.metabolitesWithSynonymsDictionary[databaseID] = [metaboliteorgene]
                                  
                                if database == "KEGG Compound":
                                    metaboliteMapping["kegg_id"] = databaseID
                                    self.metaboliteIDDictionary[databaseID] = metaboliteMapping
                                    self.metaboliteCommonName[databaseID] = metaboliteorgene

                                    if databaseID not in listOfMetabolites:
                                        listOfMetabolites.append(databaseID)
                                        self.metaboliteFromWhichDB["kegg_id"] += 1
                                    self.metabolitesWithSynonymsDictionary[databaseID] = [metaboliteorgene]
                                  
                                if database == "PubChem-compound":
                                    metaboliteMapping["pubchem_compound_id"] = databaseID
                                    self.metaboliteIDDictionary[databaseID] = metaboliteMapping
                                    self.metaboliteCommonName[databaseID] = metaboliteorgene

                                    if databaseID not in listOfMetabolites:
                                        listOfMetabolites.append(databaseID)
                                        self.metaboliteFromWhichDB["pubchem_compound_id"] += 1
                                    self.metabolitesWithSynonymsDictionary[databaseID] = [metaboliteorgene]
                                  
                                if databaseID is not "" and database == "Chemspider": 
                                    metaboliteMapping["chemspider_id"] = databaseID
                                    self.metaboliteIDDictionary[databaseID] = metaboliteMapping
                                    self.metaboliteCommonName[databaseID] = metaboliteorgene

                                    if databaseID not in listOfMetabolites:
                                        listOfMetabolites.append(databaseID)
                                        self.metaboliteFromWhichDB["chemspider_id"] += 1
                                      
                                    self.metabolitesWithSynonymsDictionary[databaseID] = [metaboliteorgene]
                                      
                                if database == "PubChem-substance":
                                    metaboliteMapping["pubchem_compound_id"] = databaseID
                                    self.metaboliteIDDictionary[databaseID] = metaboliteMapping
                                    self.metaboliteCommonName[databaseID] = metaboliteorgene

                                    if databaseID not in listOfMetabolites:
                                        listOfMetabolites.append(databaseID)
                                        self.metaboliteFromWhichDB["pubchem_compound_id"] +=1
                                      
                                    self.metabolitesWithSynonymsDictionary[databaseID] = [metaboliteorgene]
                              
                              
                            
                              
                              
                              
                              
                                if databaseID not in self.metabolitesWithPathwaysDictionary:
                                    listOfPathways = []
                                    listOfPathways.append(pathwayID)
                                    if database in ["HMDB", "CAS", "ChEBI", "KEGG Compound", "PubChem-compound", "Chemspider", "PubChem-substance"]:
                                        if database == "HMDB":
                                            databaseID = databaseID.replace("HMDB","HMDB00")
                                        self.metabolitesWithPathwaysDictionary[databaseID] = listOfPathways
                                        currentpathway = pathwayID
                                  
                                #this is what should happen if the metabolite has already been seen but we are on a NEW pathway file. If it is the same 
                                #pathway file it will not be recorded again.     
                                elif currentpathway != pathwayID:
                                   
                                    value = self.metabolitesWithPathwaysDictionary[databaseID]
                                    value = value.append(pathwayID)
                                    if database in ["HMDB", "CAS", "ChEBI", "KEGG Compound", "PubChem-compound", "Chemspider", "PubChem-substance"]:
                                        self.metabolitesWithPathwaysDictionary[databaseID] = listOfPathways
                                    self.metabolitesWithPathwaysDictionary[databaseID] = value
                                  
                            if Attributetype == "Pathway":
                                if database == "WikiPathways":
                                    listOfPathwaysForOntology.append(databaseID) 
          
            self.pathwayOntology[pathwayID] = listOfPathwaysForOntology        
            self.pathwaysWithGenesDictionary[pathwayID] = listOfGenes
            self.pathwayWithMetabolitesDictionary[pathwayID] = listOfMetabolites
     
     
    def getCommonNameForChebi(self):
        
        for key in self.metaboliteIDDictionary:
            value = self.metaboliteIDDictionary[key]
            chebi = value["chebi_id"]
            name = "NA"
            for each in chebi:
                try:
                    chebiToSearch = str(each)
                    chebiToSearch2 = libchebipy.ChebiEntity(chebiToSearch)
                    name = chebiToSearch2.get_name()
                    print(chebiToSearch)
                    print(name)
                    #time.sleep(3)
                except:
                    pass
            self.metabolitesWithSynonymsDictionary[key] = [name]     
          

                