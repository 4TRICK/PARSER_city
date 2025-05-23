import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.ticker as mtick
import numpy as np
import sys

# Настройки путей
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project/
INPUT_FILENAME = os.path.join(BASE_DIR, 'raw', 'final', 'Данные_по_курсачу.xlsx')
FILTER_FILENAME = os.path.join(BASE_DIR, 'filters.txt')
RESULTS_DIR = os.path.join(BASE_DIR, 'figures')
README_FILENAME = os.path.join(RESULTS_DIR, 'readME.txt')
os.makedirs(RESULTS_DIR, exist_ok=True)

# Очистка файла readME.txt перед началом работы
with open(README_FILENAME, 'w', encoding='utf-8') as f:
    f.write("Результаты анализа данных по недвижимости\n")
    f.write("=" * 50 + "\n\n")

# Загрузка данных
try:
    df = pd.read_excel(INPUT_FILENAME)
    df = df.dropna(subset=['price', 'total_meters'])
    df['price_per_m2'] = df['price'] / df['total_meters']
except Exception as e:
    print(f"Ошибка при загрузке данных: {e}")
    exit()


# Применение фильтров
def apply_filters(df):
    if not os.path.exists(FILTER_FILENAME):
        return df
    try:
        with open(FILTER_FILENAME, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        filters = {}
        current_task = None
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                current_task = line.strip('#').strip('.').strip()
                filters[current_task] = []
            elif line and current_task:
                filters[current_task].append(line)
        for task, values in filters.items():
            for val in values:
                if 'комн' in val:
                    df = df[~((df['rooms_count'].astype(str) + ' комн. кв-ра').str.contains(val.split('!')[0].strip()))]
                elif val in df['district'].values:
                    df = df[df['district'] != val]
    except Exception as e:
        print(f"Ошибка при применении фильтров: {e}")
    return df


df = apply_filters(df)

# Сброс стилей
sns.set(style='whitegrid', font_scale=1.1)


# Сохраняем график и добавляем описание в README
def save_plot(fig, task_number, description):
    try:
        fig.savefig(os.path.join(RESULTS_DIR, f"task_{task_number}.png"), bbox_inches='tight')
        plt.close(fig)
        with open(README_FILENAME, 'a', encoding='utf-8') as f:
            f.write(f"Задание {task_number}:\n{description}\n\n")
    except Exception as e:
        print(f"Ошибка при сохранении графика {task_number}: {e}")


# Функция для форматирования цен
def format_price(x, pos):
    if x == 0 or x == 0.0:
        return '0'
    elif x % 1_000_000 == 0:
        return f'{int(x / 1_000_000)} млн'
    else:
        return f'{x / 1_000_000:.1f} млн'


# 1. Топ-5 самых дорогих квартир по районам и метро
try:
    top_districts = df.groupby('district')['price'].max().sort_values(ascending=False).head(5).index

    top_flats_by_district = []
    for district in top_districts:
        district_data = df[df['district'] == district].sort_values('price', ascending=False)
        unique_metro = set()
        count = 0
        for _, row in district_data.iterrows():
            metro = row['underground']
            if metro not in unique_metro:
                unique_metro.add(metro)
                top_flats_by_district.append({
                    'district': district,
                    'underground': metro,
                    'price': row['price'],
                    'address': row.get('address', 'N/A')
                })
                count += 1
            if count == 2:
                break

    top_flats_df = pd.DataFrame(top_flats_by_district)

    fig1, ax1 = plt.subplots(figsize=(16, 10))
    colors = plt.cm.tab10.colors
    bar_positions = []
    metro_labels = []

    for i, district in enumerate(top_districts):
        district_data = top_flats_df[top_flats_df['district'] == district]
        x_min = i - 0.4
        x_max = i + 0.4 + (len(district_data) - 1) * 0.2
        rect = plt.Rectangle((x_min, 0), x_max - x_min, district_data['price'].max() * 1.05,
                             alpha=0.1, color=colors[i], label=district)
        ax1.add_patch(rect)

        ax1.text(x_min + (x_max - x_min) / 2, district_data['price'].max() * 1.08, district,
                 ha='center', va='bottom', fontsize=12, fontweight='bold')

        for j, (_, row) in enumerate(district_data.iterrows()):
            bar_positions.append((i - 0.4 + j * 0.2, row['price']))
            metro_labels.append(row['underground'])

    bars = ax1.bar([pos[0] for pos in bar_positions], [pos[1] for pos in bar_positions],
                   width=0.2, color='tab:blue', alpha=0.7)

    for pos, bar in zip(bar_positions, bars):
        ax1.text(bar.get_x() + bar.get_width() / 2, pos[1], format_price(pos[1], None),
                 ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax1.set_title('Топ-5 самых дорогих квартир по районам и метро', pad=20)
    ax1.set_ylabel('Цена')
    ax1.yaxis.set_major_formatter(mtick.FuncFormatter(format_price))
    ax1.legend(title='Район', bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.set_xticks([pos[0] for pos in bar_positions])
    ax1.set_xticklabels(metro_labels, rotation=90, fontsize=9)
    ax1.set_xlabel('Метро')

    # Формируем подробное описание для README
    district_info = []
    for d in top_districts:
        max_price = int(top_flats_df[top_flats_df['district'] == d]['price'].max() / 1_000_000)
        metro_list = top_flats_df[top_flats_df['district'] == d]['underground'].unique()
        metro_prices = [
            f"{m}: {int(top_flats_df[(top_flats_df['district'] == d) & (top_flats_df['underground'] == m)]['price'].max() / 1_000_000)} млн"
            for m in metro_list
        ]
        district_info.append(f"- {d}: максимальная цена {max_price} млн руб. (метро: {', '.join(metro_prices)})")

    description = "Топ-5 районов по максимальной цене квартиры.\n\nИнформация по районам:\n" + "\n".join(district_info)

    save_plot(fig1, 1, description)
except Exception as e:
    print(f"Ошибка при создании графика 1: {e}")

# 2. Цена за м² Новостройка/Вторичка с разницей (без 5% выбросов)
try:
    filtered_df = df.copy()
    for prop_type in filtered_df['type_property'].unique():
        subset = filtered_df[filtered_df['type_property'] == prop_type]
        lower_bound = subset['price_per_m2'].quantile(0.05)
        upper_bound = subset['price_per_m2'].quantile(0.95)
        filtered_df = filtered_df[~((filtered_df['type_property'] == prop_type) &
                                    ((filtered_df['price_per_m2'] < lower_bound) |
                                     (filtered_df['price_per_m2'] > upper_bound)))]

    mean_price = filtered_df.groupby('type_property')['price_per_m2'].mean()
    diff = abs(mean_price.diff().iloc[-1])

    # Округление до 10 тысяч
    mean_price_rounded = mean_price.apply(lambda x: round(x / 10000) * 10000)
    diff_rounded = round(diff / 10000) * 10000

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    sns.barplot(x=mean_price.index, y=mean_price.values, ax=ax2)
    for i, val in enumerate(mean_price):
        ax2.text(i, val, f"{int(val / 1000)} тыс.", ha='center', va='bottom')
    ax2.bar(1, diff, bottom=mean_price.iloc[0], color='purple')
    ax2.text(1, mean_price.iloc[0] + diff / 2, f"+{int(diff / 1000)} тыс.", ha='center', va='center', color='white',
             fontsize=10)
    ax2.set_title('Цена за м² (тыс. руб.): Новостройка vs Вторичка с разницей (без 5% выбросов)')
    ax2.set_xlabel('Тип недвижимости')
    ax2.set_ylabel('Цена за м², тыс. руб.')

    # Формируем подробное описание для README
    description = (
        "Сравнение цены за м² между новостройками и вторичкой с удалением 5% выбросов.\n"
        "Цены округлены до 10 тысяч:\n"
        f"- Новостройка: {int(mean_price_rounded.iloc[0] / 1000)} тыс. руб./м²\n"
        f"- Вторичка: {int(mean_price_rounded.iloc[1] / 1000)} тыс. руб./м²\n"
        f"Разница: {int(diff_rounded / 1000)} тыс. руб./м²"
    )

    save_plot(fig2, 2, description)
except Exception as e:
    print(f"Ошибка при создании графика 2: {e}")

# 3. Топ-5 улиц по средней цене квартиры
try:
    street_avg = df.groupby('street')['price'].mean()
    top5_streets = street_avg.sort_values(ascending=False).head(5)
    bottom5_streets = street_avg.sort_values().head(5)

    fig4 = plt.figure(figsize=(14, 12))
    ax4_1 = plt.subplot(2, 1, 1)
    top5_streets.plot(kind='bar', ax=ax4_1)
    for i, v in enumerate(top5_streets):
        ax4_1.text(i, v, format_price(v, None), ha='center', va='bottom')
    ax4_1.set_title('Топ-5 дорогих улиц (средняя цена квартиры)')
    ax4_1.set_ylabel('Цена')
    ax4_1.set_xlabel('Улица')
    ax4_1.yaxis.set_major_formatter(mtick.FuncFormatter(format_price))

    ax4_2 = plt.subplot(2, 1, 2)
    bottom5_streets.plot(kind='bar', ax=ax4_2)
    for i, v in enumerate(bottom5_streets):
        ax4_2.text(i, v, format_price(v, None), ha='center', va='bottom')
    ax4_2.set_title('Топ-5 дешёвых улиц (средняя цена квартиры)')
    ax4_2.set_ylabel('Цена')
    ax4_2.set_xlabel('Улица')
    ax4_2.yaxis.set_major_formatter(mtick.FuncFormatter(format_price))
    ax4_2.set_yticks([i * 500_000 for i in range(0, int(max(bottom5_streets) / 500_000) + 2)])

    plt.tight_layout()

    # Формируем подробное описание для README
    top_streets_info = [f"{i + 1}. {street}: {int(price / 1_000_000)} млн руб."
                        for i, (street, price) in enumerate(top5_streets.items())]
    bottom_streets_info = [f"{i + 1}. {street}: {int(price / 1_000_000)} млн руб."
                           for i, (street, price) in enumerate(bottom5_streets.items())]

    description = (
            "Средняя цена квартиры на улицах.\n\n"
            "Топ-5 дорогих улиц:\n" + "\n".join(top_streets_info) + "\n\n"
                                                                    "Топ-5 дешёвых улиц:\n" + "\n".join(
        bottom_streets_info)
    )

    save_plot(fig4, 3, description)
except Exception as e:
    print(f"Ошибка при создании графика 3: {e}")

# 4. Этажи в многоквартирных домах (по средней цене квартиры)
try:
    multi_floors = df[df['floors_count'] > 1]
    mean_by_floor = multi_floors.groupby('floor')['price'].mean()

    top5_cheapest_floors = mean_by_floor.sort_values().head(5)
    top5_expensive_floors = mean_by_floor.sort_values(ascending=False).head(5)

    fig6, ax6 = plt.subplots(1, 2, figsize=(16, 6))
    top5_cheapest_floors.plot(kind='bar', ax=ax6[0], color='blue')
    top5_expensive_floors.plot(kind='bar', ax=ax6[1], color='green')

    for i, v in enumerate(top5_cheapest_floors):
        ax6[0].text(i, v, format_price(v, None), ha='center', va='bottom')
    for i, v in enumerate(top5_expensive_floors):
        ax6[1].text(i, v, format_price(v, None), ha='center', va='bottom')

    ax6[0].set_title('Топ-5 дешёвых этажей')
    ax6[1].set_title('Топ-5 дорогих этажей')
    ax6[0].set_ylabel('Цена')
    ax6[1].set_ylabel('Цена')
    ax6[0].set_xlabel('Этаж')
    ax6[1].set_xlabel('Этаж')

    for ax in ax6:
        ax.yaxis.set_major_formatter(mtick.FuncFormatter(format_price))

    # Формируем подробное описание для README
    cheap_floors_info = [f"{i + 1}. {floor} этаж: {int(price / 1_000_000)} млн руб."
                         for i, (floor, price) in enumerate(top5_cheapest_floors.items())]
    expensive_floors_info = [f"{i + 1}. {floor} этаж: {int(price / 1_000_000)} млн руб."
                             for i, (floor, price) in enumerate(top5_expensive_floors.items())]

    description = (
            "Средняя цена квартиры по этажам в многоквартирных домах.\n\n"
            "Самые дорогие этажи:\n" + "\n".join(expensive_floors_info) + "\n\n"
                                                                          "Самые дешёвые этажи:\n" + "\n".join(
        cheap_floors_info)
    )

    save_plot(fig6, 4, description)
except Exception as e:
    print(f"Ошибка при создании графика 4: {e}")

# Список районов, которые нужно убрать
districts_to_remove = [
    "1 комн. кв-ра в развитом е!1-комн. квартира",
    "1 комн. кв-ра в зеленом е!1-комн. квартира",
    "1к-квартира в Московском е1-комн. квартира",
    "2 комн. кв-ра в развитом е!2-комн. квартира",
    "Двушка у парка в Невском е2-комн. квартира",
    "Евродвушка в Московском е1-комн. квартира",
    "Квартира-студия в Приморском еСтудия",
    "Просторная 1 ккв  Приморский 1-комн. квартира",
    "Студия в развитом е!Студия",
    "Студия в Московском е!Студия"
]

# Фильтруем данные для 5-го и 6-го графиков
filtered_df_for_graphs = df[~df['district'].isin(districts_to_remove)]

# 5. Дешёвые предложения по районам и типу (улучшенная версия)
try:
    fig7, ax7 = plt.subplots(figsize=(14, 8))

    # Строим график
    sns.barplot(data=filtered_df_for_graphs, x='district', y='price', hue='type_property',
                ax=ax7, estimator='mean', errorbar=None)

    # Находим глобальные мин и макс цены для каждого типа
    global_min_max = filtered_df_for_graphs.groupby('type_property')['price'].agg(['min', 'max']).reset_index()

    # Добавляем информацию о мин/макс в легенду с точными значениями
    handles, labels = ax7.get_legend_handles_labels()
    new_labels = []
    for i, row in global_min_max.iterrows():
        min_val = row['min'] / 1_000_000
        max_val = row['max'] / 1_000_000
        min_str = f"{min_val:.1f}" if min_val % 1 != 0 else f"{int(min_val)}"
        max_str = f"{max_val:.1f}" if max_val % 1 != 0 else f"{int(max_val)}"
        new_labels.append(f"{row['type_property']} (мин: {min_str} млн, макс: {max_str} млн)")

    # Перемещаем легенду в верхний правый угол
    ax7.legend(handles, new_labels, title='Тип недвижимости',
               bbox_to_anchor=(1.05, 1), loc='upper left')

    # Настраиваем отображение
    ax7.set_title('Средняя цена квартир по районам и типу недвижимости')
    ax7.set_ylabel('Цена')
    ax7.set_xlabel('Район')
    ax7.yaxis.set_major_formatter(mtick.FuncFormatter(format_price))
    plt.xticks(rotation=90)
    plt.tight_layout()

    # Формируем подробное описание для README
    type_stats = []
    for _, row in global_min_max.iterrows():
        min_val = int(row['min'] / 1_000_000)
        max_val = int(row['max'] / 1_000_000)
        type_stats.append(f"- {row['type_property']}: от {min_val} млн до {max_val} млн руб.")

    district_avg = filtered_df_for_graphs.groupby('district')['price'].mean().sort_values(ascending=False)
    top_districts = [f"{district}: {int(price / 1_000_000)} млн руб."
                     for district, price in district_avg.head(5).items()]

    description = (
            "Средняя цена по районам и типу недвижимости.\n\n"
            "Диапазон цен по типам недвижимости:\n" + "\n".join(type_stats) + "\n\n"
                                                                              "Топ-5 самых дорогих районов:\n" + "\n".join(
        top_districts)
    )

    save_plot(fig7, 5, description)
except Exception as e:
    print(f"Ошибка при создании графика 5: {e}")

# 6. Средняя цена по районам и городу
try:
    city_avg = filtered_df_for_graphs['price'].mean()
    district_avg = filtered_df_for_graphs.groupby('district')['price'].mean()
    fig8, ax8 = plt.subplots()
    district_avg.plot(kind='bar', ax=ax8)
    ax8.axhline(city_avg, color='red', linestyle='--',
                label=f'Средняя по городу: {format_price(city_avg, None)} руб.')
    ax8.set_title('Средняя цена квартиры по районам')
    ax8.set_ylabel('Цена')
    ax8.set_xlabel('Район')
    ax8.yaxis.set_major_formatter(mtick.FuncFormatter(format_price))
    ax8.legend()

    # Формируем подробное описание для README
    above_avg = district_avg[district_avg > city_avg].sort_values(ascending=False)
    below_avg = district_avg[district_avg <= city_avg].sort_values()

    above_info = [f"{district}: {int(price / 1_000_000)} млн руб. (+{int((price - city_avg) / 1_000_000)} млн)"
                  for district, price in above_avg.head(5).items()]
    below_info = [f"{district}: {int(price / 1_000_000)} млн руб. (-{int((city_avg - price) / 1_000_000)} млн)"
                  for district, price in below_avg.head(5).items()]

    description = (
            "Средняя цена по районам.\n"
            f"Средняя по городу: {int(city_avg / 1_000_000)} млн руб.\n\n"
            "Топ-5 районов выше среднего:\n" + "\n".join(above_info) + "\n\n"
                                                                       "Топ-5 районов ниже среднего:\n" + "\n".join(
        below_info)
    )

    save_plot(fig8, 6, description)
except Exception as e:
    print(f"Ошибка при создании графика 6: {e}")

# 7. Средняя цена по количеству комнат (полностью исправленная версия)
try:
    # Преобразуем rooms_count в целые числа, заменяем NaN на 0
    df['rooms_count'] = pd.to_numeric(df['rooms_count'], errors='coerce').fillna(0).astype(int)

    # Создаем категории
    conditions = [
        (df['rooms_count'] == 0),
        (df['rooms_count'] == 1),
        (df['rooms_count'] == 2),
        (df['rooms_count'] == 3),
        (df['rooms_count'] >= 4)
    ]
    choices = ['0', '1', '2', '3', '4+']
    df['rooms_cat'] = np.select(conditions, choices, default='4+')

    # Убедимся, что все категории существуют
    room_order = ['0', '1', '2', '3', '4+']
    room_labels = ['Студия', '1-комн.', '2-комн.', '3-комн.', '4+ комн.']

    # Группируем и считаем среднюю цену
    room_avg = df.groupby('rooms_cat')['price'].mean()

    # Добавляем отсутствующие категории (если таких данных нет)
    for cat in room_order:
        if cat not in room_avg.index:
            room_avg[cat] = 0
    room_avg = room_avg[room_order]

    # Создаем график
    fig9, ax9 = plt.subplots(figsize=(10, 6))
    bars = ax9.bar(room_order, room_avg.values)

    # Настраиваем подписи
    ax9.set_xticks(range(len(room_order)))
    ax9.set_xticklabels(room_labels)
    ax9.set_title('Средняя цена по количеству комнат')
    ax9.set_ylabel('Цена')
    ax9.yaxis.set_major_formatter(mtick.FuncFormatter(format_price))

    # Добавляем значения на столбцы
    for i, v in enumerate(room_avg):
        if pd.notna(v) and v > 0:
            ax9.text(i, v, format_price(v, None), ha='center', va='bottom', fontsize=10)

    # Формируем подробное описание для README
    room_prices = [
        f"- {room_labels[i]}: {int(price / 1_000_000)} млн руб."
        for i, price in enumerate(room_avg.values)
    ]

    description = (
            "Средняя цена квартиры по количеству комнат.\n"
            "Включая студии (0 комнат).\n\n" +
            "\n".join(room_prices)
    )

    save_plot(fig9, 7, description)
except Exception as e:
    print(f"Ошибка при создании графика 7: {e}")

print(f"Обработка завершена. Проверьте папку '{RESULTS_DIR}'")