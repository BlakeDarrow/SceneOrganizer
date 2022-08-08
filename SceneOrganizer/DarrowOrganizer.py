# ##### BEGIN GPL LICENSE BLOCK #####
#
#   Copyright (C) 2022  Blake Darrow <contact@blakedarrow.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

#-----------------------------------------------------#  
#   Imports
#-----------------------------------------------------# 
import bpy
import bmesh
from bpy.props import BoolProperty

def updateBooleanVisibility(self, context):
    DarrowToggleCutters.execute(self,context)
 
def updateArmsVisibility(self, context):
    DarrowToggleArms.execute(self,context)
 
def updateCurveVisibility(self, context):
    DarrowToggleCurves.execute(self,context)

def updateEmptiesVisibility(self, context):
    DarrowToggleEmpty.execute(self,context)

def updateRandomVisibility(self, context):
    bpy.context.space_data.shading.color_type = 'RANDOM'
    
def updateMaterialVisibility(self, context):
    bpy.context.space_data.shading.color_type = 'MATERIAL'

def updateWireframeVisibility(self, context):
    DarrowWireframe.execute(self,context)

def toggle_expand(context, state):
    area = next(a for a in context.screen.areas if a.type == 'OUTLINER')
    bpy.ops.outliner.show_hierarchy({'area': area}, 'INVOKE_DEFAULT')
    for i in range(state):
        bpy.ops.outliner.expanded_toggle({'area': area})
    area.tag_redraw()

def traverse_tree(t):
    yield t
    for child in t.children:
        yield from traverse_tree(child)

def store_coll_state(collection, case=False):
    coll = bpy.context.scene.collection
    colls = []
    states = []
    
    for c in traverse_tree(coll):
        if c.name in bpy.context.view_layer.layer_collection.children:
            state = bpy.context.view_layer.layer_collection.children[c.name].hide_viewport 

            if c.name not in colls:
                colls.append(c.name)
                states.append(state)

    sort_collection(bpy.context.scene.collection, False)

    for x in range(0,len(colls)):
        bpy.context.view_layer.layer_collection.children[colls[x]].hide_viewport = states[x]

def sort_collection(collection, case=False):

  if collection.children is None:
      return

  children = sorted(
      collection.children,
      key=lambda c: c.name if case else c.name.lower()
  )

  for child in children:
    collection.children.unlink(child)
    collection.children.link(child)
    sort_collection(child)

def strip(obj): 
    name = obj.name
    name = name + "temp"
    replaceList = (".","__","0","_high", "_low")

    head, sep, tail = name.partition("_low")
    if not tail:
        head, sep, tail = name.partition("_high")

    for word in replaceList:
        name = head.replace(word, "")
        
    name = name.replace("temp","")
    obj.name = name
    return obj.name

def add_suffix(obj, suffix):
    strip(obj)

    name = obj.name + "tmp"
    name = name + suffix
    name = name.replace("tmp", "")

    obj.name = name
    return obj.name

def collapse_pop_up(self, context):
    layout = self.layout
    box = layout.box()
    row = box.row(align=False)
    if bpy.context.scene.iconOnly_Bool == False:
        text_1 = "Collapse"
        text_2 = "Sort"
    else:
        text_1 = ""
        text_2 = ""

    row.operator('collapse.scene', icon='SORT_ASC', text = text_1,emboss = False)
    box = layout.box()
    row = box.row(align=False)
    row.operator('darrow.sort_outliner', icon='SORTALPHA', text = text_2,emboss = False)

def bmesh_copy_from_object(obj, transform=True, triangulate=True, apply_modifiers=False):
    """Returns a transformed, triangulated copy of the mesh"""
    assert obj.type == 'MESH'

    if apply_modifiers and obj.modifiers:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        me = obj_eval.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        obj_eval.to_mesh_clear()
    else:
        me = obj.data
        if obj.mode == 'EDIT':
            bm_orig = bmesh.from_edit_mesh(me)
            bm = bm_orig.copy()
        else:
            bm = bmesh.new()
            bm.from_mesh(me)

    if transform:
        bm.transform(obj.matrix_world)

    if triangulate:
        bmesh.ops.triangulate(bm, faces=bm.faces)

    return bm

def hasVolume(obj):
    bm = bmesh_copy_from_object(obj, apply_modifiers=True)
    volume = bm.calc_volume()
    bm.free()

    if volume > 0.0:
       return True
    else: 
        return False

