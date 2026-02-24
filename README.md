# 💻 Roteiro de Laboratório 2: Concorrência e Gargalos em Servidores TCP

**Curso:** Engenharia de Software
**Disciplina:** LABORATÓRIO DE DESENVOLVIMENTO DE APLICAÇÕES MÓVEIS E DISTRIBUÍDAS
**Professor:** Cristiano de Macedo Neto
**Unidade:** Unidade 0 — Nivelamento de conceitos de redes de computadores e Sistemas Operacionais

---

👋 Olá, pessoal! Bem-vindos a este laboratório.

Nesta prática, vamos consolidar os conceitos de redes de computadores (protocolos TCP/IP, endereçamento, backlog de conexões) e o ciclo de vida de Threads no Sistema Operacional, observando diretamente as consequências de cada decisão arquitetural em um servidor de rede.

---

## 🎯 Objetivos da Prática

1. Observar na prática o funcionamento do protocolo TCP e o comportamento da fila de conexões (*backlog*) gerenciada pelo Sistema Operacional.
2. Analisar os gargalos de servidores com I/O bloqueante (*Blocking I/O*).
3. Compreender o custo computacional (*overhead*) e a troca de contexto (*Context Switch*) na concorrência baseada em Threads.
4. Implementar um servidor assíncrono (*Event-Driven*) utilizando o modelo de *Event Loop*.

---

## 🛠️ Preparação do Ambiente

Neste repositório você já encontra os seguintes scripts em Python:

- **Simuladores de carga:** `client.py` e `clientenervoso.py`
- **Implementações de servidores:** `serverbloq.py`, `servergargalo.py` e `server.py`

> ⚠️ **Atenção:** Todos os testes devem ser executados **exclusivamente em `localhost` (`127.0.0.1`)**, nunca em redes institucionais ou compartilhadas, para evitar impacto em outros usuários e alertas de segurança da rede.

Clone este repositório para sua máquina local, abra seu terminal ou IDE de preferência e divida a tela para visualizar os logs do cliente e do servidor simultaneamente.

---

## 🧪 Etapa 1: O Gargalo Sequencial e o Comportamento da Fila TCP

Nesta etapa observaremos o que acontece quando um servidor bloqueante não consegue atender a demanda e como o Sistema Operacional gerencia a fila de conexões pendentes.

### 1.1 Servidor Bloqueante

1. Inicie o `serverbloq.py`.
2. Em outro terminal, execute o `client.py` (3 clientes simultâneos).
3. Observe o atendimento **estritamente sequencial**: o servidor só aceita a segunda conexão após concluir completamente o atendimento da primeira.

### 1.2 O Comportamento do Backlog

1. Encerre o servidor anterior e inicie o `servergargalo.py`. Este servidor é configurado com `listen(1)`, que sinaliza ao Sistema Operacional uma fila de espera muito pequena.
2. Execute o `clientenervoso.py` (10 clientes simultâneos).
3. Observe os erros `ConnectionRefusedError` e `socket.timeout`.

> 📌 **Nota técnica importante:** O parâmetro passado para `listen()` é tratado pelo kernel como uma **dica**, não como um limite rígido. Tanto no Linux quanto no Windows, o Sistema Operacional pode aceitar um número ligeiramente maior de conexões pendentes do que o valor configurado (conforme documentado em `man 2 listen` no Linux e na RFC 793). Por isso, o comportamento exato que você observará **varia de acordo com o sistema operacional**: em alguns casos você verá `ConnectionRefusedError` imediato; em outros, apenas `Timeout`. **Essa variabilidade faz parte da observação experimental desta etapa.** O que importa registrar é: sob carga suficiente, a fila esgota e novos clientes são recusados ou expiram.

> 🔗 **Conexão com a teoria:** O comportamento observado aqui corresponde diretamente ao mecanismo de *backlog* da interface de sockets descrita em Tanenbaum & Wetherall (2011, cap. 6) e ao problema clássico de escalabilidade de servidores documentado por Kegel (2006) no artigo *"The C10K Problem"* — uma leitura fortemente recomendada para contextualizar o que estamos resolvendo ao longo deste laboratório.

---

## 🧪 Etapa 2: A Solução com Threads — Paralelismo via Sistema Operacional

