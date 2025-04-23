import requests
import time
import json

# Константы
MAP_URL = "https://api-game.gramilla.world/currentMap"
USER_ID = 21625
HOME_HEX = 19035

def fetch_map_data():
    try:
        response = requests.get(MAP_URL)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Ошибка при получении карты: {e}")
        return None

def parse_cells(data):
    my_home = None
    my_cells = []

    for cell in data.get("cells", []):
        if cell.get("user_id") == USER_ID:
            if cell.get("is_home"):
                my_home = cell
            if cell.get("home_hex") == HOME_HEX:
                my_cells.append(cell)

    return my_home, my_cells

def print_summary(home, cells):
    print("\n📍 Домашняя клетка:")
    if home:
        print(json.dumps(home, indent=4, ensure_ascii=False))
    else:
        print("Домашняя клетка не найдена.")

    print(f"\n🧩 Всего клеток в территории: {len(cells)}")
    for cell in cells:
        print(f"  - ID: {cell['id']} | Коорд: ({cell['x']}, {cell['y']}) | HP: {cell['hp']}/{cell['max_hp']} | Под атакой: {cell['under_attack']}")

if __name__ == "__main__":
    while True:
        map_data = fetch_map_data()
        if map_data:
            home_cell, territory_cells = parse_cells(map_data)
            print_summary(home_cell, territory_cells)
        time.sleep(30)  # Проверять карту каждые 30 секунд
