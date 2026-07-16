import FreeCAD, FreeCADGui

# вектор - нулевой; по одной из трёх осей (три отдельные функции с одним аргументом)
F_0 = lambda: FreeCAD.Vector(0,0,0); F_XY = lambda x,y: FreeCAD.Vector(x,y,0)
F_X = lambda n: FreeCAD.Vector(n,0,0); F_Y = lambda n: FreeCAD.Vector(0,n,0); F_Z = lambda n: FreeCAD.Vector(0,0,n)   
F_SET_LEN = lambda v, new_len: v.normalize().multiply(new_len)    
F_M = lambda VX = F_X(1), VY = F_Y(1), VZ = F_Z(1), C = F_0():  FreeCAD.Matrix(VX.x, VX.y, VX.z, C.x,   VY.x, VY.y, VY.z, C.y,   VZ.x, VZ.y, VZ.z, C.z,   0,0,0,1)
F_M_44_FINAL_ROTATION = lambda Z50 = 0.2: F_M(F_X(1), F_Y(-1), F_Z(-1), FreeCAD.Vector(0,0,Z50 * 2))

def f_print(string_info):
    FreeCAD.Console.PrintMessage(string_info)
    
def f_add_obj(my_name, my_shape, my_color, doc, my_m44_transform = F_M()):
    temp_obj = doc.addObject("Part::Feature", my_name)
    temp_obj.Shape = my_shape.transformGeometry(my_m44_transform)
    r,g,b =  my_color // 256**2,(my_color // 256) % 256, my_color % 256
    temp_obj.ViewObject.ShapeColor = (r / 256.0, g / 256.0, b / 256.0)
    
# превращает массив форм в одну форму
def f_shape_multi_fuse(shapes_with_nones):
    if isinstance(shapes_with_nones, list):
        shapes = [i_shape for i_shape in shapes_with_nones if i_shape]
        if (len(shapes) == 1): return shapes[0]
        if (len(shapes) == 2): return shapes[0].fuse(shapes[1])
        if (len(shapes) > 2): return shapes[0].multiFuse(shapes[1:])
    FreeCAD.Console.PrintMessage(f' __ERROR__{shapes_with_nones}__')
    return shapes_with_nones
    
# впиши, чтобы всё красиво помещалось
def f_shape_fit_isometric(doc):
    doc.recompute(); view = FreeCADGui.activeDocument().ActiveView; view.viewIsometric(); view.fitAll()

def f_fit_shape_to_bbox_3d(shape, xmin, ymin, zmin, xmax, ymax, zmax, fused_shape_was = None):
    # Получаем старый ограничивающий контейнер
    old_bbox = shape.copy().BoundBox
    if not (fused_shape_was is None):
        old_bbox = fused_shape_was.BoundBox
    
    # Создаём новый контейнер
    new_bbox = FreeCAD.Base.BoundBox(xmin, ymin, zmin, xmax, ymax, zmax)
    
    # Вычисляем коэффициенты масштабирования
    scale_x = (new_bbox.XMax - new_bbox.XMin) / (old_bbox.XMax - old_bbox.XMin)
    scale_y = (new_bbox.YMax - new_bbox.YMin) / (old_bbox.YMax - old_bbox.YMin)
    scale_z = (new_bbox.ZMax - new_bbox.ZMin) / (old_bbox.ZMax - old_bbox.ZMin)
    
    #Console.PrintMessage([new_bbox.YMax, new_bbox.YMin, old_bbox.YMax, old_bbox.YMin])
    
    # Вычисляем центры контейнеров
    old_center = old_bbox.Center
    new_center = new_bbox.Center
    
    # Создаём матрицу преобразования
    transform = FreeCAD.Matrix()
    transform.move(-old_center)              # Переносим в начало координат
    transform.scale(scale_x, scale_y, scale_z)  # Масштабируем
    transform.move(new_center)               # Переносим в новый центр
    
    # Применяем преобразование и возвращаем результат
    return shape.transformGeometry(transform)