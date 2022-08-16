# Comunicao-Indireta-Eleição-Coordenação-Distribuda-Segurança-e-Tolerancia-a-Falhas
## Objetivos
- Experimentar a implementação de sistemas de comunicação indireta por meio de
middleware Publish/Subscribe (Pub/Sub);
- Realizar eleição de coordenador em sistemas distribuídos por meio da troca de mensagens
entre os participantes do sistema;
- Realizar votação sobre o estado de transações distribuídas por meio da troca de mensagens
entre os participantes do sistema.
- Experimentar a verificação de assinaturas de mensagens por meio de chaves públicas/
privadas;
- Tratar algumas situações de falhas ou inconsistências em Sistemas Distribuídos.
## Implementação
Primordialmente no programa o banco de dados local e as chaves publica e privada são excluídos para se evitar conflitos.
### InitMsg
No início do programa o usuário envia para a fila inicial do "init" onde se é passado o nodeID do usuário no formato JSON, a fila "init" recebe a mensagem no callback, neste callbak as mensagens são trazidas do formato JSON para um dicionário, é criada então uma lista local para armazenar os usuários e a mensagem do próprio usuário é reenviada de tempos em tempos quando o usuário recebe o próprio nodeID, quando a lista completa a quantidade de usuários o usuário envia para outra lista "pubkey" o seu nodeID e a sua chave publica.
### PubKeyMsg
Nesta fila de mensagens o usuário cria inicialmente antes mesmo de receber qualquer mensagem de outro usuário, sua chave publica e privada, as mensagens consumidas são enviadas para o callback 1 onde, seguindo a mesma execução do callbeck, as mensagens são armazenadas em uma lista, e quando a lista completa a quantidade de usuários, e enviado para a fila de "eleição" o voto do usuário, com a assinatura e o nodeID, a chave do próprio usuário e reenviada de tempos em tempos para se evitar a inanição do programa.
### ElectionMsg
As mensagens da fila de eleição são tratadas no callback2, esta fila segue os mesmos princípios das outras duas filas, porem para se adicionar um voto na lista e preciso primordialmente verificar a assinatura do eleito associado, essa verificação é feita pegando-se a chave publica do nodeID equivalente na lista de chaves local, quando se completa a quantidade de usuários, cada usuário de forma local conta os votos e seleciona o nodeID da lista que obteve a maior quantidade de votos. Os usuários também fazem uma verificação para saber se ele mesmo é o usuário eleito, e caso ele seja, gera uma nova transação e envia o challenger para os demais candidatos. 
### ChallengerMsg
Nesta fila o challenger enviado pelo usuário eleito e consumido no callback3, onde é inicialmente verificado se o challenger enviado foi realmente enviado pelo usuário eleito, posteriormente o usuário busca localmente uma seed que solucione o desafio, essa seed é encontrada gerando duas vezes mais um do challenger em threads cada thread gera strings aleatórias com tamanhos que aumentam constantemente até se encontrar uma seed, após encontrada todas as threads param e a seed encontrada é assinada e enviada para a fila "solution" para ser analisada.
### SolutionMsg
A verificação da seed é feita no callback4 onde após verificação de autenticidade, é verificado se a transição atual já foi finalizada e caso não tenha sido é gerado um arquivo seed para se armazenar localmente a seed e o nodeID recebido, e todas as outras seeds e nodeIDs posteriores, os usuários enviam para a fila "voting" o seu respectivo voto após verificação se a seed encontrada realmente soluciona o desafio.
### VotingMsg
A última fila, e a mais importante, e a fila de contagem de votos, localizada no callback5, nesta fila os votos validos são armazenados e quando se obtêm todos os votos olham-se se a maioria aprova a seed, caso sim a seed no topo do arquivo seed.txt e colocada na lista local com o id do node que enviou a seed e o arquivo então é apagado, caso a seed não seja aprovada a seed é removida do topo do arquivo seed.txt e a próxima votação se inicia. Sendo apenas possível haver verificação da votação caso o arquivo seed.txt exista.
## Testes
Os testes executados foram elaborados utilizando vários usuários e dentre eles foram utilizados alguns usuários mal-intencionados, dentre eles foram desenvolvidos 3 tipos de usuários mal-intencionados:
  -  O primeiro usuário que frauda a eleição dos usuários, tentando se passar por outros usuários enviando a sua própria seed como voto.
  -  O segundo usuário que tenta fraudar o envio de challenger, enviando uma challenger aleatória independente se foi ele o usuário eleito ou não.
  -  O terceiro usuário frauda a votação das seeds, tentado enviar votos por outros usuários de duas formar, uma quando a seed e a dele tenta enviar True como voto dos outros usuários, e a outra e quando a seed não é a dele, logo ele tenta enviar Falso como voto de todos os usuários.

