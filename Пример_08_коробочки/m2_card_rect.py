from m1_card_start import f_shape_multi_fuse, f_shape_fit_isometric, F_M_44_FINAL_ROTATION
import FreeCAD, Part

from m1_card_start import F_SET_LEN, F_X,F_Y,F_Z, F_XY, F_0

# КРИВИЗНА скругление для 90 градусов для дуги - как расстояние от середины дуги длины 2 до середины дуги
CONST_BULGE_90 = (2 ** 0.5) - 1

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
    if (bulge == 0): return Part.LineSegment(va, vb)
    # считай среднюю точку
    v_mid = F_BULGE_POINT(va, vb, bulge, v_normal_to_plane)
    # верни дугу
    return Part.Arc(va, v_mid, vb)

# массив из отрезков и дуг -> преврати в проволоку
def f_convert_my_arr_el_to_wire(my_arr_el):
    arr_el_as_shapes_before_filtered = [item for item in my_arr_el if item is not None]
    arr_el_as_shapes_filtered = [i_obj.toShape() for i_obj in arr_el_as_shapes_before_filtered]
    return Part.Wire(arr_el_as_shapes_filtered)
    
# массив из отрезков и дуг -> преврати в shape (форму призму)
def f_shape_prism_by_arr_el(my_arr_el, v_normal_to_plane):
    return Part.Face(f_convert_my_arr_el_to_wire(my_arr_el)).extrude(v_normal_to_plane)

# скруглённый прямоугольник - для самОй визитки 
def f_shape_round_rect(xyz, radius):
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
  
'''
# верни или создай активный документ
doc = FreeCAD.ActiveDocument
if doc is None:
    doc = FreeCAD.newDocument()
my_obj_a = doc.addObject("Part::Feature", "shape_test")
my_shape_pre = f_shape_rect_by_sizes_and_translate(FreeCAD.Vector(10,10,10), F_0())
my_obj_a.Shape = f_shape_round_rect([10,20,3], 2)
f_shape_fit_isometric(doc)
'''
    