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
No inicio do programa o banco de dados local e as chaves publica e privada são excluidos para se evitar conflitos.
### InitMsg
No inicio do programa o usuario envia para a fila inicial do "init" onde se é passado o nodeID do usuario no formato JSON, a fila "init" recebe as mensagem no callback, neste callbak as mensagens são trazidas do formato JSON para um dicionario, é criada então uma lista local para armazenar os usuarios e a mensagem do proprio usuario é reenviada de tempos em tempos quando o usurio recebe o proprio nodeID, quando a lista completa a quantidade de usuarios o usuario envia para uma outra lista "pubkey" o seu nodeID e a sua chave publica.
### PubKeyMsg
Nesta fila de mensagens o usuario criana inicialmente antes mesmo de receber qualquer mensagem de outro usuario, sua chave publica e privada, as mensagens consumidas são enviadas para o callback 1 onde, seguindo a mesma execução do callbeck, as mensagens são armazenadas em uma lista, e quando a lista completa a quantidade de usuarios, e enviado para a fila de "eleição" o voto do usuario, juntamente com o a assinatura e o nodeID, a chave do proprio usuario e reenviada de tempos em tempos para se evitar a inanição do programa.
### ElectionMsg
As mensagens da fila de eleição são tratadas no callback2, esta fila segue os mesmos principios das outras duas filas, porem para se adicionar um voto na lista e preciso primordialmente verificar a assinatura do eleito associado, essa verificação é feita pegando-se a chave publica do nodeID equivalente na lista de chaves local, quando se completa a quantidade de usuarios, cada usuario de forma local conta os votos e seleciona o nodeID da lista que obteve a maior quantidade de votos, por utilizar a função couter juntamente com a most_common a lista é ordenada sendo assim possivel selecioanr o que obtem o maior nodeID em caso de empate. Os usuarios também fazem uma verificação para saber se ele mesmo é o usuario eleito, e caso ele seja, gera uma nova transação e envia o chalenger para os demais candidatos. 
### ChallengerMsg
Nesta fila o challenger enviado pelo usuario eleito e consumido no callback3, onde inicialmente é verificado se o challenger enviado foi realmente enviado pelo usuario eleito, posteriormente o usuario buscalocalmente uma seed que solucione o desafio, essa seed é encontrada gerando duas vezes mais um do challenger em threads cada thread gera strings aleatorias com tamanhos que almentão constantemente até se encontrar uma seed, após encontrada todas as threads param e a seed encontrada é assinada e enviada para a fila "solution" para ser analizada.
### SolutionMsg
A verificação da seed é feita no callback4 onde após verificação de autenticidade, é verificado se a transição atual já foi finalizada e caso não tenha sido é gerad um arquivo seed para se armazenar localmente a seed recebida, e todas as outras seeds posteriores, os usuarios enviam para a fila "voting" o seu respctivo voto após verificação se a seed encontrada realmente soluciona o desafio.
### VotingMsg
A ultima fila, e a mais importante, e a fila de contagem de votos, localizada no callback5, nesta fila os votos validos são armazenados e quando se obtem todos os votos olha-se se a maioria aprova a seed, caso sim a seed no topo do arquivo seed.txt e colocada na lista local juntamente com o id do node que enviou a seed e o arquivo então é apagado, caso a seed não seja aprovada a seed é removida do topo do arquivo seed.txt e a próxima votação se inicia. Sendo apenas possivel haver verificação da votação caso o arquivo seed.txt exista.
## Testes
## Analise
## Requerimento de instalação
requer a instalação do pycryptodome 3.15.0, pika, pandas e threading.

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
sudo apt-get install -y python3-crypto
```
Instalando pandas:
```
sudo apt install python3-pandas
```
Instalando threading:
```
pip3 install threading
```
## Modo de execução
Navegue até a pasta usuario e execute o código logo abaixo garantindo que a pasta chaves não tenha sido altera e que os arquivos 0_export_public_key.py, 1_sign.py, 2_verify.py e generate_key.sh esteja na pasta e não tenham sido alterados.
```
python3 miner.py
```
após execução aparecera uma mensagem local pedindo para informar a quantidade de usuarios que participarão da minenaração. Por fim o código ficara responsavel por manter a comunicação com os outros usuarios.
## Autores
| [<img src="https://avatars.githubusercontent.com/u/56831082?v=4" width=115><br><sub>Arthur Coelho Estevão</sub>](https://github.com/arthurcoelho442) | [<img src="https://avatars.githubusercontent.com/u/53350761?v=4" width=115><br><sub>Mayke Wallace</sub>](https://github.com/Nitrox0Af) |
| :---: | :---: |
