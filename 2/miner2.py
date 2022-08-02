from pickle import TRUE
from typing import Counter
from numpy import char
import pandas as pd
import pika, sys, os
import threading
import random
import string
from hashlib import sha1
import time
import json

#from base64 import (b64encode, b64decode)
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA

global arquivo 
arquivo = 'banco-de-dados.csv'

def getTransactionID():
    try:
        df = pd.read_csv(arquivo)
    except:
        df = None
    transactionID = 0
    
    n = 10
    if(df is None):
        lista = {"TransactionID":[0], "Challenge":[random.randint(1,n)], "Seed":[" "], "Winner": [-1]}
        df = pd.DataFrame(lista)
    else:
        tam = len(df.iloc[:, 0])
        if(df.iloc[tam-1, 3] == -1):
            return df.iloc[tam-1, 0]
        else:
            transactionID = df.iloc[(tam-1), 0]+1
            lista = {"TransactionID":transactionID, "Challenge":[random.randint(1,n)], "Seed":[" "], "Winner": [-1]}
            transaction = pd.DataFrame(lista)

            df = pd.concat([df,transaction], ignore_index = True)
    
    df.to_csv(arquivo, index=False)
    
    return int(transactionID)

def getChallenge(transactionID):
    try:
        df = pd.read_csv(arquivo)
    except:
        return -1
    transaction = df.query("TransactionID ==" + str(transactionID))

    if(transaction.empty==False):
        return transaction["Challenge"].values[0]
    else:
        return -1

def verificaSEED(hash, challenger):
            for i in range(0,40):
                ini_string = hash[i]
                scale = 16
                res = bin(int(ini_string, scale)).zfill(4)
                res = str(res)
                for k in range(len(res)):
                    if(res[k] == "b"):
                        res = "0"*(4-len(res[k+1:]))+res[k+1:]
                        break

                for j in range (0, 4):
                    if(challenger == 0):
                        if(res[j] != "0"):
                            return 1
                        else:
                            return -1
                    if(res[j] == "0"):
                        challenger = challenger - 1
                    else:
                        return -1
            return -1

def genereteSignal(message):
    digest = SHA256.new()
    digest.update(message.encode('utf-8'))

    # Load private key previouly generated
    with open ("private_key.pem", "r") as myfile:
        private_key = RSA.importKey(myfile.read())

    # Sign the message
    signer = PKCS1_v1_5.new(private_key)
    sig = signer.sign(digest)

    # sig is bytes object, so convert to hex string.
    # (could convert using b64encode or any number of ways)
    return sig.hex()

def verifySignal(message, sig, public_key):
    digest = SHA256.new()
    digest.update(message.encode('utf-8'))

    sig = bytes.fromhex(sig)  # convert string to bytes object

    # Load public key (not private key) and verify signature
    public_key = RSA.importKey(public_key)
    verifier = PKCS1_v1_5.new(public_key)
    verified = verifier.verify(digest, sig)

    if verified:
        return 1
    else:
        return 0

