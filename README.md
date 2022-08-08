# Comunicao-Indireta-Eleição-Coordenação-Distribuda-Segurança-e-Tolerancia-a-Falhas

# Implementação
No inicio do programa o banco de dados local e as chaves publica e privada são excluidos para se evitar conflitos.
### InitMsg
No inicio do programa o usuario envia para a fila inicial do "init" onde se é passado o nodeID do usuario no formato JSON, a fila "init" recebe as mensagem no callback, neste callbak as mensagens são trazidas do formato JSON para um dicionario, é criada então uma lista local para armazenar os usuarios e a mensagem do proprio usuario é reenviada de tempos em tempos quando o usurio recebe o proprio nodeID, quando a lista completa a quantidade de usuarios o usuario envia para uma outra lista "pubkey" o seu nodeID e a sua chave publica.
### PubKeyMsg
Nesta fila de mensagens o usuario criana inicialmente antes mesmo de receber qualquer mensagem de outro usuario, sua chave publica e privada, as mensagens consumidas são enviadas para o callback 1 onde, seguindo a mesma execução do callbeck, as mensagens são armazenadas em uma lista, e quando a lista completa a quantidade de usuarios, e enviado para a fila de "eleição" o voto do usuario, juntamente com o a assinatura e o nodeID, a chave do proprio usuario e reenviada de tempos em tempos para se evitar a inanição do programa.
# ElectionMsg
As mensagens da fila de eleição são tratadas no callback2, esta fila segue os mesmos principios das outras duas filas, porem para se adicionar um voto na lista e preciso primordialmente verificar a assinatura do eleito associado, essa verificação é feita pegando-se a chave publica do nodeID equivalente na lista de chaves local, quando se completa a quantidade de usuarios, cada usuario de forma local conta os votos e seleciona o nodeID da lista que obteve a maior quantidade de votos, por utilizar a função couter juntamente com a most_common a lista é ordenada sendo assim possivel selecioanr o que obtem o maior nodeID em caso de empate. Os usuarios também fazem uma verificação para saber se ele mesmo é o usuario eleito, e caso ele seja, gera uma nova transação e envia o chalenger para os demais candidatos. 
# ChallengerMsg
Nesta fila o challenger enviado pelo usuario eleito e consumido no callback3, onde inicialmente é verificado se o challenger enviado foi realmente enviado pelo usuario eleito, posteriormente o usuario buscalocalmente uma seed que solucione o desafio, essa seed é encontrada gerando duas vezes mais um do challenger em threads cada thread gera strings aleatorias com tamanhos que almentão constantemente até se encontrar uma seed, após encontrada todas as threads param e a seed encontrada é assinada e enviada para a fila "solution" para ser analizada.
# SolutionMsg
# VotingMsg
## Autores
| [<img src="https://avatars.githubusercontent.com/u/56831082?v=4" width=115><br><sub>Arthur Coelho Estevão</sub>](https://github.com/arthurcoelho442) | [<img src="https://avatars.githubusercontent.com/u/53350761?v=4" width=115><br><sub>Mayke Wallace</sub>](https://github.com/Nitrox0Af) |
| :---: | :---: |
