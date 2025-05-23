import os
import pandas as pd
import logging
import time

# Настройка логов в корневом каталоге проекта BIGdata/logs
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../logs'))
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "autotest.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def list_xlsx_files(directory):
    return [f for f in os.listdir(directory) if f.endswith(".xlsx")]

def choose_file(files, prompt):
    print(prompt)
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")
    while True:
        try:
            index = int(input("Введите номер файла: "))
            if 1 <= index <= len(files):
                return files[index - 1]
            else:
                print("Некорректный номер. Попробуйте снова.")
        except ValueError:
            print("Введите корректное число.")

def compare_ads(reference_df, test_df):
    matched = 0
    mismatched = 0
    total = 0
    details = []

    ref_dict = reference_df.set_index("url").to_dict(orient="index")
    test_dict = test_df.set_index("url").to_dict(orient="index")

    for url, ref_data in ref_dict.items():
        total += 1
        if url not in test_dict:
            details.append(f"[❌] Не найдено объявление: {url}")
            mismatched += 1
            continue

        test_data = test_dict[url]
        differences = []
        for field in ["floor", "price", "total_meters", "rooms_count"]:
            ref_val = ref_data.get(field)
            test_val = test_data.get(field)
            if ref_val != test_val:
                differences.append(f"{field}: эталон={ref_val}, найдено={test_val}")

        if differences:
            details.append(f"[⚠️] Несовпадение в {url}:\n    " + "\n    ".join(differences))
            mismatched += 1
        else:
            matched += 1

    return total, matched, mismatched, details

def main():
    logging.info("🚀 Запуск автотеста сравнения объявлений")
    start_time = time.time()

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    atest_dir = os.path.join(BASE_DIR, "atest")
    raw_dir = os.path.join(BASE_DIR, "raw")

    atest_files = list_xlsx_files(atest_dir)
    raw_files = list_xlsx_files(raw_dir)

    if not atest_files:
        print("❌ В папке 'atest' нет .xlsx файлов")
        return
    if not raw_files:
        print("❌ В папке 'raw' нет .xlsx файлов")
        return

    ref_file = choose_file(atest_files, "Выберите эталонный файл из папки 'atest':")
    test_file = choose_file(raw_files, "Выберите файл парсера из папки 'raw':")

    ref_path = os.path.join(atest_dir, ref_file)
    test_path = os.path.join(raw_dir, test_file)

    try:
        reference_df = pd.read_excel(ref_path)
        test_df = pd.read_excel(test_path)
    except Exception as e:
        logging.error(f"Ошибка при чтении файлов: {e}")
        print(f"❌ Ошибка при чтении файлов: {e}")
        return

    required_cols = ["url", "floor", "price", "total_meters", "rooms_count"]
    if not all(col in reference_df.columns for col in required_cols):
        print(f"❌ Эталонный файл должен содержать колонки: {required_cols}")
        return
    if not all(col in test_df.columns for col in required_cols):
        print(f"❌ Файл парсера должен содержать колонки: {required_cols}")
        return

    print(f"\n📘 Эталонный файл: {ref_file} содержит {len(reference_df)} объявлений")
    print(f"📗 Файл парсера: {test_file} содержит {len(test_df)} объявлений\n")

    logging.info(f"Сравнение файлов: эталон = {ref_file}, проверяемый = {test_file}")
    logging.info(f"Объявлений в эталонном файле: {len(reference_df)}")
    logging.info(f"Объявлений в проверяемом файле: {len(test_df)}")

    total, matched, mismatched, details = compare_ads(reference_df, test_df)

    print(f"🔍 Проверено объявлений: {total}")
    print(f"✅ Совпадают: {matched}")
    print(f"❌ Не совпадают / не найдены: {mismatched}\n")
    for d in details:
        print(d)

    end_time = time.time()
    duration = end_time - start_time
    mins, secs = divmod(duration, 60)

    log_message = (
        f"\n📊 Итоги автотеста:\n"
        f"  Эталонный файл: {ref_file} ({len(reference_df)} объявлений)\n"
        f"  Файл парсера: {test_file} ({len(test_df)} объявлений)\n"
        f"  Всего проверено: {total}\n"
        f"  Совпало: {matched}\n"
        f"  Не совпало/не найдено: {mismatched}\n"
        f"  Время выполнения: {int(mins)} мин {int(secs)} сек\n"
    )
    logging.info(log_message)
    for entry in details:
        logging.info(entry)

if __name__ == "__main__":
    main()
