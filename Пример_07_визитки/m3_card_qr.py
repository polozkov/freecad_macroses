from m1_card_start import f_shape_multi_fuse, f_shape_fit_isometric, F_M_44_FINAL_ROTATION
from m2_card_rect import f_shape_rect_by_sizes_and_translate

# Чертит визитку с SVG логотипом, QR кодом и текстом 
import sys
sys.path.append('/usr/local/lib/python3.8/dist-packages')
import qrcode, FreeCAD
    
# генерация QR-кода с помощьб юиблиотеки qrcode 
def f_qr_code(v_min, v_max, url):
    # непосредственно генерация QR кода (без границ)
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=0)
    # добавь ссылку на наш сайт
    qr.add_data(url)
    # это самая компактная версия QR-кода (делает матрицу наименьшей из возможных)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    # пишет нули и единицы вместо булевых значений
    bit_matrix = [[1 if cell else 0 for cell in row] for row in matrix]
    
    # bit_matrix = [[1]]
    
    # размер по оси х матрицы и по оси у (столбцов и строк - они совпадают)
    nx = len(bit_matrix[0])
    ny = len(bit_matrix) 
    sizes_xyz = FreeCAD.Vector((v_max.x - v_min.x) / nx, (v_max.y - v_min.y) / ny, v_max.z - v_min.z)
    p00 = FreeCAD.Vector(v_min.x, v_max.y, v_min.z)
    
    # на сколько сдвигать нулевой-нулевой квадратик
    # !! нулевую строку y смещай на -1, потому что размеры от ближнего угла, а не от дальнего
    f_translate_ix_iy = lambda ix,iy: p00 + FreeCAD.Vector(sizes_xyz.x * ix, sizes_xyz.y * (-(iy+1)), 0)
    # фигура - клеточка
    f_shape_ix_iy = lambda ix,iy: f_shape_rect_by_sizes_and_translate(sizes_xyz, f_translate_ix_iy(ix, iy))
    
    arr_shapes = []
    for ix in range(nx):
        for iy in range(ny):
            if bit_matrix[iy][ix]:
                arr_shapes.append(f_shape_ix_iy(ix, iy))
    return f_shape_multi_fuse(arr_shapes)

'''
# верни или создай активный документ
doc = FreeCAD.ActiveDocument
if doc is None:
    doc = FreeCAD.newDocument()
my_obj_a = doc.addObject("Part::Feature", "shape_test")
my_shape_pre = f_qr_code(FreeCAD.Vector(-20,-20,0), FreeCAD.Vector(20,20,10), "https://t.me/VladimirSamonin")
my_obj_a.Shape = my_shape_pre.transformGeometry(F_M_44_FINAL_ROTATION(5))
f_shape_fit_isometric(doc)
'''
    