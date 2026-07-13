# Чертит визитку с SVG логотипом, QR кодом и текстом 
import sys
sys.path.append('/usr/local/lib/python3.8/dist-packages')
import qrcode, os, FreeCAD, FreeCADGui, Draft, importSVG,  ImportGui
from FreeCAD import Console, Vector, Matrix, Base
from Part import Wire, LineSegment, Arc, Face, show
from Draft import  make_shapestring

# верни или создай активный документ
doc = FreeCAD.ActiveDocument
if doc is None:
    doc = FreeCAD.newDocument()
   
    # имя файла - откда брать SVG
CONST_FILE_NAME_INPUT = "logo_main.svg"
# имя файла - как надо сохранить
CONST_FILE_NAME_OUTPUT = "CANAPE_CLUB_telegram_no_phone_v2.step"
# путь к шрифту
CONST_FONT_PATH =  "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf"
# информация
CONST_TEXT_STRING = "@VladimirSamonin" 
CONST_URL_FOR_QR_CODE = "https://t.me/VladimirSamonin"

CONST_SVG_RATIO = 0.85
CONST_TEXT_H = 12
CONST_QR_SIDE = 35

# КРИВИЗНА скругление для 90 градусов для дуги - как расстояние от середины дуги длины 2 до середины дуги
CONST_BULGE_90 = (2 ** 0.5) - 1
# размеры визитной карты: длина, ширина, высота
CONST_CARD_XYZ = [90, 50, 0.4]
X50, Y50, Z50 = [CONST_CARD_XYZ[0] * 0.5, CONST_CARD_XYZ[1] * 0.5, CONST_CARD_XYZ[2] * 0.5]

# скругление угла визитной карточки
CONST_CARD_RADIUS = 3

# вектор - нулевой; по одной из трёх осей (три отдельные функции с одним аргументом)
F_0 = lambda: Vector(0,0,0); F_XY = lambda x,y: Vector(x,y,0)
F_X = lambda n: Vector(n,0,0); F_Y = lambda n: Vector(0,n,0); F_Z = lambda n: Vector(0,0,n)   
F_SET_LEN = lambda v, new_len: v.normalize().multiply(new_len)    
F_M = lambda VX = F_X(1), VY = F_Y(1), VZ = F_Z(1), C = F_0():  Matrix(VX.x, VX.y, VX.z, C.x,   VY.x, VY.y, VY.z, C.y,   VZ.x, VZ.y, VZ.z, C.z,   0,0,0,1)
M_44_FINAL_ROTATION = F_M(F_X(1), F_Y(-1), F_Z(-1), Vector(0,0,Z50 * 2))
 
## (MODULE ====================================================================================================
 
 # превращает массив форм в одну форму (склеивает и по умолчанию удаляет швы)
def f_shape_multi_fuse(shapes):
    if len(shapes) == 1: return shapes[0]
    return shapes[0].multiFuse(shapes[1:])    
            
# впиши, чтобы всё красиво помещалось
def f_shape_fit_isometric():
    doc.recompute(); view = FreeCADGui.activeDocument().ActiveView; view.viewIsometric(); view.fitAll()

def f_fit_shape_to_bbox_3d(shape, xmin, ymin, zmin, xmax, ymax, zmax):
    # Получаем старый ограничивающий контейнер
    old_bbox = shape.BoundBox
    
    # Создаём новый контейнер
    new_bbox = Base.BoundBox(xmin, ymin, zmin, xmax, ymax, zmax)
    
    # Вычисляем коэффициенты масштабирования
    scale_x = (new_bbox.XMax - new_bbox.XMin) / (old_bbox.XMax - old_bbox.XMin)
    scale_y = (new_bbox.YMax - new_bbox.YMin) / (old_bbox.YMax - old_bbox.YMin)
    scale_z = (new_bbox.ZMax - new_bbox.ZMin) / (old_bbox.ZMax - old_bbox.ZMin)
    
    #Console.PrintMessage([new_bbox.YMax, new_bbox.YMin, old_bbox.YMax, old_bbox.YMin])
    
    # Вычисляем центры контейнеров
    old_center = old_bbox.Center
    new_center = new_bbox.Center
    
    # Создаём матрицу преобразования
    transform = App.Matrix()
    transform.move(-old_center)              # Переносим в начало координат
    transform.scale(scale_x, scale_y, scale_z)  # Масштабируем
    transform.move(new_center)               # Переносим в новый центр
    
    # Применяем преобразование и возвращаем результат
    return shape.transformGeometry(transform)
    
