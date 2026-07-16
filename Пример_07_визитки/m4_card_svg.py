import FreeCAD
import Part
import os
import re
import importSVG

import m1_card_start
from m1_card_start import f_shape_multi_fuse, f_shape_fit_isometric, f_print

def f_current_folder():
    return os.path.dirname(os.path.abspath(__file__))
    
def f_add_mm(s):
    return re.sub(r'(width|height)="(\d+(?:\.\d+)?)"', r'\1="\2mm"', s)
    
def f_int_color(s):
    return int(re.search(r'fill="#([0-9A-Fa-f]{6})"', s).group(1), 16)

def f_read_file(full_filename):
    with open(full_filename, 'r', encoding='utf-8') as f:
        return f.read()
        
def f_pre_post_arr_pathes(svg_text):
    i = svg_text.index("<svg")
    j = svg_text.index(">", i) + 1
    svg_pre = f_add_mm(svg_text[i:j])

    k = svg_text.rindex("</svg>")
    svg_post = svg_text[k:k + 6]

    svg_paths = []
    svg_colors = []
    svg_files = []
    pos = j
    while True:
        try: a = svg_text.index("<path", pos)
        except ValueError: break
        b = svg_text.index("/>", a) + 2
        I_PATH = svg_text[a:b]
        svg_paths.append(I_PATH)
        svg_colors.append(f_int_color(I_PATH))
        svg_files.append(svg_pre + I_PATH + svg_post)
        pos = b

    return {"svg_pre": svg_pre, "svg_post": svg_post, "svg_paths": svg_paths, "svg_colors": svg_colors, "svg_files": svg_files}

def f_svg_to_shapes_without_colors(svg_text, doc, svg_temp_name = 'svg_file.svg', height = 10):
    full_path = os.path.join(f_current_folder(), svg_temp_name)
    # Записываем (перезаписываем, если существует)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(svg_text)
    importSVG.insert(full_path, doc.Name)
    
    imported = doc.Objects
    arr_shapes = []
    # генерируй все формы
    for obj in imported:
        if not hasattr(obj, "Shape"):
            continue
        for wire in obj.Shape.Wires:
            if not wire.isClosed():  # проволока не замкнута
                continue
            try:
                face = Part.Face(wire)
                v = FreeCAD.Vector(0,0,height)
                arr_shapes.append(face.extrude(v).copy())
            except Exception:
                pass
                
    # Удаляем все объекты Path
    for obj in list(doc.Objects):
        if obj.Name.startswith("Path"):
            doc.removeObject(obj.Name)
    os.remove(full_path)
    return arr_shapes
    
def f_is_shape_parent(shape_parent, shape_child, delta = 1e-6):
    if (shape_parent is None) or (shape_child is None): return False
    volume_fused = shape_parent.fuse(shape_child).Volume
    return volume_fused <= (shape_parent.Volume + delta)
  
# рекурсивное удаление дырок (у родителей вычитаются внутренности) 
def f_cut_inners_for_obj(SHAPES):
    # двойной цикл: ищи пару потомок-родитель
    for i_inner in range(len(SHAPES)):
        for i_outer in range(len(SHAPES)):
            # проверь, что внутренность внутри родителя - есть дырка
            if (i_inner != i_outer) and f_is_shape_parent(SHAPES[i_outer], SHAPES[i_inner]):
                # выччти из родителя дырку
                SHAPES[i_outer] = SHAPES[i_outer].cut(SHAPES[i_inner]).copy()
                # удали объект потомка (дырка исчезла)
                SHAPES[i_inner] = None
                # рекурсивный вызов с новыми флагами (массив флагов изменяется, он передаётся по ссылке)
                return f_cut_inners_for_obj(SHAPES)
    return f_shape_multi_fuse(SHAPES)
                    
def f_arr_shapes_and_colors(file_name, doc):
    full_filename =  os.path.join(f_current_folder(),  file_name)
    my_parse = f_pre_post_arr_pathes(f_read_file(full_filename))
    
    arr_fused_shapes = []
    for i, i_file in enumerate(my_parse["svg_files"]):
         i_arr_shapes = f_svg_to_shapes_without_colors(i_file, doc)
         i_shape = f_cut_inners_for_obj(i_arr_shapes)
         arr_fused_shapes.append(i_shape)
    
    arr_unique = sorted(set(my_parse["svg_colors"]))
    arr_combines = [[] for _ in list(range(len(arr_unique)))]
    for i, i_shape in enumerate(arr_fused_shapes):
        i_index = arr_unique.index(my_parse["svg_colors"][i])
        arr_combines[i_index].append(i_shape.copy())
        
    arr_fused_combines = [f_shape_multi_fuse(i_arr_shapes).removeSplitter() for i_arr_shapes in arr_combines]
    
    return {"arr_fused_shapes": arr_fused_combines, "arr_colors": arr_unique}
  

 