def curve_to_mesh(context, curve):
    deg = context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(curve.evaluated_get(deg), depsgraph=deg)
    new_obj = bpy.data.objects.new(curve.name + "_tempMesh", me)
    context.collection.objects.link(new_obj)
    new_obj.matrix_world = curve.matrix_world

    if hasVolume(new_obj):
        bool = False
    else:
        bool =  True

    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[new_obj.name].select_set(True)
    bpy.ops.object.delete() 

    return bool

class OrganizerSettings(bpy.types.PropertyGroup):
    armsVis : BoolProperty(
        name = "Armature Visibility",
        update = updateArmsVisibility,
        default=False,
    )
    curveVis : BoolProperty(
        name = "Curve Visibility",
        update = updateCurveVisibility,
        default=False,
    )
    booleanVis : BoolProperty(
        name = "Cutter Visibility",
        update = updateBooleanVisibility,
        default=False,
    )
    emptiesVis : BoolProperty(
        name = "Empty Visibility",
        update = updateEmptiesVisibility,
        default=False,
    )
    randomVis : BoolProperty(
        name = "Random Visibility",
        update = updateRandomVisibility,
    )
    materialVis : BoolProperty(
        name = "Material Visibility",
        update = updateMaterialVisibility,
        default=False,
    )
    wireframeVis : BoolProperty(
        name = "Wireframe Visibility",
        update = updateWireframeVisibility,
        default=False,
    )

class DarrowOrganizePanel():
    bl_category = "DarrowTools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

class DARROW_PT_organizePanel(DarrowOrganizePanel, bpy.types.Panel):
    bl_label = "Scene Organizer"
    bl_category = "DarrowTools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_idname = "DARROW_PT_organizePanel"
    
    def draw_header(self, context):
        self.layout.prop(context.scene, 'showSceneAdvancedOptionsBool',
                         icon="MOD_HUE_SATURATION", text="")

    def draw(self, context):
        scn = bpy.context.scene
        layout = self.layout
        col = layout.column(align=True)
        col.scale_y = 1
        col.label(text="Hide and sort by type")
        col_1 = layout.box().column()
        col_1.scale_y = 1.33
        col_1 = col_1.split(factor=0.5, align=True)

        split = col_1.split(factor=0.3, align=True)
        panel = split.column(align=True)
        icon = split.column(align=True)

        col_2 = col_1.split(factor=1, align=True)
        split_2 = col_2.split(factor=0.7, align=True)
        icon_2 = split_2.column(align=True)
        panel_2 = split_2.column(align=True)
        
        col = layout.box().row().split(align=True)
        col.scale_y = 1.1

        icon.operator('set.cutter_coll',text="Cutters", )
        panel.prop(scn.my_settings, 'booleanVis',text = "", toggle=True, icon="MOD_BOOLEAN")

        icon_2.operator('set.curve_coll', text = "Curves", )
        panel_2.prop(scn.my_settings, 'curveVis', text="", toggle=True, icon='MOD_CURVE')

        icon.operator('set.empty_coll', text="Empties", )
        panel.prop(scn.my_settings, 'emptiesVis',text = "", toggle=True, icon="EMPTY_AXIS")
        
        icon_2.operator('set.arms_coll', text="Arms", )
        panel_2.prop(scn.my_settings, 'armsVis',text = "", toggle=True, icon="ARMATURE_DATA")
     
        col.operator('collapse.scene', text="Collapse", icon="SORT_ASC")
        col.operator('darrow.sort_outliner',text="Sort", icon="SORTALPHA")

        if bpy.context.scene.showSceneAdvancedOptionsBool == True:
            col = layout.box()
            col.scale_y = 1.1
            col.prop(context.scene, "volumeCurves_Bool", text="Zero volume curves only")
            col.prop(context.scene,'iconOnly_Bool', text ="Display only icons in outliner")

class DARROW_PT_organizePanel_2(DarrowOrganizePanel, bpy.types.Panel):
    bl_parent_id = "DARROW_PT_organizePanel"
    bl_label = "Naming"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        cf = row.split(align=True)
        cf.scale_y = 1.33
        cf.operator('darrow.rename_high', text="_high",)
        cf.operator('darrow.rename_low', text="_low",)
        row = row.row(align=True)
        row.scale_y = 1.33
        row.operator('darrow.rename_clean', text="Strip", icon="TRASH")

