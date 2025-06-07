// 블록을 생성할 수 있는지 여부를 확인하고, 그렇지 않으면 게임을 종료합니다.
for (var i = 0; i < now_block_shape.length; i++) {
    var x = parseInt(now_block_shape[i].split(':')[0]) + block_start_x;
    var y = parseInt(now_block_shape[i].split(':')[1]) + block_start_y;
    if (document.getElementById(x + ":" + y).className == "block") {
        isGameEnd = true;
        ws.send(JSON.stringify({ code: "game_end", socket_idx: my_socket_idx }));

        var div = document.getElementById("div_for_game_end");
        div.style.display = "block";
        div.innerHTML = "GAME OVER";

        return;
    }
} 