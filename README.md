# Comunicao-Indireta-Eleição-Coordenação-Distribuda-Segurança-e-Tolerancia-a-Falhas

# Implementação
### InitMsg
No inicio do programa o usuario envia para a fila inicial do "init" onde se é passado o nodeID do usuario no formato JSON, a fila "init" recebe as mensagem no callback, neste callbak as mensagens são trazidas do formato JSON para um dicionario, é criada então uma lista local para armazenar os usuarios e a mensagem do proprio usuario é reenviada de tempos em tempos quando o usurio recebe o proprio nodeID, quando a lista completa a quantidade de usuarios o usuario envia para uma outra lista "pubkey" o seu nodeID e a sua chave publica.
## Autores
| [<img src="https://avatars.githubusercontent.com/u/56831082?v=4" width=115><br><sub>Arthur Coelho Estevão</sub>](https://github.com/arthurcoelho442) | [<img src="https://avatars.githubusercontent.com/u/53350761?v=4" width=115><br><sub>Mayke Wallace</sub>](https://github.com/Nitrox0Af) |
| :---: | :---: |
