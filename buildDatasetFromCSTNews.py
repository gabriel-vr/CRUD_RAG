"""
This script is used to build the database to evaluate the RAG system and the
database to build the vector store from the CSTNews corpus.
"""

"""
There were some modifications i performed in the CSTNews 6.0 folder in order to this script works

Firstly, I am assuming that there is a file in the Sumarios folder corresponding to the text file in the Textos-fonte.
This was not true in two cases: 
    * In C2_Politica_ReeleicaoLula, there was an extra space in the file name
    * In C30_Dinheiro_LucroItau - concordanciaRST, the summaries are divided into versions,
        so i picked the first one and removed the "versao1" from the name

Secondly, the file D2_C3_Estadao_20-07-2007_11h28_sumario_humano.txt had some chars not encoded in utf-8, so i had to correct them mannualy
"""

import os
import re
import random
import json

seed = 10
random.seed(seed)


path = "../CSTNews6.0"
sourceTextDirName = "Textos-fonte"
pathToCSTNewsDataset = "data/CSTNews/"

pathToCSTNewsJson = os.path.join(pathToCSTNewsDataset, "CSTNews.json")

pathToCSTNewsVecStoreFiles = os.path.join(pathToCSTNewsDataset, "vecStoreFiles")

# Reading clusters from the Corpus
clusters = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
clusters = list(filter(
    lambda cluster: re.search(r"For\ all\ the\ clusters", cluster) is None, 
    clusters))


dataset = {
    "event_summary": []
}

filesToUseInVectorStore = []

clusterFiles = {}


#Getting the file names from the clusters
for cluster in clusters:
    pathToTexts = os.path.join(cluster, sourceTextDirName)
    sourceTexts = os.listdir(pathToTexts)
    sourceTexts = map(lambda file: os.path.join(pathToTexts, file), sourceTexts)
                      
    mapTitleToText = {}
    texts = []
    titles = []
    summaries = []

    for text in sourceTexts:
        #This is done to only get files with the corresponding title available
        isTitle = re.search(r"_titulo", text) is not None
        if(isTitle):
            mapTitleToText[text] = text.replace("_titulo", "")
    
    for item, value in mapTitleToText.items():
        texts.append(value)
        titles.append(item)
        summary = item.replace("Textos-fonte", "Sumarios").replace("_titulo", "_sumario_humano")
        summaries.append(summary)

    #We are interested in clusters with more than one text
    if(len(texts) > 1):
        clusterFiles[cluster] = {
            "texts": texts,
            "titles": titles,
            "summaries": summaries
        }
        

#Select one text from the cluster to use as reference summary and the others to compose the vector store
for cluster in clusterFiles:
    nTextsInCluster = len(clusterFiles[cluster]["texts"])
    
    textToUseAsQuery = random.randrange(nTextsInCluster)
    
    textFile = clusterFiles[cluster]["texts"][textToUseAsQuery]
    titleFile = clusterFiles[cluster]["titles"][textToUseAsQuery]
    summaryFile = clusterFiles[cluster]["summaries"][textToUseAsQuery]

    del clusterFiles[cluster]["texts"][textToUseAsQuery]
    del clusterFiles[cluster]["titles"][textToUseAsQuery]
    del clusterFiles[cluster]["summaries"][textToUseAsQuery]

    textInfos = {}
    with open(textFile) as f:
        textInfos["text"] = f.read()
    
    with open(titleFile) as f:
        textInfos["event"] = f.read()
    
    with open(summaryFile) as f:
        textInfos["summary"] = f.read()

    textInfos["ID"] = hash(textInfos["text"])

    dataset["event_summary"].append(textInfos)

    for file in clusterFiles[cluster]["texts"]:
        filesToUseInVectorStore.append(file)


if(not os.path.exists(pathToCSTNewsDataset)):
    os.mkdir(pathToCSTNewsDataset)

with open(pathToCSTNewsJson, "w") as f:
    f.write(json.dumps(dataset, ensure_ascii=False, indent=1))

if(not os.path.exists(pathToCSTNewsVecStoreFiles)):
    os.mkdir(pathToCSTNewsVecStoreFiles)

for file in filesToUseInVectorStore:
    fileName = file.split("/")[-1]
    with open(os.path.join(pathToCSTNewsVecStoreFiles, fileName), "w") as fDest:
        with open(file) as fSrc:
            fDest.write(fSrc.read())
        