import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import Delaunay

def calculate_exact_volumes(points, z_target):
    """Рассчитывает объемы выемки и насыпи."""
    xy = points[:, :2]
    tri = Delaunay(xy)
    
    total_cut = 0.0
    total_fill = 0.0
    
    for simplex in tri.simplices:
        p1, p2, p3 = points[simplex]
        z1, z2, z3 = p1[2], p2[2], p3[2]
        
        area = 0.5 * abs((p2[0]-p1[0])*(p3[1]-p1[1]) - (p3[0]-p1[0])*(p2[1]-p1[1]))
        if area == 0:
            continue
            
        h1, h2, h3 = z1 - z_target, z2 - z_target, z3 - z_target
        
        if h1 >= 0 and h2 >= 0 and h3 >= 0:
            total_cut += area * (h1 + h2 + h3) / 3.0
        elif h1 <= 0 and h2 <= 0 and h3 <= 0:
            total_fill += area * abs(h1 + h2 + h3) / 3.0
        else:
            z_avg = (z1 + z2 + z3) / 3.0
            if z_avg >= z_target:
                total_cut += area * (z_avg - z_target)
            else:
                total_fill += area * (z_target - z_avg)
                
    return total_cut, total_fill, tri

def export_to_vrml(points, tri, z_target, vrml_path):
    """Экспорт модели в VRML с плоскостями, указателями точек и вертикальной линейкой высот/глубин."""
    easting, northing, elevation = points[:, 0], points[:, 1], points[:, 2]
    xmin, xmax = easting.min(), easting.max()
    ymin, ymax = northing.min(), northing.max()
    z_min, z_max = elevation.min(), elevation.max()
    idx_min, idx_max = np.argmin(elevation), np.argmax(elevation)
    p_min, p_max = points[idx_min], points[idx_max]
    
    # Смещение для линейки (рядом с углом рельефа)
    dx = xmax - xmin
    dy = ymax - ymin
    offset_x = xmin - (dx * 0.05 if dx > 0 else 1.0)
    offset_y = ymin - (dy * 0.05 if dy > 0 else 1.0)
    tick_length = max(dx, dy) * 0.03 if max(dx, dy) > 0 else 0.5
    
    with open(vrml_path, "w", encoding="utf-8") as f:
        f.write("#VRML V2.0 utf8\n\n")
        f.write("Transform {\n")
        f.write("  rotation 1 0 0 -1.5707963\n")
        f.write("  children [\n")
        f.write("    Group {\n")
        f.write("      children [\n")
        
        # 1. Поверхность рельефа (непрозрачная)
        f.write("        # Поверхность рельефа\n")
        f.write("        Shape {\n")
        f.write("          appearance Appearance { material Material { diffuseColor 0.6 0.6 0.6 transparency 0.0 } }\n")
        f.write("          geometry IndexedFaceSet {\n")
        f.write("            solid TRUE\n")
        f.write("            creaseAngle 0.5\n")
        f.write("            coord Coordinate { point [\n")
        for x, y, z in zip(easting, northing, elevation):
            f.write(f"              {x:.3f} {y:.3f} {z:.3f},\n")
        f.write("            ] }\n")
        f.write("            coordIndex [\n")
        for simplex in tri.simplices:
            f.write(f"              {simplex[0]}, {simplex[1]}, {simplex[2]}, -1,\n")
        f.write("            ]\n")
        f.write("          }\n")
        f.write("        },\n")
        
        # 2. Сечения/Плоскости
        planes = [(z_target, "0.2 0.8 0.2", 0.5, "Target"), (z_min, "0.1 0.2 0.8", 0.7, "Min"), (z_max, "0.8 0.2 0.2", 0.7, "Max")]
        for z_val, color, transp, name in planes:
            f.write(f"        # Плоскость {name}\n")
            f.write("        Shape {\n")
            f.write(f"          appearance Appearance {{ material Material {{ diffuseColor {color} transparency {transp} }} }}\n")
            f.write("          geometry IndexedFaceSet {\n")
            f.write("            coord Coordinate { point [\n")
            f.write(f"              {xmin:.3f} {ymin:.3f} {z_val:.3f}, {xmax:.3f} {ymin:.3f} {z_val:.3f}, {xmax:.3f} {ymax:.3f} {z_val:.3f}, {xmin:.3f} {ymax:.3f} {z_val:.3f},\n")
            f.write("            ] }\n")
            f.write("            coordIndex [ 0, 1, 2, 3, -1 ]\n")
            f.write("          }\n")
            f.write("        },\n")
            
        # 3. Указатели экстремумов (конусы повернуты на 90 градусов по оси Y)
        f.write("        # Стрелка минимума (синяя)\n")
        f.write(f"        Transform {{ translation {p_min[0]:.3f} {p_min[1]:.3f} {p_min[2]+2.0:.3f} rotation 0 1 0 1.5708 children [\n")
        f.write("          Shape { appearance Appearance { material Material { diffuseColor 0 0 1 } } geometry Cone { bottomRadius 0.5 height 1.5 } }\n")
        f.write("        ] } ,\n")
        f.write("        # Стрелка максимума (красная)\n")
        f.write(f"        Transform {{ translation {p_max[0]:.3f} {p_max[1]:.3f} {p_max[2]-2.0:.3f} rotation 0 1 0 -1.5708 children [\n")
        f.write("          Shape { appearance Appearance { material Material { diffuseColor 1 0 0 } } geometry Cone { bottomRadius 0.5 height 1.5 } }\n")
        f.write("        ] },\n")
        
        # 4. Линейка высот и глубин (Vertical Ruler Scale)
        f.write("        # Шкала / Линейка высот и глубин\n")
        f.write("        Shape {\n")
        f.write("          appearance Appearance { material Material { emissiveColor 1 1 1 } }\n")
        f.write("          geometry IndexedLineSet {\n")
        f.write("            coord Coordinate { point [\n")
        f.write(f"              {offset_x:.3f} {offset_y:.3f} {z_min:.3f},\n")
        f.write(f"              {offset_x:.3f} {offset_y:.3f} {z_max:.3f},\n")
        
        z_range = z_max - z_min
        step = 0.5 if z_range <= 5.0 else (1.0 if z_range <= 15.0 else 2.0)
        ticks = np.arange(np.floor(z_min/step)*step, np.ceil(z_max/step)*step + step/2, step)
        ticks = [t for t in ticks if z_min <= t <= z_max]
        if z_target not in ticks and z_min <= z_target <= z_max:
            ticks.append(z_target)
        ticks = sorted(list(set(ticks)))
        
        line_indices = ["0, 1, -1"]
        pt_idx = 2
        for t_z in ticks:
            f.write(f"              {offset_x:.3f} {offset_y:.3f} {t_z:.3f},\n")
            f.write(f"              {offset_x - tick_length:.3f} {offset_y:.3f} {t_z:.3f},\n")
            line_indices.append(f"{pt_idx}, {pt_idx+1}, -1")
            pt_idx += 2
            
        f.write("            ] }\n")
        f.write("            coordIndex [\n")
        for idx_str in line_indices:
            f.write(f"              {idx_str},\n")
        f.write("            ]\n")
        f.write("          }\n")
        f.write("        },\n")
        
        # Подписи (Text) для ключевых отметок на линейке
        text_labels = [
            (z_max, f"Max: {z_max:.2f}m (h={z_max - z_target:+.2f}m)", "1 0.2 0.2"),
            (z_target, f"Target: {z_target:.2f}m (0.00m)", "0.2 0.8 0.2"),
            (z_min, f"Min: {z_min:.2f}m (d={z_min - z_target:+.2f}m)", "0.2 0.4 1")
        ]
        
        text_size = max(dx, dy) * 0.025 if max(dx, dy) > 0 else 0.4
        for z_val, label_str, color_str in text_labels:
            f.write(f"        Transform {{ translation {offset_x - tick_length*1.5:.3f} {offset_y:.3f} {z_val:.3f} rotation 1 0 0 1.5708 children [\n")
            f.write("          Shape {\n")
            f.write(f"            appearance Appearance {{ material Material {{ diffuseColor {color_str} emissiveColor {color_str} }} }}\n")
            f.write("            geometry Text {\n")
            f.write(f"              string [ \"{label_str}\" ]\n")
            f.write(f"              fontStyle FontStyle {{ size {text_size:.3f} justify [ \"RIGHT\", \"MIDDLE\" ] }}\n")
            f.write("            }\n")
            f.write("          }\n")
            f.write("        ] },\n")

        f.write("      ]\n")
        f.write("    }\n")
        f.write("  ]\n")
        f.write("}\n")

