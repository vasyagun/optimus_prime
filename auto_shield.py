import asyncio
import json
import websockets
import requests
# Константы

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZGRyZXNzIjoiMDo3NDZhYzE5ZWY3OWU1YmIzN2I2YWQ3YjdmMTRkNmMzNzhlNWYzZGY5ZTZkY2Q2NTA3Y2IxOTM1NDg3ZDczOWU3IiwiZXhwIjoyMDYwOTMwMTU4fQ.tJX-x6nkGs0W_BH74berAxGC0kVl5AZRYUrSYz23uXU"  # обрежь для безопасности
USER_ID = 21625
WS_URL = f"wss://api-game.gramilla.world/ws?token={TOKEN}"
MAP_URL = "https://api-game.gramilla.world/currentMap"
UPDATE_INTERVAL = 30  # сколько секунд между обновлениями клеток

# Глобальные переменные
MY_CELLS = set()
applied_cells = set()

# Фоновая задача для обновления клеток
async def update_my_cells_periodically():
    global MY_CELLS
    while True:
        try:
            resp = requests.get(MAP_URL)
            resp.raise_for_status()
            data = resp.json()
            updated_cells = set()
            for cell in data.get("cells", []):
                if cell.get("user_id") == USER_ID:
                    updated_cells.add(cell["id"])
            MY_CELLS = updated_cells
            print(f"🔄 Обновлено количество клеток: {len(MY_CELLS)}")
        except Exception as e:
            print(f"⚠️ Ошибка при обновлении клеток: {e}")
        await asyncio.sleep(UPDATE_INTERVAL)

# Фоновый ping для поддержания соединения
async def send_ping_periodically(websocket):
    while True:
        try:
            ping = {
                "type": "ping",
                "token": TOKEN
            }
            await websocket.send(json.dumps(ping))
            # print("📡 Ping отправлен")
        except Exception as e:
            print(f"⚠️ Ошибка отправки ping: {e}")
        await asyncio.sleep(20)  # каждые 20 сек


# Основной обработчик WebSocket
async def listen():
    async with websockets.connect(WS_URL) as websocket:
        print("🔌 Подключено к WebSocket")

        # запускаем отправку ping'ов
        asyncio.create_task(send_ping_periodically(websocket))

        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                msg_type = data.get("type")

                if msg_type == "cell_update":
                    cell_id = data["data"]["cell_id"]
                    hp = data["data"]["hp"]
                    if cell_id in MY_CELLS and cell_id not in applied_cells:
                        print(f"⚠️ Клетка {cell_id} теряет HP ({hp}) — атака!")
                        await apply_shield(websocket, cell_id)

                elif msg_type == "map_cell_update":
                    cell = data["data"]
                    if cell.get("user_id") == USER_ID and cell.get("under_attack"):
                        cell_id = cell["id"]
                        if cell_id not in applied_cells:
                            print(f"🚨 Клетка {cell_id} под атакой (under_attack = true)")
                            await apply_shield(websocket, cell_id)

                elif msg_type == "attack_started":
                    attack = data["data"]
                    cell_id = attack.get("cell_id")
                    if attack.get("cell_owner_id") == USER_ID and cell_id not in applied_cells:
                        print(f"🔥 Атака начата на клетку {cell_id} от {attack.get('attacker_nickname')}")
                        await apply_shield(websocket, cell_id)

            except Exception as e:
                print(f"⚠️ Ошибка обработки сообщения: {e}")

# Отправка щита
async def apply_shield(websocket, cell_id):
    msg = {
        "type": "apply_shield",
        "hours": 1,
        "cell_id": cell_id,
        "token": TOKEN
    }
    await websocket.send(json.dumps(msg))
    applied_cells.add(cell_id)
    print(f"🛡️ Щит установлен на клетку {cell_id}")

# Запуск всех задач
async def main():
    # Создаём фоновую задачу на обновление клеток
    asyncio.create_task(update_my_cells_periodically())
    # Стартуем прослушку WebSocket
    await listen()

if __name__ == "__main__":
    asyncio.run(main())