Todos os usuários mal-intencionados utilizados para teste podem ser encontrados na pasta "Teste" do repositório.
## Analise
Conforme fomos desenvolvendo o código, encontramos algumas dificuldades que possibilitaram o entendimento aprofundado em relação de comunicação distribuída, a coordenação com a qual as filas funcionam são complexas, mas após compreensão possibilitaram uma implementação satisfatória de comunicação indireta, um dos aprendizados adquirido foi em pauta do funcionamento paralelo e sequencial das filas, percebemos que apesar da operação paralela das filas, ex: "ppd/solution" e "ppd/voting" as mensagens consumidas são executadas sequencialmente nas filas, ex: caso recebemos duas soluções, a primeira solução sera consumida no callback referente a "solution" e caso solution envie seu voto para "voting", o mesmo entra em execução paralelamente por tanto a segunda mensagem de solução só ira ser analisada após o callback da 1 mensagem de solução ser finalizado. Isto facilitou nosso entendimento e proporcionou uma implementação mais limpa e dinâmica com a junção de uso de memória e disco.

A análise anterior também nos trouxe outra reflexão, pois o modo que implementamos dispensava algumas variáveis que eram passadas obrigatoriamente pelas filas, denotando um conceito essencial em comunicação indireta, conceito este que diz respeito a implementação de código, pois não importa o modo que os outros usuários implementam seus códigos contanto que as mensagens em fila sejam padronizadas, contudo, nosso código mesmo não utilizando das variáveis passadas em fila, envia mensagens com a mesma formatação que a de outros usuários, para garantir a confiabilidade.

## Requerimento de instalação
requer a instalação do pycryptodome 3.15.0, pika, pandas, threading e do RabbitMQ.

Primeiramente atualizando o sistema
```
sudo apt-get update -y
```
```
sudo apt-get upgrade -y
```
Instalação do pip:
```
python3 -m pip install --upgrade pip
```
Instalação do pika:
```
python3 -m pip install --upgrade pika
```
Instalando pycrypto:
```
python3 -m pip install --upgrade pyCrypto
```
Instalando pandas:
```
sudo apt install python3-pandas
```
Instalando threading:
```
pip3 install threading
```
Instalando time:
```
pip install python-time
```
Instalação do RabbitMQ:

<a href="https://www.vultr.com/docs/install-rabbitmq-server-ubuntu-20-04-lts/?utm_source=performance-max-latam&utm_medium=paidmedia&obility_id=17096555207&utm_adgroup=&utm_campaign=&utm_term=&utm_content=&gclid=Cj0KCQjw3eeXBhD7ARIsAHjssr_Pi2EL3oHR-gBu8xULUWuVvIZCereqfGfjoYEwc6L6vaUVUbRa7LAaAgjQEALw_wcB">RabbitMQ</a>
## Modo de execução
Navegue até a pasta usuario e execute o código logo abaixo garantindo que a pasta chaves não tenha sido altera e que os arquivos 0_export_public_key.py, 1_sign.py, 2_verify.py e generate_key.sh esteja na pasta e não tenham sido alterados.
```
python3 miner.py
```
Após execução aparecera uma mensagem local pedindo para informar a quantidade de usuários que participarão da mineração. Por fim, o código ficara responsável por manter a comunicação com os outros usuários.
## Autores
| [<img src="https://avatars.githubusercontent.com/u/56831082?v=4" width=115><br><sub>Arthur Coelho Estevão</sub>](https://github.com/arthurcoelho442) | [<img src="https://avatars.githubusercontent.com/u/53350761?v=4" width=115><br><sub>Mayke Wallace</sub>](https://github.com/Nitrox0Af) |
| :---: | :---: |