Nesta etapa delegamos o bloqueio de I/O ao Sistema Operacional através de Threads, observando os ganhos e os custos dessa abordagem.

### 2.1 Servidor Multithread

1. Inicie o `server.py`.
2. Execute o `clientenervoso.py` (10 clientes simultâneos).
3. Observe que todos os clientes conectam quase instantaneamente e o log exibe o número de threads ativas (`threading.active_count()`).

> 🔎 **Ponto de reflexão:** O servidor agora delega cada conexão para uma Thread separada. O Sistema Operacional realiza a **Troca de Contexto** (*Context Switch*) na CPU para manter todas essas threads ativas de forma concorrente. Cada Thread consome memória de pilha (*stack*) alocada pelo SO — tipicamente entre 512 KB e 8 MB por thread dependendo da plataforma. Anote o número máximo de threads simultâneas que você observou: você precisará desse dado no relatório.

> 🔗 **Conexão com a teoria:** O ciclo de vida de threads e o custo do *Context Switch* são discutidos em Silberschatz, Galvin & Gagne (2018, cap. 4). A relação entre threads, I/O bloqueante e escalabilidade é central para compreender as limitações desta abordagem frente ao modelo assíncrono.

---

## 🧪 Etapa 3: Alta Performance com I/O Assíncrono (Event Loop)

Nesta etapa você implementará um servidor TCP assíncrono utilizando a biblioteca `asyncio` do Python, que implementa o padrão de *Event Loop* — modelo amplamente adotado em servidores de produção de alta escala (Node.js, Nginx, Uvicorn).

### 3.1 Contexto teórico antes de codar

No modelo assíncrono, uma **única Thread** gerencia todas as conexões por meio de um laço de eventos (*Event Loop*). Quando uma operação de I/O é iniciada (ex: esperar dados de um cliente), o Event Loop **não bloqueia** — ele simplesmente registra um *callback* e passa para o próximo evento pendente. Isso elimina o custo de criação e troca de contexto entre múltiplas Threads.

A figura abaixo representa conceitualmente a diferença:

```
Modelo Multithread:          Modelo Assíncrono (Event Loop):
  Thread 1 → Cliente A          Event Loop (Thread única)
  Thread 2 → Cliente B            ├── await Cliente A
  Thread 3 → Cliente C            ├── await Cliente B
  ...                             └── await Cliente C
  (N threads no SO)               (1 thread, N corrotinas)
```

### 3.2 Implementação

Crie um arquivo chamado `server_async.py` na raiz do repositório. Você deverá implementar um servidor TCP assíncrono seguindo a estrutura abaixo. Os comentários indicam **o que você deve preencher** — a lógica de cada passo é sua responsabilidade:

```python
import asyncio

HOST = '127.0.0.1'
PORT = 65432

async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Corrotina chamada pelo Event Loop para cada nova conexão.
    Substitui a função que antes rodava em uma Thread separada.
    """
    addr = writer.get_extra_info('peername')
    print(f"[NOVA CONEXÃO] {addr}")

    # 1. Leia os dados enviados pelo cliente (use 'await reader.read(1024)')
    # TODO: ...

    # 2. Simule um processamento pesado SEM bloquear a thread principal.
    #    Use 'await asyncio.sleep(5)' — NÃO use 'time.sleep(5)'.
    #    Entenda a diferença: time.sleep bloqueia a Thread; asyncio.sleep
    #    apenas suspende a corrotina e devolve o controle ao Event Loop.
    # TODO: ...

    # 3. Envie a resposta ao cliente (use 'writer.write(...)' e 'await writer.drain()')
    # TODO: ...

    # 4. Feche a conexão (use 'writer.close()' e 'await writer.wait_closed()')
    # TODO: ...

    print(f"[DESCONECTADO] {addr}")


async def main():
    """
    Ponto de entrada assíncrono: cria e inicia o servidor.
    """
    # Use asyncio.start_server() passando handle_client, HOST e PORT
    # TODO: ...

    print(f"[ASSÍNCRONO] Servidor rodando em {HOST}:{PORT} — Event Loop ativo.")

    # Mantenha o servidor rodando indefinidamente
    # TODO: ...


if __name__ == "__main__":
    asyncio.run(main())
```

