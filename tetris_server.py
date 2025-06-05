from asyncio import start_server
import websockets, json;
import asyncio;
import numpy as np;
from random import randint

# Specify all connected sockets as global variables.
global ALL_SOCKET, ALL_SOCKET_IDX, SOCKET_AUTOINCRE  
ALL_SOCKET = []
ALL_SOCKET_IDX = []
SOCKET_AUTOINCRE = 0

global isGameEnded
isGameEnded = False


async def accept(websocket, path):
    global SOCKET_AUTOINCRE, ALL_SOCKET, ALL_SOCKET_IDX
    print("connected from client")
    # Keep the unique number of the current socketin idx (increased by 1).
    websocket.idx = SOCKET_AUTOINCRE  
    SOCKET_AUTOINCRE += 1
    websocket.connected = True
    websocket.tetrisHTML = ""
    websocket.isGameEnd = False
    websocket.isReady = False
    ALL_SOCKET.append(websocket)
    ALL_SOCKET_IDX.append(websocket.idx)

    data = {"code": "my_socket_idx", "socket_idx": websocket.idx}
    await websocket.send(json.dumps(data));

    # Sending all players information(sending all sockets information).
    await sendingAllSocketInfo();

    while True:
        try:
            data = await websocket.recv();
            data = json.loads(data);

            if data["code"] == "iam_ready":
                # Change the status value (isReady) to true for the socket declared ready.
                findIdxFromAllSocket(data["socket_idx"]).isReady = True

                # Notify to whole players that one friend is in READY status.
                for sc in ALL_SOCKET:
                    if sc.idx != data["socket_idx"]: 
                        data = {"code": "friend_ready", "socket_idx": data["socket_idx"]}
                        await sc.send(json.dumps(data));

                isAllReady = True
                for sc in ALL_SOCKET:
                    if sc.isReady != True:
                        isAllReady = False
                # All sockets are ready.
                if isAllReady == True: 
                    await stanby()
            elif data["code"] == "send_tetris_html":
                await sendTetrisHTML(data["socket_idx"])
            elif data["code"] == "newblock_request":
                await prepare_and_send_specific_client_block(findIdxFromAllSocket(data["socket_idx"]), data["sending_block_idx"])
            elif data["code"] == "strike":
                await strike(data["attacker"], data["count"])
            elif data["code"] == "game_end":
                findIdxFromAllSocket(data["socket_idx"]).isGameEnd = True

                countPlaying = 0
                winnerIdx = -1
                for sc in ALL_SOCKET:
                    if sc.idx != data["socket_idx"]:
                        data_temp = {"code": "friend_game_end", "socket_idx": data["socket_idx"]}
                        await sc.send(json.dumps(data_temp))

                        if sc.isGameEnd == False:
                            countPlaying += 1
                            winnerIdx = sc.idx

                if countPlaying <= 1:
                    isGameEnded = True
                    await gameFinish(winnerIdx)

            elif data["code"] == "my_tetris":
                data["html"] = data["html"].replace('class="space" id="', 'class="space" pre_id="')
                data["html"] = data["html"].replace('class="block" id="', 'class="block" pre_id="')
                data["html"] = data["html"].replace('id="divEND"', 'pre_id="divEND"')
                data["html"] = data["html"].replace('class="space"', 'class="space_small"')
                data["html"] = data["html"].replace('class="block"', 'class="block_small"')
                data["html"] = data["html"].replace('makeBlock(12, 22);', '')
                data["html"] = data["html"].replace('style="width:300px"', '')

                findIdxFromAllSocket(data["socket_idx"]).tetrisHTML = data["html"]

        # When socket disconnected.
        except websockets.ConnectionClosed: 
            websocket.connected = False
            continue
        finally:
             # Disconnected status.
            if websocket.connected != True: 
                for idx, val in enumerate(ALL_SOCKET_IDX):
                    if val == websocket.idx:
                        del ALL_SOCKET_IDX[idx]
                del ALL_SOCKET[websocket.idx]
                break


async def strike(attacker, cnt):
    data = {"code": "attack_counter", "count": cnt}
    data = json.dumps(data)

    for sc in ALL_SOCKET:
        if sc.idx != attacker:  
            await sc.send(data)


async def gameFinish(winnerIdx):
    data = {"code": "game_finish", "sockets": ALL_SOCKET_IDX, "winnerIdx": winnerIdx}
    data = json.dumps(data);

    for sc in ALL_SOCKET:
        await sc.send(data)


# Send new current block and next block to a specific client
async def prepare_and_send_specific_client_block(sc, client_sending_block_idx):
    global NEXT_BLOCK_SHAPE, NOW_BLOCK_SHAPE, BLOCK_ARRAY, ALL_BLOCK

    current_block_array_idx = client_sending_block_idx 
    next_block_array_idx = client_sending_block_idx + 1  

    # Ensure BLOCK_ARRAY is filled up to the next_block_array_idx.
    while len(BLOCK_ARRAY) <= next_block_array_idx:
        BLOCK_ARRAY.append(randint(0, len(ALL_BLOCK) - 1))

    now_block_for_client = BLOCK_ARRAY[current_block_array_idx]
    next_block_for_client = BLOCK_ARRAY[next_block_array_idx]

    # Set the current and next block shapes for this client
    NOW_BLOCK_SHAPE = now_block_for_client  
    NEXT_BLOCK_SHAPE = next_block_for_client
    
    data = {"code": "newblock", "now_block": now_block_for_client, "next_block": next_block_for_client}
    await sc.send(json.dumps(data))


