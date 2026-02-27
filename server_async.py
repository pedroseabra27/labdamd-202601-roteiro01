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
    data = await reader.read(1024)
    if not data:
        print(f"[{addr}] conexao fechada sem dados")
        writer.close()
        await writer.wait_closed()
        return
    msg = data.decode('utf-8')
    print(f"[{addr}] recebeu: {msg}")

    # 2. Simule um processamento pesado SEM bloquear a thread principal.
    #    Use 'await asyncio.sleep(5)' — NÃO use 'time.sleep(5)'.
    #    Entenda a diferença: time.sleep bloqueia a Thread; asyncio.sleep
    #    apenas suspende a corrotina e devolve o controle ao Event Loop.
    # TODO: ...
    await asyncio.sleep(5)

    # 3. Envie a resposta ao cliente (use 'writer.write(...)' e 'await writer.drain()')
    # TODO: ...
    resposta = f"dados: {msg}"
    writer.write(resposta.encode('utf-8'))
    await writer.drain()

    # 4. Feche a conexão (use 'writer.close()' e 'await writer.wait_closed()')
    # TODO: ...
    writer.close()
    await writer.wait_closed()
    


async def main():
    """
    Ponto de entrada assíncrono: cria e inicia o servidor.
    """
    # Use asyncio.start_server() passando handle_client, HOST e PORT
    # TODO: ...
    server = await asyncio.start_server(handle_client, HOST, PORT)

    print(f"[ASSÍNCRONO] Servidor rodando em {HOST}:{PORT} — Event Loop ativo.")

    # Mantenha o servidor rodando indefinidamente
    # TODO: ...
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())