class DARROW_PT_organizePanel_3(DarrowOrganizePanel, bpy.types.Panel):
    bl_parent_id = "DARROW_PT_organizePanel"
    bl_label = "Viewport"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene

        cf4 = layout.column_flow(columns=2, align=True)
        cf4.scale_y = 1.1
        cf4.prop(scn.my_settings, 'wireframeVis',text = "Wireframe")
        rand = cf4.column(align=True)
        rand.prop(scn.my_settings, 'randomVis', text = "Random")
        mat = cf4.column(align=True)
        mat.prop(scn.my_settings, 'materialVis',text = "Material")
        
        if scn.my_settings.randomVis == True:
                mat.enabled = False
        if scn.my_settings.materialVis == True:
                rand.enabled = False

class ORGANIZER_OT_Dummy(bpy.types.Operator):
    bl_idname = "organizer.dummy"
    bl_label = ""
    bl_description = ""
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context):
        return False

    def execute(self, context):
        return {'FINISHED'}

class DarrowSort(bpy.types.Operator):
    bl_label = "Sort Outliner"
    bl_idname = "darrow.sort_outliner"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Sort Outliner"

    def execute(self,context):
        case_sensitive = False
        for scene in bpy.data.scenes:
            store_coll_state(scene.collection, case_sensitive)
        return {'FINISHED'}

class DarrowRenameSelectedHigh(bpy.types.Operator):
    bl_label = "Rename as high"
    bl_idname = "darrow.rename_high"
    bl_description = "Rename selected as high"
    bl_options = {'UNDO'}

    def execute(self,context):
        objs = bpy.context.selected_objects
        for obj in objs:
            add_suffix(obj, "_high")
        return {'FINISHED'}

class DarrowRenameSelectedLow(bpy.types.Operator):
    bl_label = "Rename as low"
    bl_idname = "darrow.rename_low"
    bl_description = "Rename selected as low"
    bl_options = {'UNDO'}

    def execute(self,context):
        objs = bpy.context.selected_objects
        for obj in objs:
            add_suffix(obj, "_low")
        return {'FINISHED'}

class DarrowCleanName(bpy.types.Operator):
    bl_label = "Strip names"
    bl_idname = "darrow.rename_clean"
    bl_description = "Replace '.' with '_', and high/low"
    bl_options = {'UNDO'}

    def execute(self,context):
        objs = bpy.context.selected_objects
        for obj in objs:
            strip(obj)
        return {'FINISHED'}

class DarrowToggleCutters(bpy.types.Operator):
    bl_label = "Toggle Cutters"
    bl_idname = "darrow.toggle_cutters"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Toggle the visibility of cutters."

    def execute(self, context):
        bpy.context.scene.cutterVis_Bool = not bpy.context.scene.cutterVis_Bool

        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                if ob.display_type == 'BOUNDS' or ob.display_type == 'WIRE':
                    parent = ob.users_collection[0].name
                    if "_cutters" not in ob.users_collection[0].name:
                        bpy.context.view_layer.layer_collection.children[parent].hide_viewport = bpy.context.scene.cutterVis_Bool
                        bpy.context.view_layer.layer_collection.children[parent].hide_viewport = not bpy.context.view_layer.layer_collection.children[parent].hide_viewport
                    ob.hide_set(bpy.context.scene.cutterVis_Bool)
                    ob.hide_set(not bpy.context.scene.cutterVis_Bool)

        return {'FINISHED'}