async def sendTetrisHTML(idx):
    ALL_SOCKET_HTML = []
    for sc in ALL_SOCKET:
        ALL_SOCKET_HTML.append({"code": "tetris_html", "idx": sc.idx, "html": sc.tetrisHTML})

    data = {"code": "friends_now_html", "friends_tetris_html": ALL_SOCKET_HTML}
    data = json.dumps(data)
    await findIdxFromAllSocket(idx).send(data)


async def stanby():
    print("stanby")
    
    # 1. Send "stanby" message to clients first.
    stanby_data = {"code": "stanby", "sockets": ALL_SOCKET_IDX}
    stanby_data_json = json.dumps(stanby_data)
    for sc in ALL_SOCKET:
        await sc.send(stanby_data_json)

    # 2. Start the countdown (sends messages up to "Start!").
    await startTimer() 

    # 3. After "Start!", broadcast the first block information.
    await newBlock()


async def startTimer():
    countDown = 3 

    for i in range(countDown, 0, -1): 
        data = {"code": "countdown", "count": str(i)} 
        data = json.dumps(data)

        for sc in ALL_SOCKET:
            await sc.send(data)

        await asyncio.sleep(1)

    data = {"code": "countdown", "count": "Start!"}
    data = json.dumps(data)

    for sc in ALL_SOCKET:
        await sc.send(data)


global NEXT_BLOCK_SHAPE, NOW_BLOCK_SHAPE
NEXT_BLOCK_SHAPE = ""  # Next block.
NOW_BLOCK_SHAPE = ""  # Current block.

global ALL_BLOCK, BLOCK_POSITION_SHAPE
ALL_BLOCK = []
ALL_BLOCK.append(np.array([["0:0", "1:0", "2:0", "3:0"], ["0:0", "0:1", "0:2", "0:3"]]))
ALL_BLOCK.append(np.array([["0:0", "0:1", "1:1"], ["0:1", "0:0", "1:0"], ["0:0", "1:0", "1:1"], ["1:0", "0:1", "1:1"]]))
ALL_BLOCK.append(
    np.array([["0:1", "1:1", "1:0"], ["0:-1", "0:0", "1:0"], ["0:1", "0:0", "1:0"], ["0:-1", "1:-1", "1:0"]]))
ALL_BLOCK.append(np.array(
    [["0:1", "1:1", "2:1", "0:0"], ["0:1", "0:0", "0:-1", "1:-1"], ["0:-2", "1:-2", "2:-2", "2:-1"],
     ["0:0", "0:1", "-1:2", "0:2"]]))
ALL_BLOCK.append(np.array([["0:1", "1:1", "2:1", "2:0"], ["1:-1", "1:0", "1:1", "2:1"], ["-1:1", "-1:0", "0:0", "1:0"],
                           ["0:-1", "1:-1", "1:0", "1:1"]]))
ALL_BLOCK.append(np.array([["1:1", "2:1", "1:0", "2:0"]]))

global BLOCK_ARRAY
BLOCK_ARRAY = []


async def newBlock():
    # Bring the blocks randomly.
    global NEXT_BLOCK_SHAPE, ALL_BLOCK, BLOCK_POSITION_SHAPE
    BLOCK_POSITION_SHAPE = 0

    if NEXT_BLOCK_SHAPE == "":
        BLOCK_ARRAY.append(randint(0, len(ALL_BLOCK) - 1));
        BLOCK_ARRAY.append(randint(0, len(ALL_BLOCK) - 1));

        NOW_BLOCK_SHAPE = BLOCK_ARRAY[len(BLOCK_ARRAY) - 2]
        NEXT_BLOCK_SHAPE = BLOCK_ARRAY[len(BLOCK_ARRAY) - 1]
    else:
        BLOCK_ARRAY.append(randint(0, len(ALL_BLOCK) - 1));

        NOW_BLOCK_SHAPE = NEXT_BLOCK_SHAPE
        NEXT_BLOCK_SHAPE = BLOCK_ARRAY[len(BLOCK_ARRAY) - 1]

    data = {"code": "newblock", "next_block": NEXT_BLOCK_SHAPE, "now_block": NOW_BLOCK_SHAPE}
    data = json.dumps(data)

    for sc in ALL_SOCKET:
        await sc.send(data)


def findIdxFromAllSocket(idx):
    for sc in ALL_SOCKET:
        if sc.idx == idx:
            return sc


async def sendingAllSocketInfo():
    data = {"code": "all_friends", "sockets": ALL_SOCKET_IDX}
    for sc in ALL_SOCKET:
        await sc.send(json.dumps(data));
        print("sending AllSocketInfo!")


# Web socket server is created on localhost, 8080 port.
start_server = websockets.serve(accept, "localhost", 8080);
loop = asyncio.get_event_loop();
loop.run_until_complete(start_server);

try:
    loop.run_forever();
finally:
    loop.close();

