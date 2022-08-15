from typing import Counter
from hashlib import sha1
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from Crypto.PublicKey import RSA

import pandas as pd

import pika, sys, os, threading
import string, json
import random, time

global arquivo 
arquivo = 'output/banco-de-dados.csv'

def getTransactionID(create = False):
    try:
        df = pd.read_csv(arquivo)
    except:
        df = None
    transactionID = 0
    
    a = 18
    b = 20
    if(df is None):
        lista = {"TransactionID":[0], "Challenge":[random.randint(a,b+1)], "Seed":[" "], "Winner": [-1]}
        df = pd.DataFrame(lista)
    else:
        tam = len(df.iloc[:, 0])
        if(df.iloc[tam-1, 3] == -1):
            return df.iloc[tam-1, 0]
        elif(create):
            transactionID = df.iloc[(tam-1), 0]+1
            lista = {"TransactionID":transactionID, "Challenge":[random.randint(a,b+1)], "Seed":[" "], "Winner": [-1]}
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
    n = int(challenger/4)
    p = challenger - 4*n
    
    if(hash[:n] == "0"*n):
        res = str(bin(int(hash[n], 16)).zfill(4))
        
        for k in range(len(res)):
            if(res[k] == "b"):
                res = "0"*(4-len(res[k+1:]))+res[k+1:]
                break       
        if(res[:p] == "0"*p and res[p] != "0"):
            return 1
    return 0