class DarrowToggleCurves(bpy.types.Operator):
    bl_label = "Toggle Curves"
    bl_idname = "darrow.toggle_curves"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Toggle the visibility of curves."

    def execute(self, context):
        bpy.context.scene.curveVis_Bool = not bpy.context.scene.curveVis_Bool

        for ob in bpy.data.objects:
            if ob.type == 'CURVE':
                if bpy.context.scene.volumeCurves_Bool == True:
                    if curve_to_mesh(context, ob):
                        parent = ob.users_collection[0].name
                
                        if "_curves" not in ob.users_collection[0].name:
                            bpy.context.view_layer.layer_collection.children[parent].hide_viewport = bpy.context.scene.curveVis_Bool
                            bpy.context.view_layer.layer_collection.children[parent].hide_viewport = not bpy.context.view_layer.layer_collection.children[parent].hide_viewport

                        ob.hide_set(bpy.context.scene.curveVis_Bool)
                        ob.hide_set(not bpy.context.scene.curveVis_Bool)
                else:
                    parent = ob.users_collection[0].name
                
                    if "_curves" not in ob.users_collection[0].name:
                        bpy.context.view_layer.layer_collection.children[parent].hide_viewport = bpy.context.scene.curveVis_Bool
                        bpy.context.view_layer.layer_collection.children[parent].hide_viewport = not bpy.context.view_layer.layer_collection.children[parent].hide_viewport

                    ob.hide_set(bpy.context.scene.curveVis_Bool)
                    ob.hide_set(not bpy.context.scene.curveVis_Bool)

        return {'FINISHED'}

class DarrowToggleArms(bpy.types.Operator):
    bl_label = "Toggle Armature"
    bl_idname = "darrow.toggle_arms"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Toggle the visibility of armatures."

    def execute(self, context):
        bpy.context.scene.armsVis_Bool = not bpy.context.scene.armsVis_Bool

        for ob in bpy.data.objects:
            if ob.type == 'ARMATURE':
                parent = ob.users_collection[0].name
                
                if "_armatures" not in ob.users_collection[0].name:
                    bpy.context.view_layer.layer_collection.children[parent].hide_viewport = bpy.context.scene.armsVis_Bool
                    bpy.context.view_layer.layer_collection.children[parent].hide_viewport = not bpy.context.view_layer.layer_collection.children[parent].hide_viewport

                ob.hide_set(bpy.context.scene.armsVis_Bool)
                ob.hide_set(not bpy.context.scene.armsVis_Bool)

        return {'FINISHED'}

class DarrowToggleEmpty(bpy.types.Operator):
    bl_label = "Toggle Empty"
    bl_idname = "darrow.toggle_empty"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Toggle the visibility of empties"

    def execute(self, context):
        bpy.context.scene.emptyVis_Bool = not bpy.context.scene.emptyVis_Bool

        for ob in bpy.data.objects:
            if ob.type == 'EMPTY':
                parent = ob.users_collection[0].name
        
                if "_empties" not in ob.users_collection[0].name:
                    bpy.context.view_layer.layer_collection.children[parent].hide_viewport = bpy.context.scene.emptyVis_Bool
                    bpy.context.view_layer.layer_collection.children[parent].hide_viewport = not bpy.context.view_layer.layer_collection.children[parent].hide_viewport

                ob.hide_set(bpy.context.scene.emptyVis_Bool)
                ob.hide_set(not bpy.context.scene.emptyVis_Bool)

        return {'FINISHED'}

class DarrowCollapseOutliner(bpy.types.Operator):
    bl_label = "Collapse Outliner"
    bl_idname = "collapse.scene"
    bl_description = "Collapse all items in the outliner"

    def execute(self, context):
        toggle_expand(context, 2)
        return {'FINISHED'}
               
class DarrowWireframe(bpy.types.Operator):
    bl_idname = "set.wireframe"
    bl_description = "Display Wireframe Overlay Only"
    bl_label = "Toggle Wireframe"

    def execute(self, context):
        obj = context.active_object
        if bpy.context.scene.showWireframeBool == False:
            bpy.context.scene.showWireframeBool = True
            if obj is not None:
                bpy.context.active_object.select_set(False)
            bpy.context.space_data.show_gizmo = False
            bpy.context.space_data.overlay.show_floor = False
            bpy.context.space_data.overlay.show_axis_y = False
            bpy.context.space_data.overlay.show_axis_x = False
            bpy.context.space_data.overlay.show_cursor = False
            bpy.context.space_data.overlay.show_object_origins = False
            bpy.context.space_data.overlay.show_wireframes = True
        else:
            bpy.context.scene.showWireframeBool = False
            if obj is not None:
                bpy.context.active_object.select_set(False)
            bpy.context.space_data.show_gizmo = True
            bpy.context.space_data.overlay.show_floor = True
            bpy.context.space_data.overlay.show_axis_y = True
            bpy.context.space_data.overlay.show_axis_x = True
            bpy.context.space_data.overlay.show_cursor = True
            bpy.context.space_data.overlay.show_object_origins = True
            bpy.context.space_data.overlay.show_wireframes = False

        return {'FINISHED'} 
    
