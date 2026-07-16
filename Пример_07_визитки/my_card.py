import FreeCAD, os, Draft, ImportGui

import m1_card_start, m2_card_rect, m3_card_qr, m4_card_svg
import importlib
importlib.reload(m1_card_start)
importlib.reload(m2_card_rect)
importlib.reload(m3_card_qr)
importlib.reload(m4_card_svg)
   
# имя файла - откда брать SVG
CONST_FILE_NAME_INPUT = "logo_main.svg"
# имя файла - как надо сохранить
CONST_FILE_NAME_OUTPUT = "CANAPE_MULTI_COLOR_V2.step"
# путь к шрифту
CONST_FONT_PATH =  "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf"
# информация
CONST_TEXT_STRING = "@VLADIMIRSAMONIN" 
CONST_URL_FOR_QR_CODE = "https://t.me/VladimirSamonin"

CONST_SVG_RATIO = 51.0 / 60.0
CONST_TEXT_H = 12
CONST_QR_SIDE = 35

# размеры визитной карты: длина, ширина, высота
CONST_CARD_XYZ = [90, 50, 0.4]
X50, Y50, Z50 = [CONST_CARD_XYZ[0] * 0.5, CONST_CARD_XYZ[1] * 0.5, CONST_CARD_XYZ[2] * 0.5]

# скругление угла визитной карточки
CONST_CARD_RADIUS = 3

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

def f_shape_string(text_str = CONST_TEXT_STRING, extrude_mm = 10, font_size = 10):
    # строка с нужным шрифтом и размером шрифта
    shapestring = Draft.make_shapestring(String=text_str, FontFile=CONST_FONT_PATH, Size=font_size)
    # выдави текст вверх
    shape_result = shapestring.Shape.extrude(m1_card_start.F_Z(extrude_mm))
    # удали двумерную подложку
    doc.removeObject(shapestring.Name)
    return shape_result 

doc = FreeCAD.ActiveDocument
if doc is None: doc = FreeCAD.newDocument() 

def f_final_combine():
    def f_i_name(i): return f'my_svg_{i}'
    M44 = m1_card_start.F_M_44_FINAL_ROTATION(Z50)
    
    my_info = m4_card_svg.f_arr_shapes_and_colors(CONST_FILE_NAME_INPUT, doc)
    union_svg_shape = m1_card_start.f_shape_multi_fuse(my_info["arr_fused_shapes"])
    LEN = len(my_info["arr_fused_shapes"])
    arr_svg_el = [m1_card_start.f_fit_shape_to_bbox_3d(i, *f_calculate_bb(0), union_svg_shape) for i in my_info["arr_fused_shapes"]]
    for i in range(LEN):
        m1_card_start.f_add_obj(f_i_name(i), arr_svg_el[i], my_info["arr_colors"][i], doc, M44)
    
    T = f_calculate_bb(1)
    shape_qr_code_in_bb = m3_card_qr.f_qr_code(FreeCAD.Vector(T[0],T[1],T[2]), FreeCAD.Vector(T[3],T[4],T[5]), CONST_URL_FOR_QR_CODE)
    shape_text_in_bb = m1_card_start.f_fit_shape_to_bbox_3d(f_shape_string(), *f_calculate_bb(2))
    
    CONST_NAME_QR = "my_qr_code_in_bb"
    CONST_NAME_TEXT = "my_text_in_bb"
    CONST_NAME_ROUND_RECT = "my_round_rect"
    
    shape_round_rect_start = m2_card_rect.f_shape_round_rect(CONST_CARD_XYZ, CONST_CARD_RADIUS)
    shape_array_for_cut = [shape_qr_code_in_bb, shape_text_in_bb, *arr_svg_el]
    shape_round_rect = shape_round_rect_start.cut(m1_card_start.f_shape_multi_fuse(shape_array_for_cut))
    
    m1_card_start.f_add_obj(CONST_NAME_QR, shape_qr_code_in_bb, 0, doc, M44)
    m1_card_start.f_add_obj(CONST_NAME_TEXT, shape_text_in_bb, 0, doc, M44)
    m1_card_start.f_add_obj(CONST_NAME_ROUND_RECT, shape_round_rect, 256**3-1, doc, M44)
    
    m1_card_start.f_shape_fit_isometric(doc)
    
    #return
    # Экспорт
    my_filename = os.path.join(m4_card_svg.f_current_folder(), CONST_FILE_NAME_OUTPUT)
    arr_obj_for_svg = [doc.getObject(f_i_name(i))  for i in list(range(LEN))]
    arr_all_obj = [doc.getObject(CONST_NAME_ROUND_RECT), doc.getObject(CONST_NAME_QR), doc.getObject(CONST_NAME_TEXT), *arr_obj_for_svg]
    ImportGui.export(arr_all_obj, my_filename)
    m1_card_start.f_print(f'Экспортировано: {my_filename}')
    
f_final_combine()
    