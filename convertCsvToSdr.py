import csv
from datetime import datetime
import sys


def convert_csv_to_sdr33(csv_filename):
  unique_points = {}

  with open(csv_filename, mode='r', encoding='utf-8') as f:
    sample = f.read(2048)
    f.seek(0)
    delimiter = ';' if ';' in sample else ','

    reader = csv.DictReader(f, delimiter=delimiter)

    for row in reader:
      row = {k.strip(): v.strip() for k, v in row.items() if k}

      pt_id = (
          row.get('Name')
          or row.get('PointID')
          or row.get('Taškas')
          or row.get('ID')
      )
      x_val = row.get('X')
      y_val = row.get('Y')
      z_val = row.get('Z') or row.get('H') or '0.000'

      if pt_id and x_val and y_val:
        unique_points[pt_id] = {
            'x': float(x_val),
            'y': float(y_val),
            'z': float(z_val),
        }

  current_time = datetime.now()
  date_str = current_time.strftime('%y-%m-%d')
  time_str = current_time.strftime('%H:%M:%S')

  sdr_lines = [
      f'HDR01ON     000000 {date_str} {time_str}',
      'HDR02SDR33-CSV-CONVERTER                  ',
      f'COM03Converted on {date_str} {time_str}',
  ]

  for pt_id, coords in sorted(
      unique_points.items(),
      key=lambda x: int(x[0]) if x[0].isdigit() else str(x[0]),
  ):
    line = f"COORD02 {pt_id:<16} {coords['x']:12.3f} {coords['y']:12.3f} {coords['z']:10.3f}"
    sdr_lines.append(line)

  sdr_lines.append('EOR00')

  output_filename = csv_filename.rsplit('.', 1)[0] + '.sdr'
  with open(output_filename, 'w', encoding='utf-8') as f:
    f.write('\n'.join(sdr_lines) + '\n')

  print(f'Файл успешно создан: {output_filename}')
  print(f'Всего уникальных точек записано: {len(unique_points)}')


if __name__ == '__main__':
  if len(sys.argv) < 2:
    print('Использование: python convertCsvToSdr.py <путь_к_файлу.csv>')
    sys.exit(1)

  csv_file = sys.argv[1]
  convert_csv_to_sdr33(csv_file)