class DarrowSetCollectionCutter(bpy.types.Operator):
    bl_idname = "set.cutter_coll"
    bl_description = "Move all cutters to a collection"
    bl_label = "Group All cutters"

    def execute(self, context):
        collectionFound = False
        empty_collection_name = "_cutters"
        old_obj = bpy.context.selected_objects
        scene = bpy.context.scene.objects

        bpy.ops.object.select_all(action='DESELECT')

        for myCol in bpy.data.collections:
            if myCol.name == empty_collection_name:
                collectionFound = True
                break

        bools = []
        for obj in scene:
            for mods in obj.modifiers:
                if mods.type == 'BOOLEAN':
                    bools.append(mods.object)
        
            if obj.display_type == 'BOUNDS':
                bools.append(obj)

        if collectionFound == False and not len(bools) == 0:
            CreateCollections()
        else:
            self.report({'WARNING'}, "No boolean cutters left to sort")
        if len(bools) != 0:
            for obj in bools:
                print(obj)
                if obj is not None:
                    for coll in obj.users_collection:
                        coll.objects.unlink(obj)
                    
                    bpy.data.collections[empty_collection_name].objects.link(obj)
            self.report({'INFO'}, "Moved all booleans")
       
        bpy.ops.object.select_all(action='DESELECT')

        for x in old_obj:     
            x.select_set(state=True)

        return {'FINISHED'}

def CreateCollections():
    master_collection = bpy.data.collections.new("_SceneOrganizer")
    empty_collection = bpy.data.collections.new("_empties")
    cutters_collection = bpy.data.collections.new("_cutters")
    curves_collection = bpy.data.collections.new("_curves")
    armatures_collection = bpy.data.collections.new("_armatures")
    bpy.context.scene.collection.children.link(master_collection)
    bpy.data.collections[master_collection.name].color_tag = 'COLOR_05'
    master_collection.children.link(empty_collection)
    master_collection.children.link(cutters_collection)
    master_collection.children.link(curves_collection)
    master_collection.children.link(armatures_collection)

class DarrowSetCurveCollection(bpy.types.Operator):
    bl_idname = "set.curve_coll"
    bl_description = "Move all curves without volume to a collection"
    bl_label = "Group All Curves"

    def execute(self, context):
        collectionFound = False
        empty_collection_name = "_curves"
        old_obj = bpy.context.selected_objects
        scene = bpy.context.scene.objects
        curves = []

        bpy.ops.object.select_all(action='DESELECT')
        for myCol in bpy.data.collections:
            if myCol.name == empty_collection_name:
                collectionFound = True
                break

        for obj in scene:
            if obj.type == "CURVE":
                if bpy.context.scene.volumeCurves_Bool == True:
                    if curve_to_mesh(context, obj):
                        curves.append(obj)
                else:
                    curves.append(obj)

        if collectionFound == False and not len(curves) == 0:
            CreateCollections()
        else:
            self.report({'WARNING'}, "No curves left to sort")
        if len(curves) != 0:
            for obj in curves:
                if obj is not None:
                    for coll in obj.users_collection:
                        coll.objects.unlink(obj)
                    bpy.data.collections[empty_collection_name].objects.link(obj)
            self.report({'INFO'}, "Moved all curves")
    
        bpy.ops.object.select_all(action='DESELECT')

        for x in old_obj:     
            x.select_set(state=True)
       
        return {'FINISHED'}

class DarrowSetCollection(bpy.types.Operator):
    bl_idname = "set.empty_coll"
    bl_description = "Move all empties to a collection"
    bl_label = "Group All Empties"

    def execute(self, context):
        collectionFound = False
        empty_collection_name = "_empties"
        old_obj = bpy.context.selected_objects
        scene = bpy.context.scene.objects
        empties = []

        bpy.ops.object.select_all(action='DESELECT')
        for myCol in bpy.data.collections:
            if myCol.name == empty_collection_name:
                collectionFound = True
                break

        for obj in scene:
            if obj.type == "EMPTY":
                empties.append(obj)

        if collectionFound == False and not len(empties) == 0:
            CreateCollections()
        else:
            self.report({'WARNING'}, "No empties left to sort")
        if len(empties) != 0:
            for obj in empties:
                if obj is not None:
                    for coll in obj.users_collection:
                        coll.objects.unlink(obj)
                    bpy.data.collections[empty_collection_name].objects.link(obj)
            self.report({'INFO'}, "Moved all empties")
    
        bpy.ops.object.select_all(action='DESELECT')

        for x in old_obj:     
            x.select_set(state=True)

        return {'FINISHED'}