## MODULE) (SVG ====================================================================================================
    
def f_svg_to_shapes(height=42, file_name = CONST_FILE_NAME_INPUT):
    # Импортирует SVG и возвращает список экструдированных Part.Shape.
    # Каждый замкнутый контур SVG превращается в отдельную форму.
    # Никакие отверстия не обрабатываются и не объединяются.
    full_path = os.path.dirname(os.path.abspath(__file__)) + "/" + file_name
    importSVG.insert(full_path, doc.Name)
    imported = doc.Objects
    shapes = []
    # генерируй фсе формы
    for obj in imported:
        if not hasattr(obj, "Shape"):
            continue
        for wire in obj.Shape.Wires:
            if not wire.isClosed(): # проволока не замкнута - ничнего не делай
                continue
            try:# только для граней
                face = Part.Face(wire)
                shapes.append(face.extrude(FreeCAD.Vector(0, 0, height)).copy())
            except Exception:
                pass
    # Удаляем все объекты Path
    for obj in list(doc.Objects):
        if obj.Name.startswith("Path"):
            doc.removeObject(obj.Name)          
    return shapes

def f_bbox_inner_outer_xy(i, o):
    # Проверка, что inner_bb находится внутри outer_bb по двум осям: x,y
    return (i.XMin >= o.XMin) and (i.YMin >= o.YMin) and  (i.XMax <= o.XMax) and (i.YMax <= o.YMax)

# рекурсивное удаление дырок (у родителей вычитаются внутренности) 
def f_cut_inners_for_obj(LEN, arr_flags_are_objects):
    # двойной цикл: ищи пару потомок-родитель
    for i_inner in range(LEN):
        for i_outer in range(LEN):
            # числа разные и при этом есть оба объекта (они не удалены как потомки)
            if (i_inner != i_outer) and arr_flags_are_objects[i_inner] and arr_flags_are_objects[i_outer]:
                obj_inner = doc.getObject(f'svg_shape_{i_inner:03d}')
                obj_outer = doc.getObject(f'svg_shape_{i_outer:03d}')
                # проверь, что внутренность внутри родителя - есть дырка
                if f_bbox_inner_outer_xy(obj_inner.Shape.BoundBox, obj_outer.Shape.BoundBox):
                    # ставь флаг, что элемент удалён
                    arr_flags_are_objects[i_inner] = False
                    # выччти из родителя дырку
                    obj_outer.Shape = obj_outer.Shape.copy().cut(obj_inner.Shape.copy())
                    # удали объект потомка (дырка исчезла)
                    doc.removeObject(f'svg_shape_{i_inner:03d}')
                    # рекурсивный вызов с новыми флагами (массив флагов изменяется, он передаётся по ссылке)
                    f_cut_inners_for_obj(LEN, arr_flags_are_objects)
                    return

# создаёт временные объекты  svg_shape_{i:03d}, вырезает дырки. Всё объединяет и удаляет все временные объекты.     
def f_cut_holes_and_multi_fuse(shape_array):
    arr_obj = []
    # создаёт временные объекты
    for i,i_shape in enumerate(shape_array):
        arr_obj.append(doc.addObject("Part::Feature", f'svg_shape_{i:03d}'))
        arr_obj[i].Shape = i_shape
    LEN = len(shape_array) 
    arr_flags_are_objects = [True] * LEN
    # вырезает дырки
    f_cut_inners_for_obj(LEN, arr_flags_are_objects)
    
    # индексы родителей (дырки - как потомки удалены и объектов с такими индексами нет)
    arr_indexes = [i for i, value in enumerate(arr_flags_are_objects) if value]
    # формы радителей
    arr_shapes = [doc.getObject(f'svg_shape_{i:03d}').Shape for i in arr_indexes]
    # результат - объединение всех родителей
    shape_multi_fuse = f_shape_multi_fuse(arr_shapes).copy()
    # удаление временных форм для отдельных родителей (которые были перед объединение)
    for i in arr_indexes: doc.removeObject(f'svg_shape_{i:03d}')
        
    return shape_multi_fuse # верни объединённную форму
    
## SVG) (RECT ====================================================================================================