def genereteSignal(message):
    digest = SHA256.new()
    digest.update(message.encode('utf-8'))

    # Load private key previouly generated
    with open ("chaves/private_key.pem", "r") as myfile:
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
    qtd_usuarios = int(input("Informe a quantidade de usuarios: "))
    usuarios, chaves, eleitos, votacao = [], [], [], []
    
    random.seed(random.randint(0,2^(32)-1))
    nodeID = random.randint(0,2^(32)-1)
    
    numero = str(nodeID)
    
    def callback(ch, method, properties, body):
        temp = body.decode()
        dic = json.loads(temp)
        
        if(len(usuarios) < qtd_usuarios):
            try:
                if(usuarios.index(temp) >= 0):
                    if(dic["NodeId"] == nodeID):
                        channel.basic_publish(exchange = 'ppd/init', routing_key = '', body = temp)
                        time.sleep(1)
            except:
                usuarios.append(temp)

            #Sala completa
            if(len(usuarios) == qtd_usuarios):
                public_key = open("chaves/public_key.txt")
                dic = {"NodeId": nodeID, "PubKey": public_key.read()}
                public_key.close()
                
                jsonSTR = json.dumps(dic,indent=2)
                
                channel.basic_publish(exchange = 'ppd/pubkey', routing_key = '', body = jsonSTR)
                print(usuarios)             
            elif(dic["NodeId"] == nodeID):
                channel.basic_publish(exchange = 'ppd/init', routing_key = '', body = temp)
                time.sleep(1)

    def callback1(ch, method, properties, body):
        try:
            if(usuarios.index(json.dumps({"NodeId": nodeID},indent=2)) >= 0):
                pass
        except:
            sys.exit(0)
        
        temp = body.decode()
        dic = json.loads(temp)
        if(len(chaves) < qtd_usuarios):
            try:
                if(chaves.index(temp) >= 0):
                    if(dic["NodeId"] == nodeID):
                        channel.basic_publish(exchange = 'ppd/pubkey', routing_key = '', body = temp)
                        time.sleep(1)
            except:
                chaves.append(temp)

            #Sala completa
            if(len(chaves) == qtd_usuarios):
                voto = json.loads(random.choice(usuarios))
                dic = {"NodeId":nodeID,"ElectionNumber":int(voto["NodeId"])}

                
                jsonSTR = json.dumps(dic,indent=2)
                sig = genereteSignal(jsonSTR)
                
                dic.update({"Sign":sig})
                jsonSTR = json.dumps(dic,indent=2)
                
                channel.basic_publish(exchange = 'ppd/election', routing_key = '', body = jsonSTR)
            elif(dic["NodeId"] == nodeID):
                channel.basic_publish(exchange = 'ppd/pubkey', routing_key = '', body = temp)
                time.sleep(1)

    def callback2(ch, method, properties, body): 
        def getCherman(eleitos):
            eleitos = [json.loads(aux)["NodeId"] for aux in eleitos]
            chairman = Counter(eleitos)
            print(chairman)
            chairman = chairman.most_common(1)[0][0]
            print(chairman)
            return chairman                   
        temp = body.decode()
        dic = json.loads(temp)
        sig = dic.pop("Sign")
        
        if(len(eleitos) < qtd_usuarios):
            try:
                if(eleitos.index(temp) >= 0):
                    if(dic["NodeId"] == nodeID):
                        channel.basic_publish(exchange = 'ppd/election', routing_key = '', body = temp)
                        time.sleep(1)
            except:
                #Verifica assinaturas
                for chave in chaves:
                    chave = json.loads(chave)
                    if(chave["NodeId"] == dic["NodeId"]):
                        if(not verifySignal(json.dumps(dic,indent=2), sig, chave["PubKey"])):
                            print("\nLog: \n\t Tentativa de fraude na eleição")
                        else:
                            eleitos.append(temp)
            
            #Sala completa
            if(len(eleitos) == qtd_usuarios):
                #Eleito
                chairman = getCherman(eleitos)
                
                print("\nLog: \n\tresultado da eleição: participante eleito {}\n".format(chairman))
                votacao.clear()
                
                # verifica se o proprio usuario é o prefeito e publica o challenger gerado
                if(chairman == nodeID):
                    trasactionID    = getTransactionID(True) # Cria a transação
                    challenger      = getChallenge(trasactionID)
                    
                    dic = {"NodeId":nodeID, "TransactionNumber":int(getTransactionID()),"Challenge":int(challenger)}
                    jsonSTR = json.dumps(dic, indent=2)
                    
                    sig = genereteSignal(jsonSTR)
                    
                    dic.update({"Sign":sig})
                    jsonSTR = json.dumps(dic,indent=2)
                    
                    channel.basic_publish(exchange = 'ppd/challenge', routing_key = '', body = jsonSTR)
                    
            elif(dic["NodeId"] == nodeID):
                channel.basic_publish(exchange = 'ppd/election', routing_key = '', body = temp)
                time.sleep(1)
                
    def callback3(ch, method, properties, body):
        def setChallenge(challenger):
            transactionID = getTransactionID(True)
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
        
        def random_generator(size=6, n=1, chars=string.ascii_letters+string.punctuation+string.digits): # Gera string aleatória
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
        dic = json.loads(temp)
        sig = dic.pop("Sign")
        
        #Verifica assinatura do eleito
        chairman = json.loads(Counter(eleitos).most_common(1)[0][0]) 
        if(chairman["NodeId"] != dic["NodeId"]):
            print("\nLog: \n\t Tentativa de fraude no envio da challenger")
            return
        for chave in chaves:
            chave = json.loads(chave)
            if(chave["NodeId"] == chairman["NodeId"]):
                if(not verifySignal(json.dumps(dic,indent=2), sig, chave["PubKey"])):
                    print("\nLog: \n\t Tentativa de fraude na chave do lider")
                    return
        
        challenger      = dic["Challenge"] # Pega challenger anunciado
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
        dic = {"NodeId":nodeID, "TransactionNumber":int(getTransactionID()), "Seed":seed[0]}
        jsonSTR = json.dumps(dic, indent=2)
        sig = genereteSignal(jsonSTR)
        
        dic.update({"Sign":sig})
        jsonSTR = json.dumps(dic,indent=0)
        
        channel.basic_publish(exchange = 'ppd/solution', routing_key = '', body = jsonSTR)
        
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
        dic = json.loads(temp)
        sig = dic.pop("Sign")
        
        #Verifica autênticidade
        for chave in chaves:
            chave = json.loads(chave)
            if(chave["NodeId"] == dic["NodeId"]):
                if(not verifySignal(json.dumps(dic,indent=2), sig, chave["PubKey"])):
                    print("\nLog: \n\t Tentativa de Fraude na Seed")
                    return
        
        try:
            df = pd.read_csv(arquivo)
        except:
            return -1 
        
        aux = df.query("TransactionID ==" + str(getTransactionID()))
        if(aux["Winner"].values[0] == -1):
            voto = False                            # Erro, não resolve desafio ou desafio solucionado
            if(submitChallenge(dic["Seed"]) == 1):  # Resolve desafio
                voto = True

            arq = open("seed.txt", "a")
            arq.write(str(dic["NodeId"])+"\t"+dic["Seed"]+"\n")
            arq.close()
            
            dic = {"NodeId":nodeID, "SolutionID":dic["NodeId"], "TransactionNumber":int(getTransactionID()), "Seed":dic["Seed"], "Vote":voto}
            jsonSTR = json.dumps(dic, indent=2)
            sig = genereteSignal(jsonSTR)
            
            dic.update({"Sign":sig})
            jsonSTR = json.dumps(dic,indent=2)
        
            channel.basic_publish(exchange = 'ppd/voting', routing_key = '', body = jsonSTR)  
        
    def callback5(ch, method, properties, body):
        def verificaVotacao(votacao):
            count = 0
            for voto in votacao:
                if(voto[2]):
                    count = count + 1
            if(count >= qtd_usuarios/2):
                return 1
            return 0
        
        temp = body.decode()
        dic = json.loads(temp)
        sig = dic.pop("Sign")
        
        try:
            df = pd.read_csv(arquivo)
        except:
            return -1 
        aux = df.query("TransactionID ==" + str(getTransactionID()))
        if(len(votacao) < qtd_usuarios and aux["Winner"].values[0] == -1):
            try:
                if(votacao.index(temp) >= 0):
                    pass
            except:
                #Verifica autênticidade
                for chave in chaves:
                    chave = json.loads(chave)
                    if(chave["NodeId"] == dic["NodeId"]):
                        if(not verifySignal(json.dumps(dic,indent=2), sig, chave["PubKey"])):
                            print("\nLog: \n\t Tentativa de Fraude na Votação")
                        else:
                            votacao.append(temp)
            
            if(len(votacao) == qtd_usuarios):
                arq = open("seed.txt", "r")
                split = arq.read().split("\n")
                arq.close()
                if(verificaVotacao(votacao)):
                    dic = split[0].split("\t")
                    
                    aux.loc[getTransactionID(),"Seed"]   = dic[1]
                    aux.loc[getTransactionID(),"Winner"] = int(dic[0])
                    
                    df.iloc[getTransactionID(),:] = aux.iloc[0,:]
                    
                    df.to_csv(arquivo, index=False)
                    
                    eleitos.clear()
                    
                    voto = json.loads(random.choice(usuarios))
                    
                    dic = {"NodeId":nodeID,"ElectionNumber":voto["NodeId"]}                    
                    jsonSTR = json.dumps(dic,indent=2)
                    sig = genereteSignal(jsonSTR)
                    
                    dic.update({"Sign":sig})
                    jsonSTR = json.dumps(dic,indent=2)

                    channel.basic_publish(exchange = 'ppd/election', routing_key = '', body = jsonSTR)
                    
                    os.remove("seed.txt")
                else:
                    arq = open("seed.txt", "w")
                    arq.write("/".join(split[1:]))
                    arq.close()
                            
    connection = pika.BlockingConnection(pika.ConnectionParameters(host = 'localhost'))
    channel = connection.channel()

    print(nodeID)

    # Verifica se a lista esta completa
    channel.exchange_declare(exchange='ppd/init', exchange_type='fanout')
    init = channel.queue_declare(queue = 'ppd/init/'+numero)                # assina/publica - Sala de Espera
    channel.queue_bind(exchange='ppd/init', queue=init.method.queue)

    channel.exchange_declare(exchange='ppd/pubkey', exchange_type='fanout')
    pubkey = channel.queue_declare(queue = 'ppd/pubkey/'+numero)            # assina/publica - Eleção do presidente
    channel.queue_bind(exchange='ppd/pubkey', queue=pubkey.method.queue)
   
    channel.exchange_declare(exchange='ppd/election', exchange_type='fanout')
    election = channel.queue_declare(queue = 'ppd/election/'+numero)        # assina/publica - Eleção do presidente
    channel.queue_bind(exchange='ppd/election', queue=election.method.queue)
    
    channel.exchange_declare(exchange='ppd/challenge', exchange_type='fanout')
    challenge = channel.queue_declare(queue = 'ppd/challenge/'+numero)      # assina/publica - Desafio da transição atual
    channel.queue_bind(exchange='ppd/challenge', queue=challenge.method.queue)

    channel.exchange_declare(exchange='ppd/solution', exchange_type='fanout')
    solution = channel.queue_declare(queue = 'ppd/solution/'+numero)        # assina/publica - Verificação da seed que resolve desafio
    channel.queue_bind(exchange='ppd/solution', queue=solution.method.queue)

    channel.exchange_declare(exchange='ppd/voting', exchange_type='fanout')
    voting = channel.queue_declare(queue = 'ppd/voting/'+numero)            # assina/publica - Lista de votação na seed que soluciona o desafio
    channel.queue_bind(exchange='ppd/voting', queue=voting.method.queue)
    
    
    # InitMsg
    dic = {"NodeId": nodeID}
    jsonSTR = json.dumps(dic,indent=2)
    
    channel.basic_consume(queue = 'ppd/init/'+numero , on_message_callback = callback, auto_ack = True)
    channel.basic_publish(exchange = 'ppd/init', routing_key = '', body = jsonSTR)

    # PubKeyMsg
    os.system("bash chaves/generate_key.sh")
    os.system("python3 chaves/0_export_public_key.py")
    os.system("mv private_key.pem public_key.txt chaves/")
    
    channel.basic_consume(queue = 'ppd/pubkey/'+numero , on_message_callback = callback1, auto_ack = True)
    
    # ElectionMsg
    channel.basic_consume(queue = 'ppd/election/'+numero , on_message_callback = callback2, auto_ack = True)
    
    # ChallengerMsg
    channel.basic_consume(queue = 'ppd/challenge/'+numero , on_message_callback = callback3, auto_ack = True)
    
    # SolutionMsg
    channel.basic_consume(queue = 'ppd/solution/'+numero , on_message_callback = callback4, auto_ack = True)
    
    # VotingMsg
    channel.basic_consume(queue = 'ppd/voting/'+numero , on_message_callback = callback5, auto_ack = True)
    
    channel.start_consuming()

if __name__ == '__main__':
    try:
        file = 'output/banco-de-dados.csv'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        file = 'chaves/private_key.pem'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        file = 'chaves/public_key.txt'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        main()
    except KeyboardInterrupt:
        file = 'chaves/private_key.pem'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        file = 'chaves/public_key.txt'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        file = 'seed.txt'
        if(os.path.exists(file) and os.path.isfile(file)): 
            os.remove(file)
        print('Interrupted')
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)