class DarrowSetArmsCollection(bpy.types.Operator):
    bl_idname = "set.arms_coll"
    bl_description = "Move all armatures to a collection"
    bl_label = "Group All Armatures"

    def execute(self, context):
        collectionFound = False
        empty_collection_name = "_armatures"
        old_obj = bpy.context.selected_objects
        scene = bpy.context.scene.objects
        curves = []

        bpy.ops.object.select_all(action='DESELECT')
        for myCol in bpy.data.collections:
            if myCol.name == empty_collection_name:
                collectionFound = True
                break

        for obj in scene:
            if obj.type == "ARMATURE":
                curves.append(obj)

        if collectionFound == False and not len(curves) == 0:
            CreateCollections()
        else:
            self.report({'WARNING'}, "No armatures left to sort")
        if len(curves) != 0:
            for obj in curves:
                if obj is not None:
                    for coll in obj.users_collection:
                        coll.objects.unlink(obj)
                    bpy.data.collections[empty_collection_name].objects.link(obj)
            self.report({'INFO'}, "Moved all armatures")
    
        bpy.ops.object.select_all(action='DESELECT')

        for x in old_obj:     
            x.select_set(state=True)

        return {'FINISHED'}

#-----------------------------------------------------#  
#   Registration classes
#-----------------------------------------------------#
classes = (ORGANIZER_OT_Dummy,DARROW_PT_organizePanel,DARROW_PT_organizePanel_2,DARROW_PT_organizePanel_3,OrganizerSettings,DarrowSort,
            DarrowRenameSelectedHigh,DarrowRenameSelectedLow,DarrowCleanName,DarrowToggleEmpty,DarrowSetCollectionCutter,
            DarrowToggleCutters, DarrowCollapseOutliner, DarrowSetCollection, DarrowWireframe, DarrowSetCurveCollection, DarrowToggleCurves, DarrowToggleArms,DarrowSetArmsCollection,)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.OUTLINER_HT_header.prepend(collapse_pop_up)

    bpy.types.Scene.my_settings = bpy.props.PointerProperty(type=OrganizerSettings)

    bpy.types.Scene.cutterVis_Bool = bpy.props.BoolProperty(
        name="Vis Bool",
        description="Toggle visibility of cutters",
        default=False
    )
    bpy.types.Scene.volumeCurves_Bool = bpy.props.BoolProperty(
        name="Volume Curves",
        description="(This can be slow when a large amount of curves are present in the scene.",
        default=True
    )

    bpy.types.Scene.curveVis_Bool = bpy.props.BoolProperty(
        name="Vis Bool",
        description="Toggle visibility of curves",
        default=False
    )

    bpy.types.Scene.armsVis_Bool = bpy.props.BoolProperty(
        name="Vis Bool",
        description="Toggle visibility of armatures",
        default=False
    )

    bpy.types.Scene.iconOnly_Bool = bpy.props.BoolProperty(
        name="",
        description="Show only icons in outliner header",
        default=False
    )
    bpy.types.Scene.emptyVis_Bool = bpy.props.BoolProperty(
        name="Vis Bool",
        description="Toggle visibility of empties",
        default=False
    )

    bpy.types.Scene.parentcoll_string = bpy.props.StringProperty(
            name="Name",
            description="Collection Name",
            default="Collection"
        )

    bpy.types.Scene.compactBool = bpy.props.BoolProperty(
    name = "Advanced",
    description = "Toggle Advanced Mode",
    default = False
    )

    bpy.types.Scene.showWireframeBool = bpy.props.BoolProperty(
    name = "Toggle Wireframe",
    description = "Toggle visibility of wireframe mode",
    default = False
    )
    bpy.types.Scene.showSceneAdvancedOptionsBool = bpy.props.BoolProperty(
        name="Advanced",
        description="Show advanced options",
        default=False
    )

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    bpy.types.OUTLINER_HT_header.remove(collapse_pop_up)

if __name__ == "__main__":
    register()