def main():  
    qtd_usuarios = 2
    usuarios, chaves, eleitos, votacao = [], [], [], []
    nodeID = random.randint(0,2^(32)-1)
    
    def callback(ch, method, properties, body):
        temp = body.decode()
        dic = json.loads(temp)
        
        if(len(usuarios) < qtd_usuarios):
            try:
                if(usuarios.index(temp) >= 0):
                    if(dic["nodeID"] == nodeID):
                        channel.basic_publish(exchange = 'init', routing_key = '', body = temp)
            except:
                usuarios.append(temp)

                #Sala completa
                if(len(usuarios) == qtd_usuarios):
                    public_key = open("public_key.txt")
                    dic = {"nodeID": nodeID, "public_key": public_key.read()}
                    public_key.close()
                    
                    jsonSTR = json.dumps(dic,indent=2)
                    
                    channel.basic_publish(exchange = 'pubkey', routing_key = '', body = jsonSTR)
                    print(usuarios)             
                elif(dic["nodeID"] == nodeID):
                    channel.basic_publish(exchange = 'init', routing_key = '', body = temp)

    def callback1(ch, method, properties, body):
        temp = body.decode()
        dic = json.loads(temp)
        if(len(chaves) < qtd_usuarios):
            try:
                if(chaves.index(temp) >= 0):
                    if(dic["nodeID"] == nodeID):
                        channel.basic_publish(exchange = 'pubkey', routing_key = '', body = temp)
            except:
                chaves.append(temp)

                #Sala completa
                if(len(chaves) == qtd_usuarios):
                    voto = json.loads(random.choice(usuarios))
                    dic = {"nodeID":nodeID,"voto":voto["nodeID"]}

                    
                    jsonSTR = json.dumps(dic,indent=2)
                    sig = genereteSignal(jsonSTR)

                    channel.basic_publish(exchange = 'election', routing_key = '', body = jsonSTR+"/"+sig)
                elif(dic["nodeID"] == nodeID):
                    channel.basic_publish(exchange = 'pubkey', routing_key = '', body = temp)

    def callback2(ch, method, properties, body):
        temp = body.decode()
        
        split = temp.split("/")
        dic = json.loads(split[0])
        
        if(len(eleitos) < qtd_usuarios):
            try:
                if(eleitos.index(split[0]) >= 0):
                    if(dic["nodeID"] == nodeID):
                        channel.basic_publish(exchange = 'election', routing_key = '', body = temp)
            except:
                eleitos.append(split[0])
                #Sala completa
                if(len(eleitos) == qtd_usuarios):
                    #Verifica assinaturas
                    for chave in chaves:
                        chave = json.loads(chave)
                        if(chave["nodeID"] == dic["nodeID"]):
                            if(not verifySignal(split[0], split[1], chave["public_key"])):
                                print("\nLog: \n\t Tentativa de Fraude na votação")
                                eleitos.remove(split[0])
                                break
                    #Eleito
                    chairman = json.loads(Counter(eleitos).most_common(1)[0][0])
                    
                    print("\nLog: \n\tresultado da eleição: participante eleito {}\n".format(chairman["nodeID"]))
                    
                    # verifica se o proprio usuario é o prefeito e publica o challenger gerado
                    if(chairman["nodeID"] == nodeID):
                        trasactionID    = getTransactionID() # Cria a transação
                        challenger      = getChallenge(trasactionID)
                        
                        dic = {"nodeID":nodeID,"challenger":int(challenger)}
                        jsonSTR = json.dumps(dic, indent=2)
                        sig = genereteSignal(jsonSTR)
                        
                        channel.basic_publish(exchange = 'challenge', routing_key = '', body = jsonSTR+"/"+sig)
                elif(dic["nodeID"] == nodeID):
                    channel.basic_publish(exchange = 'election', routing_key = '', body = temp)
                
    def callback3(ch, method, properties, body):
        def setChallenge(challenger):
            transactionID = getTransactionID()
            try:
                df = pd.read_csv(arquivo)
            except:
                return -1
            
            trasition = df.query("TransactionID == "+str(transactionID))    
            
            if(trasition.empty == True):
                return -1
            
            trasition.loc[transactionID,"Challenge"] = challenger
            df.iloc[transactionID,:] = trasition.iloc[0,:]
            
            df.to_csv(arquivo, index=False)
        
        def random_generator(size=6, n=1, chars=string.printable): # Gera string aleatória
            random.seed(n)
            return ''.join(random.choice(chars) for _ in range(size))

        def getSeed(challenger, seed, size): # Gera seed
            n = 0
            while(flag):
                seedTemp = random_generator(size, n)
                texto = str(seedTemp).encode('utf-8')
                hash = sha1(texto).hexdigest()
                
                if(verificaSEED(hash, challenger) == 1):
                    seed.append(seedTemp)
                    break
                n = n + 1
                
        temp = body.decode()
        split = temp.split("/")
        dic = json.loads(split[0])

        #Verifica assinatura do eleito
        chairman = json.loads(Counter(eleitos).most_common(1)[0][0]) 
        if(chairman["nodeID"] != dic["nodeID"]):
            print("\nLog: \n\t Tentativa de Fraude no envio da challenger")
            return
        for chave in chaves:
            chave = json.loads(chave)
            if(chave["nodeID"] == chairman["nodeID"]):
                if(not verifySignal(split[0], split[1], chave["public_key"])):
                    print("\nLog: \n\t Tentativa de Fraude na chave do lider")
                    return
        
        challenger      = dic["challenger"] # Pega challenger anunciado
        setChallenge(challenger)

        # Buscar, localmente, uma seed (semente) que solucione o desafio proposto
        flag = True
        seed, multThread = [], []

        for i in range(1,challenger*2+1):
            thread = threading.Thread(target=getSeed, args=(challenger, seed, i, ))
            multThread.append(thread)
            thread.start()
            
            if(len(seed) > 0):
                flag = False
                break   

        while(True):
            if(len(seed) != 0):
                break

        flag = False

        # Verifica se todas as threads acabaram 
        for thread in multThread:
            thread.join()
        
        #enviar resposta para broker
        dic = {"nodeID":nodeID,"seed":seed[0]}
        jsonSTR = json.dumps(dic, indent=2)
        sig = genereteSignal(jsonSTR)
        
        print(jsonSTR)
        channel.basic_publish(exchange = 'solution', routing_key = '', body = jsonSTR+"/"+sig)
        
    def callback4(ch, method, properties, body):
        def submitChallenge(seed):
            try:
                df = pd.read_csv(arquivo)
            except:
                return -1
            
            transactionID = getTransactionID() 
            trasition = df.query("TransactionID == "+str(transactionID))    
            
            if(trasition.empty == True):
                return -1
            elif(trasition["Winner"].values != -1):
                return 0

            texto = str(seed).encode('utf-8')
            hash = sha1(texto).hexdigest()
            challenge = trasition["Challenge"].values[0]

            if(verificaSEED(hash, challenge) == 1):
                return 1
            else:
                return 0
        
        temp = body.decode()
        split = temp.split("/")
        dic = json.loads(split[0])
        
        #Verifica autênticidade
        for chave in chaves:
            chave = json.loads(chave)
            if(chave["nodeID"] == dic["nodeID"]):
                if(not verifySignal(split[0], split[1], chave["public_key"])):
                    print("\nLog: \n\t Tentativa de Fraude na Seed")
                    return
        
        try:
            df = pd.read_csv(arquivo)
        except:
            return -1 
        
        aux = df.query("TransactionID ==" + str(getTransactionID()))
        print(aux)
        if(aux["Winner"].values[0] == -1):
            voto = False                       # Erro, não resolve desafio ou desafio solucionado
            if(submitChallenge(dic["seed"]) == 1):  # Resolve desafio
                voto = True

            dic = {"nodeID":nodeID,"vote":voto}
            jsonSTR = json.dumps(dic, indent=2)
            sig = genereteSignal(jsonSTR)
            
            channel.basic_publish(exchange = 'voting', routing_key = '', body = jsonSTR+"/"+sig)
        
    def callback5(ch, method, properties, body):
        def verificaVotacao(votacao):
            count = 0
            for voto in votacao:
                if(voto[2]):
                    count = count + 1
            if(count >= qtd_usuarios/2):
                return 1
            return 0
            
        if(len(votacao) != qtd_usuarios):
            votacao.append(body.decode().split("/"))
        if(len(votacao) == qtd_usuarios):
            print(votacao)
            chairman = 0
            if(verificaVotacao(votacao)):
                try:
                    df = pd.read_csv(arquivo)
                except:
                    return -1 
                
                aux = df.query("TransactionID ==" + votacao[0][2])
                if(aux["Winner"].values[0] == -1):
                    transactionID = getTransactionID()
                    
                    trasition = df.query("TransactionID == "+str(transactionID))  
                    
                    trasition.loc[transactionID,"Seed"]   = votacao[0][1]
                    trasition.loc[transactionID,"Winner"] = float(votacao[0][0])
                    
                    df.iloc[transactionID,:] = trasition.iloc[0,:]
                    
                    df.to_csv(arquivo, index=False)
                    chairman = usuarios.index(votacao[0][0])
                else:
                    return
            
            print(chairman)
            channel.queue_purge('ppd/result/'+numero)
            if(usuarios[chairman] == str(id)):
                trasactionID    = getTransactionID()
                challenger      = getChallenge(trasactionID)
                channel.basic_publish(exchange = 'Challenge', routing_key = '', body = str(challenger)+'/'+str(trasactionID))
            
            votacao.clear()
            
    numero = "2"
    
    connection = pika.BlockingConnection(pika.ConnectionParameters(host = 'localhost'))
    channel = connection.channel()

    print(nodeID)

    # Verifica se a lista esta completa
    channel.exchange_declare(exchange='init', exchange_type='fanout')
    init = channel.queue_declare(queue = 'ppd/init/'+numero)                # assina/publica - Sala de Espera
    channel.queue_bind(exchange='init', queue=init.method.queue)

    channel.exchange_declare(exchange='pubkey', exchange_type='fanout')
    pubkey = channel.queue_declare(queue = 'ppd/pubkey/'+numero)            # assina/publica - Eleção do presidente
    channel.queue_bind(exchange='pubkey', queue=pubkey.method.queue)
   
    channel.exchange_declare(exchange='election', exchange_type='fanout')
    election = channel.queue_declare(queue = 'ppd/election/'+numero)        # assina/publica - Eleção do presidente
    channel.queue_bind(exchange='election', queue=election.method.queue)
    
    channel.exchange_declare(exchange='challenge', exchange_type='fanout')
    challenge = channel.queue_declare(queue = 'ppd/challenge/'+numero)      # assina/publica - Desafio da transição atual
    channel.queue_bind(exchange='challenge', queue=challenge.method.queue)

    channel.exchange_declare(exchange='solution', exchange_type='fanout')
    solution = channel.queue_declare(queue = 'ppd/solution/'+numero)        # assina/publica - Verificação da seed que resolve desafio
    channel.queue_bind(exchange='solution', queue=solution.method.queue)

    channel.exchange_declare(exchange='voting', exchange_type='fanout')
    voting = channel.queue_declare(queue = 'ppd/voting/'+numero)            # assina/publica - Lista de votação na seed que soluciona o desafio
    channel.queue_bind(exchange='voting', queue=voting.method.queue)
    
    
    # InitMsg
    dic = {"nodeID": nodeID}
    jsonSTR = json.dumps(dic,indent=2)
    
    channel.basic_consume(queue = 'ppd/init/'+numero , on_message_callback = callback, auto_ack = True)
    channel.basic_publish(exchange = 'init', routing_key = '', body = jsonSTR)

    # PubKeyMsg
    os.system("bash generate_key.sh")
    os.system("python3 0_export_public_key.py")
    
    channel.basic_consume(queue = 'ppd/pubkey/'+numero , on_message_callback = callback1, auto_ack = True)
    
    # ElectionMsg
    channel.basic_consume(queue = 'ppd/election/'+numero , on_message_callback = callback2, auto_ack = True)
    
    # ChallengerMsg
    channel.basic_consume(queue = 'ppd/challenge/'+numero , on_message_callback = callback3, auto_ack = True)
    
    # SolutionMsg
    channel.basic_consume(queue = 'ppd/solution/'+numero , on_message_callback = callback4, auto_ack = True)
    
    # VotingMsg
    #channel.basic_consume(queue = 'ppd/voting/'+numero , on_message_callback = callback5, auto_ack = True)
    
    
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        file = 'banco-de-dados.csv'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        file = 'private_key.pem'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        file = 'public_key.txt'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        print('Interrupted')
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)

#def submitChallenge(transactionID, ClientID, seed):