# считай точку на середине изгиба дуги (известна нормаль плоскости, для прямой линии bulge = 0,  180 по ч.с. -1, 180 против ч.с. +1)
def F_BULGE_POINT(va, vb, bulge = CONST_BULGE_90, v_normal_to_plane = F_Z(1)):
    new_length = (vb-va).Length * bulge * 0.5 # длина от середины отрезка (хорды) до середины дуги
    new_cross_vector_from_mid_to_result = F_SET_LEN((vb-va).cross(v_normal_to_plane), new_length)
    return (vb + va) * 0.5 + new_cross_vector_from_mid_to_result

# отрезок (или дуга окружности по параметру "изгиб") (считает среднюю точку с изгибом и проводит дугу через неё)
def f_parse_AB_BULGE(va, vb, bulge, v_normal_to_plane = F_Z(1)):
    # начало и конец совпадают, ничего не делай
    if ((va - vb).Length == 0): return None
    # нулевая кривизна - это отрезок
    if (bulge == 0): return LineSegment(va, vb)
    # считай среднюю точку
    v_mid = F_BULGE_POINT(va, vb, bulge, v_normal_to_plane)
    # верни дугу
    return Arc(va, v_mid, vb)

# массив из отрезков и дуг -> преврати в проволоку
def f_convert_my_arr_el_to_wire(my_arr_el):
    arr_el_as_shapes_before_filtered = [item for item in my_arr_el if item is not None]
    arr_el_as_shapes_filtered = [i_obj.toShape() for i_obj in arr_el_as_shapes_before_filtered]
    return Wire(arr_el_as_shapes_filtered)
    
# массив из отрезков и дуг -> преврати в shape (форму призму)
def f_shape_prism_by_arr_el(my_arr_el, v_normal_to_plane):
    return Face(f_convert_my_arr_el_to_wire(my_arr_el)).extrude(v_normal_to_plane)

# скруглённый прямоугольник - для самОй визитки 
def f_shape_round_rect(xyz = CONST_CARD_XYZ, radius = CONST_CARD_RADIUS):
    # вектора на половины размеров
    vx_50 = F_X(xyz[0] * +0.5); vy_50 = F_Y(xyz[1] * +0.5)
    # четырё угловые точки (углы прямоугольника)
    p4 = [vx_50 * sign_x + vy_50 * sign_y for sign_x,sign_y in [[+1,+1],[-1,+1],[-1,-1],[+1,-1]]]
    # 8 изменений для 4 вершин (итого будет 8 точек)
    i0123_sign_x_sign_y = [[0, 0, -1], [0, -1, 0], [1, +1, 0], [1, 0, -1], [2, 0, +1], [2, +1, 0], [3, -1, 0], [3, 0, +1]]
    # узлы скруглённого прямоугольника
    p8 = [F_XY(radius * sign_x, radius * sign_y) + p4[i] for i,sign_x,sign_y in i0123_sign_x_sign_y]
    # 8 элементов (отрезков и дуг)
    p8_el = [f_parse_AB_BULGE(p8[i], p8[(i+1) % 8], CONST_BULGE_90 if ((i % 2) == 0) else 0) for i in [0,1,2,3,4,5,6,7]]
    return f_shape_prism_by_arr_el(p8_el, F_Z(xyz[2]))

# прямоугольник (для одиночной квадратной ячейки QR - кода)
def f_shape_rect_by_sizes_and_translate(sizes_xyz, translate_xyz):
    return Part.makeBox(sizes_xyz.x, sizes_xyz.y, sizes_xyz.z).translated(translate_xyz)
  
## RECT) (QR ====================================================================================================

# генерация QR-кода с помощьб юиблиотеки qrcode 
def f_qr_code(v_min, v_max, url = CONST_URL_FOR_QR_CODE):
    # непосредственно генерация QR кода (без границ)
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
    # добавь ссылку на наш сайт
    qr.add_data(url)
    # это самая компактная версия QR-кода (делает матрицу наименьшей из возможных)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    # пишет нули и единицы вместо булевых значений
    bit_matrix = [[1 if cell else 0 for cell in row] for row in matrix]
    
    # Вывод битовой матрицы построчно в консоль FreeCAD
    for row in bit_matrix: Console.PrintMessage("".join(map(str, row)) + "\n")
    
    # bit_matrix = [[1]]
    
    # размер по оси х матрицы и по оси у (столбцов и строк - они совпадают)
    nx = len(bit_matrix[0])
    ny = len(bit_matrix) 
    sizes_xyz = Vector((v_max.x - v_min.x) / nx, (v_max.y - v_min.y) / ny, v_max.z - v_min.z)
    p00 = Vector(v_min.x, v_max.y, v_min.z)
    
    # на сколько сдвигать нулевой-нулевой квадратик
    # !! нулевую строку y смещай на -1, потому что размеры от ближнего угла, а не от дальнего
    f_translate_ix_iy = lambda ix,iy: p00 + F_XY(sizes_xyz.x * ix, sizes_xyz.y * (-(iy+1)))
    # фигура - клеточка
    f_shape_ix_iy = lambda ix,iy: f_shape_rect_by_sizes_and_translate(sizes_xyz, f_translate_ix_iy(ix, iy))
    
    arr_shapes = []
    for ix in range(nx):
        for iy in range(ny):
            if bit_matrix[iy][ix]:
                arr_shapes.append(f_shape_ix_iy(ix, iy))
    return f_shape_multi_fuse(arr_shapes)

