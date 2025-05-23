import pandas as pd
import os
from tqdm import tqdm
import time


def merge_excel_files(output_filename="merged_data.xlsx"):
    start_time = time.time()  # Засекаем время начала

    # Получаем путь к папке raw (на один уровень выше от scripts)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    raw_dir = os.path.join(project_root, "raw")
    final_dir = os.path.join(raw_dir, "final")

    # Создаем папку final, если ее нет
    os.makedirs(final_dir, exist_ok=True)

    all_dataframes = []
    excel_files = [f for f in os.listdir(raw_dir) if f.endswith(".xlsx") and f != output_filename]

    print(f"🔍 Найдено {len(excel_files)} Excel-файлов в {raw_dir}")

    for file in tqdm(excel_files, desc="Обработка файлов", unit="file"):
        file_path = os.path.join(raw_dir, file)
        try:
            df = pd.read_excel(file_path)
            df['source_file'] = file  # добавить имя файла
            all_dataframes.append(df)
        except Exception as e:
            print(f"\n⚠️ Ошибка при чтении {file}: {e}")

    if all_dataframes:
        merged_df = pd.concat(all_dataframes, ignore_index=True)
        output_path = os.path.join(final_dir, output_filename)
        merged_df.to_excel(output_path, index=False)

        # Вычисляем время выполнения
        elapsed_time = time.time() - start_time
        print(f"\n✅ Готово! Объединено {len(all_dataframes)} файлов.")
        print(f"📁 Результат сохранен в: {output_path}")
        print(f"⏱ Время выполнения: {elapsed_time:.2f} секунд")
    else:
        print("\n❌ Не удалось прочитать ни один Excel-файл.")


if __name__ == "__main__":
    merge_excel_files()