def main():
    parser = argparse.ArgumentParser(description="Расчет объемов и генерация 3D модели.")
    parser.add_argument("file", help="Путь к CSV")
    parser.add_argument("target", nargs="?", type=float, default=None, help="Проектная высота (если не указана, берется наивысшая точка)")
    args = parser.parse_args()
    
    input_path = Path(args.file)
    df = pd.read_csv(input_path)
    points = df[['Easting', 'Northing', 'Elevation']].values
    
    elevation = points[:, 2]
    z_min, z_max = elevation.min(), elevation.max()
    z_p5, z_p95 = np.percentile(elevation, 5), np.percentile(elevation, 95)
    
    z_target = args.target if args.target is not None else z_max
    
    print(f"Самая низкая точка (Min): {z_min:.4f} м")
    print(f"Самая высокая точка (Max): {z_max:.4f} м")
    print(f"Диапазон господствующих высот (90% точек, 5%–95%): от {z_p5:.4f} м до {z_p95:.4f} м")
    
    if args.target is None:
        print(f"Проектная высота не задана. Автоматически установлена по наивысшей точке: {z_target:.4f} м")
    else:
        print(f"Проектная высота (Target): {z_target:.4f} м")

    cut, fill, tri = calculate_exact_volumes(points, z_target)
    vrml_path = input_path.with_suffix('.wrl')
    export_to_vrml(points, tri, z_target, vrml_path)
    
    print(f"Выемка: {cut:.4f} м³, Насыпь: {fill:.4f} м³")
    print(f"VRML файл создан: {vrml_path}")

if __name__ == "__main__":
    main()