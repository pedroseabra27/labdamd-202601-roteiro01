
## Questão 1 — Backlog e Recusa de Conexões

O `clientenervoso.py` apresentou falhas ao testar o `servergargalo.py` porque esse servidor usa `listen(1)`, tornando a fila de conexões TCP muito pequena. Mesmo que o Sistema Operacional arredonde esse valor internamente, a fila continua insuficiente para absorver os 10 clientes simultâneos, resultando em `ConnectionRefusedError` ou `socket.timeout` para os que não conseguem entrar.

No `server.py`, o `listen()` é chamado sem argumento, utilizando o tamanho de fila padrão do SO, que supera tranquilamente nossa demanda. Além disso, ao aceitar uma conexão, o servidor a delega imediatamente a uma Thread e retorna ao `accept()`, impedindo o acúmulo de conexões pendentes na fila. Com isso, todos os 10 clientes são atendidos sem erros.

---

## Questão 2 — Custo de Recursos: Threads vs. Event Loop

Comparando as duas abordagens nos experimentos, ficou claro que o modelo multithread possui maior consumo de memória e CPU. Cada Thread criada tem sua própria stack alocada pelo SO, e a alternância entre elas exige trocas de contexto — operações que envolvem salvar e restaurar registradores e estado de execução. Quanto mais threads ativas, maior esse overhead. No teste com `server.py` e 10 clientes simultâneos, foram observadas **11 threads ativas** (`threading.active_count()`): uma por cliente e a thread principal.

No modelo assíncrono (`server_async.py`), apenas **1 thread** gerencia todas as conexões por meio de corrotinas. Corrotinas são estruturas mais leves do que threads — ao encontrar um `await`, o Event Loop simplesmente suspende aquela corrotina e executa outra, sem envolver o escalonador do SO. O custo de alternância entre corrotinas é significativamente menor do que entre threads, resultando em menor overhead de CPU e consumo de memória muito mais controlado.

---


