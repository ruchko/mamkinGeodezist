import csv
import os
import sys

def parse_sdr(file_path):
    points = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()
            
    for line in lines:
        line_str = line.strip()
        # Проверяем, что строка относится к координатам (начинается с 08 или содержит POS)
        if line_str.startswith('08') or 'POS' in line_str:
            # Поддерживаем разделение как запятыми, так и пробелами/табуляцией
            if ',' in line_str:
                parts = [p.strip() for p in line_str.split(',')]
            else:
                parts = line_str.split()
                
            try:
                # Если первая часть содержит тег (например '08TP' или '08'), 
                # то имя точки обычно во второй позиции, а координаты дальше
                if len(parts) >= 5:
                    point_id = parts[1]
                    easting = float(parts[2])
                    northing = float(parts[3])
                    elevation = float(parts[4])
                    points.append([point_id, easting, northing, elevation])
            except (IndexError, ValueError):
                continue
                
        # Альтернативный вариант для стандартных строк SDR (если данные идут с фиксированной длиной)
        elif len(line_str) >= 54 and line_str.startswith(('02', '08', '18')):
            try:
                # Пример для стандартного SDR формата со срезом по позициям символов:
                name = line_str[4:8].strip() if len(line_str.strip()) < 20 else line_str[4:16].strip()
                # Попробуем извлечь числа из строки, если они идут блоками
                # Но проще проверить, есть ли пробелы
                pass
            except Exception:
                continue
                
    return points

def write_csv(points, output_path):
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['PointID', 'Easting', 'Northing', 'Elevation'])
        writer.writerows(points)

def main():
    input_sdr = sys.argv[1] if len(sys.argv) > 1 else 'exampleInput.sdr'
    
    if len(sys.argv) > 2:
        output_csv = sys.argv[2]
    else:
        base = os.path.splitext(input_sdr)[0]
        output_csv = f"{base}.csv"
        
    if not os.path.exists(input_sdr):
        print(f"Ошибка: Файл '{input_sdr}' не найден.")
        return

    points = parse_sdr(input_sdr)
    
    # Если через запятую/пробелы ничего не нашлось, попробуем классический парсер по фиксированным позициям SDR33
    if not points:
        print("Строки с разделителями не найдены, пробуем парсить SDR по фиксированным позициям...")
        with open(input_sdr, 'r', encoding='latin-1') as f:
            for line in f:
                if line.startswith(('02', '08', '18')):
                    try:
                        if len(line) >= 68: # SDR33
                            name = line[4:20].strip()
                            north = float(line[20:36])
                            east = float(line[36:52])
                            elev = float(line[52:68])
                            points.append([name, east, north, elev])
                        elif len(line) >= 38: # SDR2x
                            name = line[4:8].strip()
                            north = float(line[8:18])
                            east = float(line[18:28])
                            elev = float(line[28:38])
                            points.append([name, east, north, elev])
                    except ValueError:
                        continue

    write_csv(points, output_csv)
    print(f"Конвертировано {len(points)} точек из '{input_sdr}' в '{output_csv}'")

if __name__ == "__main__":
    main()