from cianparser import CianParser
import pandas as pd
from tqdm import tqdm
import time
import os


def select_from_list(prompt, options):
    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")
    while True:
        try:
            choice = int(input("Введите номер варианта: "))
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print("Некорректный ввод. Попробуйте снова.")
        except ValueError:
            print("Введите число!")


def ensure_raw_directory_exists():
    # Поднимаемся на три уровня вверх от src/scripts/ до BIGdata/
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    raw_dir = os.path.join(project_root, 'raw')
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)
    return raw_dir


def generate_filename(city, deal_type, rooms, min_area, max_area):
    # Сокращения для городов
    city_abbr = {
        "Москва": "Msk",
        "Санкт-Петербург": "SPb",
        "Нижний Новгород": "NNov"
    }.get(city, city)

    # Тип недвижимости
    deal_type_abbr = "first" if deal_type.lower() == "новостройка" else "second"

    # Форматирование комнат
    if isinstance(rooms[0], str) and rooms[0] == "studio":
        room_str = "studio"
    else:
        room_str = "_".join(map(str, rooms))

    # Площадь
    area_str = f"({min_area}_{max_area})"

    return f"{city_abbr}_{deal_type_abbr}_{room_str}_{area_str}"


def main():
    start_time = time.time()

    available_cities = ["Москва", "Санкт-Петербург", "Нижний Новгород"]
    city = select_from_list("Выберите город:", available_cities)

    deal_type = select_from_list("Выберите тип недвижимости:", ["Новостройка", "Вторичка"])
    object_type = "new" if deal_type.lower() == "новостройка" else "secondary"

    room_options = ["Студия", "1", "2", "3", "4", "5"]
    print("Выберите типы комнат (через запятую):")
    for i, room in enumerate(room_options, start=1):
        print(f"{i}. {room}")
    selected_room_numbers = input("Введите номера через запятую, например: 1,2,3: ")
    room_indices = [int(i.strip()) for i in selected_room_numbers.split(",") if i.strip().isdigit()]
    selected_rooms = []
    for i in room_indices:
        if 1 <= i <= len(room_options):
            selected_rooms.append("studio" if room_options[i - 1] == "Студия" else int(room_options[i - 1]))

    try:
        min_area = int(input("Минимальная площадь (кв.м): "))
        max_area = int(input("Максимальная площадь (кв.м): "))
    except ValueError:
        print("Введено некорректное значение. Используем значения по умолчанию.")
        min_area = 0
        max_area = 250

    print(f"\nСобираем данные: {deal_type}, комнаты: {selected_rooms}, город: {city}")

    parser = CianParser(location=city)

    try:
        raw_dir = ensure_raw_directory_exists()
        base_filename = generate_filename(city, deal_type, selected_rooms, min_area, max_area)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{base_filename}_{timestamp}.xlsx"
        filepath = os.path.join(raw_dir, filename)

        print("\nНачинаем парсинг...")

        with tqdm(total=75, desc="Парсинг страниц", unit="страница") as pbar:
            data = parser.get_flats(
                deal_type="sale",
                rooms=tuple(selected_rooms),
                with_saving_csv=False,
                additional_settings={
                    "start_page": 1,
                    "end_page": 75,
                    "min_total_meters": min_area,
                    "max_total_meters": max_area,
                    "object_type": object_type,
                    "callback_after_iteration": lambda x: pbar.update(1)
                }
            )

        df = pd.DataFrame(data)
        df.to_excel(filepath, index=False)

        execution_time = time.time() - start_time
        mins, secs = divmod(execution_time, 60)

        print(f"\n✅ Успешно собрано {len(data)} объявлений.")
        print(f"⏱ Время выполнения: {int(mins)} мин {int(secs)} сек")
        print(f"💾 Файл сохранен в: {filepath}")

    except Exception as e:
        print(f"❌ Ошибка при сборе данных: {e}")


if __name__ == "__main__":
    main()