> 📚 **Referências para esta etapa:**
> - Documentação oficial do `asyncio`: https://docs.python.org/3/library/asyncio.html
> - Kegel, D. (2006). *The C10K Problem*. Disponível em: http://www.kegel.com/c10k.html
> - Para uma análise comparativa formal entre modelos de concorrência, consulte: Ousterhout, J. (1996). *Why Threads Are A Bad Idea (for most purposes)*. USENIX Technical Conference.

### 3.3 Validação

1. Execute seu `server_async.py`.
2. Ataque-o com o `clientenervoso.py`.
3. Verifique que **todos os 10 clientes** são atendidos com sucesso, em concorrência, com **uma única Thread** ativa no processo Python.

---

## 📦 Entrega e Avaliação

A entrega será avaliada pelos *commits* neste repositório via GitHub Classroom.

**Links Úteis:**
- [Página da nossa Classe no GitHub](https://classroom.github.com/classrooms/76447459-icei-puc-minas-pples-ti-202601-labdamd-g2)
- [Link do Assignment atual](https://classroom.github.com/a/FIuNNNdh)

### O que deve ser commitado?

**1. Código Fonte — `server_async.py`**

O arquivo implementado na Etapa 3, funcionando corretamente e atendendo os 10 clientes do `clientenervoso.py` sem erros.

**2. Relatório Técnico — `RELATORIO.md`**

Crie o arquivo `RELATORIO.md` na raiz do repositório respondendo de forma técnica e objetiva às seguintes questões:

- **Questão 1 — Backlog e Recusa de Conexões:**
O `clientenervoso.py` apresentou falhas (`ConnectionRefusedError` ou `Timeout`) ao testar o `servergargalo.py`, mas obteve sucesso imediato contra o `server.py`. Explique o motivo técnico, referenciando o conceito de *backlog* TCP e o comportamento do Sistema Operacional. Considere a variabilidade de comportamento entre sistemas operacionais mencionada no roteiro.

- **Questão 2 — Custo de Recursos: Threads vs. Event Loop:**
Com base no número máximo de threads simultâneas que você observou no `server.py` (via `threading.active_count()`), explique a diferença no consumo de memória e no uso de CPU entre a abordagem Multithread e a abordagem Assíncrona. Sua resposta deve ser fundamentada na observação experimental, não apenas conceitual.

**3. Desafio Extra** 

Altere o `clientenervoso.py` para disparar **200 conexões simultâneas** contra seu `server_async.py`.

> ⚠️ Execute este desafio apenas em `localhost`. Nunca aponte para servidores externos ou redes institucionais.

Tire um *screenshot* da execução comprovando que o servidor suportou a carga e anexe a imagem no `RELATORIO.md`.

---

## ✅ Checklist de Entrega

Antes de fazer o *push* final, verifique:

- [ ] `server_async.py` está na raiz do repositório e executa sem erros
- [ ] `server_async.py` atende os 10 clientes do `clientenervoso.py` com sucesso
- [ ] `RELATORIO.md` responde as duas questões com embasamento técnico
- [ ] O usuário do Professor tem acesso de visualização ao repositório
- [ ] O *push* foi realizado antes do prazo de encerramento da Sprint (01/03/2026)

---

## 📚 Referências Bibliográficas

KEGEL, D. **The C10K Problem**, 2006. Disponível em: http://www.kegel.com/c10k.html. Acesso em: fev. 2026.

OUSTERHOUT, J. **Why Threads Are A Bad Idea (for most purposes)**. USENIX Technical Conference, 1996.

PYTHON SOFTWARE FOUNDATION. **asyncio — Asynchronous I/O**. Python 3 Documentation. Disponível em: https://docs.python.org/3/library/asyncio.html. Acesso em: fev. 2026.

SILBERSCHATZ, A.; GALVIN, P. B.; GAGNE, G. **Operating System Concepts**. 10. ed. Hoboken: Wiley, 2018. cap. 4.

TANENBAUM, A. S.; WETHERALL, D. J. **Computer Networks**. 5. ed. Upper Saddle River: Pearson Prentice Hall, 2011. cap. 6.


//