## QR) (TEXT====================================================================================================

# одна строка текста
def f_shape_string(text_str = CONST_TEXT_STRING, extrude_mm = 10, font_size = 10):
    # строка с нужным шрифтом и размером шрифта
    shapestring = make_shapestring(String=text_str, FontFile=CONST_FONT_PATH, Size=font_size)
    # выдави текст вверх
    shape_result = shapestring.Shape.extrude(F_Z(extrude_mm))
    # удали двумерную подложку
    doc.removeObject(shapestring.Name)
    return shape_result
    
## TEXT) (CALCULATE ====================================================================================================

def f_calculate_bb(svg_qr_text_012, ratio = CONST_SVG_RATIO, qr = CONST_QR_SIDE, text_h = CONST_TEXT_H):
    svg_w = qr * ratio
    svg_h = qr
    gap_x = (X50*2 - qr - svg_w) / 3.0
    gap_y = (Y50*2 - qr - text_h) / 3.0
            	
    x,y,z = [-X50 + gap_x, -Y50 + gap_y, Z50]
    X,Y,Z = [X50 - gap_x, +Y50 - gap_y, Z50 * 2]
            	
    if svg_qr_text_012 == 0: return [x,Y - qr,z, x + svg_w,Y,Z]
    if svg_qr_text_012 == 1: return [X-qr,Y-qr,z, X,Y,Z]
    # ширина текста - по отступам слева и справа - как у оси Y
    if svg_qr_text_012 == 2: return [-X50+gap_y,y,z, X50-gap_y,(-Y50) + gap_y + text_h,Z]
            	
## CALCULATE) ====================================================================================================

def f_final_combine():
    svg_pre = f_cut_holes_and_multi_fuse(f_svg_to_shapes())
    svg_post = f_fit_shape_to_bbox_3d(svg_pre, *f_calculate_bb(0))

    T = f_calculate_bb(1)
    qr_code_post = f_qr_code(Vector(T[0],T[1],T[2]), Vector(T[3],T[4],T[5]),)
    text_post = f_fit_shape_to_bbox_3d(f_shape_string(), *f_calculate_bb(2))
    
    #M_44_FINAL_ROTATION = F_M()
    
    # форма a - текст и QR-код
    my_shape_a = text_post.fuse(qr_code_post).fuse(svg_post).removeSplitter()
    my_obj_a = doc.addObject("Part::Feature", "shape_a")
    my_obj_a.Shape = my_shape_a.transformGeometry(M_44_FINAL_ROTATION)
    
    # форма b - пластина визитки за вычитом: текста и QR-кода
    my_shape_b = f_shape_round_rect().cut(my_shape_a).removeSplitter()
    my_obj_b = doc.addObject("Part::Feature", "shape_b")
    my_obj_b.Shape = my_shape_b.transformGeometry(M_44_FINAL_ROTATION)
        
    # Цвета
    my_obj_a.ViewObject.ShapeColor = (0.0, 0.0, 0.0)   # текст
    my_obj_b.ViewObject.ShapeColor = (1.0, 1.0, 0.0)   # фон
    
    # расположи всё, чтобы было видно
    f_shape_fit_isometric()
    
    # Экспорт
    my_folder_current_macro = os.path.dirname(os.path.abspath(__file__))
    my_filename = my_folder_current_macro + "/" + CONST_FILE_NAME_OUTPUT
    ImportGui.export([my_obj_a, my_obj_b], my_filename)
    Console.PrintMessage("Экспортировано:", my_filename)
    
f_final_combine()
