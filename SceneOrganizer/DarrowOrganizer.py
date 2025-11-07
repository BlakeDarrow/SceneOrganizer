# ##### BEGIN GPL LICENSE BLOCK #####
#
#   Copyright (C) 2022, 2023  Blake Darrow <contact@blakedarrow.com>
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

import bpy
import bmesh
from bpy.props import BoolProperty, CollectionProperty, IntProperty, FloatVectorProperty, StringProperty
from bpy.types import Menu, PropertyGroup
import time
import datetime
from mathutils import Vector

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

def updateOverlapVisibility(self, context):
    DarrowToggleOverlap.execute(self,context)

class StoredPosition(PropertyGroup):
    """Stores a single position (Vec3)"""
    position: FloatVectorProperty(
        name="Position",
        description="Stored 3D position",
        size=3,
        default=(0.0, 0.0, 0.0)
    )
    name: StringProperty(
        name="Name",
        description="Name for this position slot",
        default="Position"
    )

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

def store_and_execute_states(collection, case=False):
    coll = bpy.context.scene.collection
    colls = []
    states = []

    obj_states = []
    objs = []

    for c in traverse_tree(coll):
        if c.name in bpy.data.collections:
                state = get_layer_collection(c).hide_viewport
                if c.name not in colls:
                    colls.append(c)
                    states.append(state)

    for col in bpy.data.collections:
        get_layer_collection(col).hide_viewport = False

    for x in bpy.context.scene.objects:
        if x not in obj_states:
            state = x.visible_get()
            objs.append(x)
            obj_states.append(state)

    sort_collection(bpy.context.scene.collection, False)

    for x in range(0,len(colls)):
        if colls[x] in colls:
            get_layer_collection(colls[x]).hide_viewport = states[x]

    for x in range(0,len(objs)):
        if objs[x] in objs:
            objs[x].hide_set(not obj_states[x])

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

def get_layer_collection(collection):
    '''Returns the view layer LayerCollection for a specified Collection'''
    def scan_children(lc, result=None):
        for c in lc.children:
            if c.collection == collection:
                return c
            result = scan_children(c, result)
        return result

    return scan_children(bpy.context.view_layer.layer_collection)

def toggleCollectionVis(ob, collectionName, bool, parentCollName = None):
    if str(ob.users_collection[0].name) == collectionName:
        """Blender makes things hard and throws an error if you try to directly access a nested collection from the viewlayer. This was a workaround I found online."""

        coll = get_layer_collection(bpy.data.collections[collectionName])
        coll.hide_viewport = bool
        coll.hide_viewport = not coll.hide_viewport

        # Make sure the parent collection "_SceneOrganizer" is visible
        get_layer_collection(bpy.data.collections["_SceneOrganizer"]).hide_viewport = False

        # If additional parent collection, make sure its visible
        if parentCollName != None:
            coll2 = get_layer_collection(bpy.data.collections[parentCollName])

            coll2.hide_viewport = bool
            coll2.hide_viewport = not coll2.hide_viewport

            bpy.data.collections[parentCollName].hide_viewport = False

    ob.hide_set(bool)
    ob.hide_set(not bool)

def MakeCollections(name, color, bool):
    collectionFound = False

    for myCol in bpy.data.collections:
        if myCol.name == "_SceneOrganizer":
            collectionFound = True
            master_collection = bpy.data.collections["_SceneOrganizer"]
            break

    if collectionFound == False:    
        master_collection = bpy.data.collections.new("_SceneOrganizer")
        bpy.context.scene.collection.children.link(master_collection)
    new_collection = bpy.data.collections.new(name)

    bpy.data.collections[master_collection.name].color_tag = 'COLOR_05'
    bpy.data.collections[new_collection.name].color_tag = color
    master_collection.children.link(new_collection)

    get_layer_collection(new_collection).hide_viewport = not bool

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
    overlapVis : BoolProperty(
        name = "Overlapping Visibility",
        update = updateOverlapVisibility,
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
        col.label(text="Overlap Searching (Sequential)")
        col_1 = layout.box().column()
        col_1.scale_y = 1.1
      
        panel = col_1.column(align=True)
        panel.prop(context.scene, "originTolerance", text="Origin", slider=True)
        panel.prop(context.scene, "boundsTolerance", text="Bounds", slider=True)
        panel.prop(context.scene, "vertTolerance", text="Vertex", slider=True)

        col = layout.column(align=True)
        col.label(text="Viewport Tools")
        col_1 = layout.box().column()
        panel = col_1.column(align=True)
        col_1.scale_y = 1.1
        cf4 = panel.column_flow(columns=2, align=True)
        cf4.prop(scn.my_settings, 'materialVis',text = "Material", toggle = True)
        
        rand = cf4.column(align=True)
        rand.prop(scn.my_settings, 'randomVis', text = "Random", toggle = True)
        mat = panel.row(align=True)
        mat.prop(scn.my_settings, 'wireframeVis',text = "Wireframe", toggle = True)

        if scn.my_settings.randomVis == True:
                mat.enabled = False
        if scn.my_settings.materialVis == True:
                rand.enabled = False

        # Position Storage Section
        col = layout.column(align=True)
        col.label(text="Position Storage")
        col_1 = layout.box().column()
        col_1.scale_y = 1.1
        
        obj = context.active_object
        if obj is not None:
            panel = col_1.column(align=True)
            
            # Add/Remove buttons
            row = panel.row(align=True)
            row.operator("organizer.add_position_slot", text="", icon='ADD')
            row.operator("organizer.remove_position_slot", text="", icon='REMOVE')
            
            # Display stored positions
            if len(obj.stored_positions) > 0:
                panel.separator()
                for idx, stored_pos in enumerate(obj.stored_positions):
                    row = panel.row(align=True)
                    
                    # Editable name field
                    row.prop(stored_pos, "name", text="")
                    
                    # Store button
                    store_op = row.operator("organizer.store_position", text="", icon='EXPORT')
                    store_op.index = idx
                    
                    # Retrieve button
                    retrieve_op = row.operator("organizer.retrieve_position", text="", icon='IMPORT')
                    retrieve_op.index = idx
                    
                    # Display position
                    sub = panel.row(align=True)
                    sub.scale_y = 0.8
                    sub.label(text=f"  ({stored_pos.position[0]:.3f}, {stored_pos.position[1]:.3f}, {stored_pos.position[2]:.3f})")
            else:
                panel.label(text="No position slots. Click + to add.", icon='INFO')
        else:
            col_1.label(text="Select an object", icon='ERROR')

        if bpy.context.scene.showSceneAdvancedOptionsBool == True:

            box = layout.box()
            col = box.column(align=True)
            col.scale_y = 1.1
            col.label(text="Overlap Sorting")
            col.prop(context.scene, "overlapSortMethod", text="")
            col.prop(context.scene, "maxSearchVerts", text="Vertex Search Depth", slider = True)
            col.prop(context.scene,'excludeOverlapSort', text ="Disable Overlap in Sort All", toggle = True)
            col.separator()
            col.prop(context.scene, "volumeCurves_Bool", text="Disable Zero-Volume Checking", invert_checkbox = True ,toggle = True)
            col.prop(context.scene,'iconOnly_Bool', text ="Disable Button Text in Outliner", toggle = True)
            
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

class ORGANIZER_OT_StorePosition(bpy.types.Operator):
    bl_idname = "organizer.store_position"
    bl_label = "Store Position"
    bl_description = "Store the current object's position"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        
        if self.index >= len(obj.stored_positions):
            self.report({'WARNING'}, "Invalid index")
            return {'CANCELLED'}
        
        obj.stored_positions[self.index].position = obj.location
        self.report({'INFO'}, f"Stored position: {obj.location}")
        return {'FINISHED'}

class ORGANIZER_OT_RetrievePosition(bpy.types.Operator):
    bl_idname = "organizer.retrieve_position"
    bl_label = "Retrieve Position"
    bl_description = "Set the current object's position to the stored value"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        
        if self.index >= len(obj.stored_positions):
            self.report({'WARNING'}, "Invalid index")
            return {'CANCELLED'}
        
        obj.location = obj.stored_positions[self.index].position
        self.report({'INFO'}, f"Retrieved position: {obj.location}")
        return {'FINISHED'}

class ORGANIZER_OT_AddPositionSlot(bpy.types.Operator):
    bl_idname = "organizer.add_position_slot"
    bl_label = "Add Position Slot"
    bl_description = "Add a new position storage slot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        
        obj.stored_positions.add()
        return {'FINISHED'}

class ORGANIZER_OT_RemovePositionSlot(bpy.types.Operator):
    bl_idname = "organizer.remove_position_slot"
    bl_label = "Remove Position Slot"
    bl_description = "Remove the last position storage slot"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({'WARNING'}, "No active object")
            return {'CANCELLED'}
        
        if len(obj.stored_positions) > 0:
            obj.stored_positions.remove(len(obj.stored_positions) - 1)
        return {'FINISHED'}

class DarrowSort(bpy.types.Operator):
    bl_label = "Sort Outliner"
    bl_idname = "darrow.sort_outliner"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Sort Outliner"

    def execute(self,context):
        case_sensitive = False
        for scene in bpy.data.scenes:
            store_and_execute_states(scene.collection, case_sensitive)
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

class DarrowClearAnnotate(bpy.types.Operator):
    bl_label = "Clear All Annotations"
    bl_idname = "darrow.clear_annotations"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Clear ALL annotations"

    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

        grease_pencil_blocks = [block for block in bpy.data.grease_pencils]
        for gpencil in grease_pencil_blocks:
            bpy.data.grease_pencils.remove(gpencil)
     
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
                    toggleCollectionVis(ob, "_Cutters", bpy.context.scene.cutterVis_Bool)

        return {'FINISHED'}

class DarrowToggleOverlap(bpy.types.Operator):
    bl_label = "Toggle Overlap"
    bl_idname = "darrow.toggle_overlap"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Toggle the visibility of curves."

    def execute(self, context):
        bpy.context.scene.overlapVis_Bool = not bpy.context.scene.overlapVis_Bool

        for ob in bpy.data.objects:
            if "Match: " in ob.users_collection[0].name:
                toggleCollectionVis(ob, ob.users_collection[0].name, bpy.context.scene.overlapVis_Bool, parentCollName="_Overlapping")
                   
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
                        toggleCollectionVis(ob, "_Curves", bpy.context.scene.curveVis_Bool)
                else:
                    toggleCollectionVis(ob, "_Curves", bpy.context.scene.curveVis_Bool)
                   
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
                toggleCollectionVis(ob, "_Armatures", bpy.context.scene.armsVis_Bool)
                
        return {'FINISHED'}

class DarrowToggleEmpty(bpy.types.Operator):
    bl_label = "Toggle Empty"
    bl_idname = "darrow.toggle_empty"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Toggle the visibility of empties"

    def execute(self, context):
        bpy.context.scene.emptyVis_Bool = not bpy.context.scene.emptyVis_Bool

        for ob in bpy.data.objects:
            if ob.type == 'EMPTY' or ob.type == "LATTICE":
                toggleCollectionVis(ob, "_Empties", bpy.context.scene.emptyVis_Bool)

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
        empty_collection_name = "_Cutters"
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
            MakeCollections("_Cutters","COLOR_01", bpy.context.scene.cutterVis_Bool)
            
        if len(bools) != 0:
            for obj in bools:
                if obj is not None:
                    for coll in obj.users_collection:
                        coll.objects.unlink(obj)
                    
                    bpy.data.collections[empty_collection_name].objects.link(obj)
            self.report({'INFO'}, "Moved all booleans")
       
        bpy.ops.object.select_all(action='DESELECT')

        for x in old_obj:     
            x.select_set(state=True)

        return {'FINISHED'}

class DarrowSetCurveCollection(bpy.types.Operator):
    bl_idname = "set.curve_coll"
    bl_description = "Move all curves without volume to a collection"
    bl_label = "Group All Curves"

    def execute(self, context):
        collectionFound = False
        empty_collection_name = "_Curves"
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
            MakeCollections("_Curves","COLOR_07",context.scene.my_settings.curveVis)
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

class DarrowSetOverlap(bpy.types.Operator):
    bl_idname = "set.overlap"
    bl_description = "Move all overlapping objects. Generally helpful to sort LODs. This can be slow with large scenes. You can disable this from running in the 'Sort All' operation inside the 'Scene Organizer' panel settings"
    bl_label = "Group All Overlapping Objects."
    bl_options = {'UNDO'}
 
    def find_overlapping_objects(self, context):
        def check_objs_overlap(obj_list):

            origin_tolerance = bpy.context.scene.originTolerance
            bounds_tolerance = bpy.context.scene.boundsTolerance
            vert_tolerance = bpy.context.scene.vertTolerance

            def find_origins(objects, tolerance):
                matching_origins = dict()

                for obj1 in objects:
                    origin1 = obj1.location
                    matching_origins[str(origin1)] = []

                for obj1 in objects:
                    origin1 = obj1.location

                    for obj2 in objects:
                        if obj2 in matching_origins[str(origin1)]:
                            continue

                        if obj2 != obj1:
                            origin2 = obj2.location
                            distance = (origin1 - origin2).length
                            if distance <= tolerance:
                                matching_origins[str(origin1)].append(obj2)

                return matching_origins
            
            def find_bounds_verts(origin_dict, origin_tolerance, bounds_tolerance, vertex_tolerance):

                matching_bounds = dict()
                all_bounds = dict()

                for key in origin_dict:

                    for obj in origin_dict[key]:

                        name = obj.name
                        bounds = obj.bound_box
                        origin = obj.location
                        object = obj
                        matrix = [obj.matrix_world @ Vector(bound_vertex) for bound_vertex in bounds]
                        all_bounds[name] = [matrix, origin, object]

                match = 0
                max_search_verts = bpy.context.scene.maxSearchVerts
                grouped_objects = {}  # To keep track of which objects are grouped together

                for name1, data1 in all_bounds.items():

                    if name1 not in grouped_objects:
                        group = [name1]
                        shared_origin = data1[1]  # Origin of the first object in the group. Close enough to use as key for shared objects

                        for name2, data2 in all_bounds.items():
                            if name1 != name2 and name2 not in grouped_objects:
                                bounds1, origin1, object1 = data1
                                bounds2, origin2, object2 = data2
                                object2 = data2[2]
                                origin_distance = (origin1 - origin2).length

                                if origin_distance <= origin_tolerance:
                                    overlap = any(
                                        all(
                                            abs(v1 - v2) <= bounds_tolerance
                                            for v1, v2 in zip(bound1, bound2)
                                        )
                                        for bound1, bound2 in zip(bounds1, bounds2)
                                    )

                                    if overlap:
                                        vertices1 = [object1.matrix_world @ Vector(v.co) for v in object1.data.vertices[:max_search_verts]]
                                        vertices2 = [object2.matrix_world @ Vector(v.co) for v in object2.data.vertices[:max_search_verts]]
                                        vert_overlap = False
                                        for v1 in vertices1:
                                            for v2 in vertices2:
                                                if (v1 - v2).length <= vertex_tolerance:
                                                    vert_overlap = True
                                                    break
                                            if vert_overlap:
                                                break

                                    if overlap and vert_overlap:
                                        group.append(name2)
                                        grouped_objects[name2] = True
                                        shared_origin = shared_origin

                        if len(group) > 1:
                            match += 1
                            match_key = f"Match: {match} - Origin: {shared_origin}"
                            matching_bounds[match_key] = group

                return matching_bounds
            
            matching_origins = find_origins(obj_list, origin_tolerance)
            matching_bounds = find_bounds_verts(matching_origins, origin_tolerance, bounds_tolerance, vert_tolerance)

            return matching_bounds

        def find_most_verts(overlapping_objs):
            sortMethod = context.scene.overlapSortMethod

            for obj_name, matches in overlapping_objs.items():
                object_with_highest_vertex_count = None
                highest_vertex_count = 0
                object_with_lowest_vertex_count = None
                lowest_vertex_count = float('inf') 

                for match_obj_name in matches:
                    obj = bpy.data.objects[match_obj_name]
                    vertex_count = len(obj.data.vertices)

                    if sortMethod == "Highest":
                        if vertex_count >= highest_vertex_count:
                            highest_vertex_count = vertex_count
                            object_with_highest_vertex_count = obj

                    if sortMethod == "Lowest":
                        if vertex_count <= lowest_vertex_count:
                            lowest_vertex_count = vertex_count
                            object_with_lowest_vertex_count = obj 


                    overlapping_objs[obj_name] = [matches, object_with_highest_vertex_count, object_with_lowest_vertex_count]

            return overlapping_objs

        def move_to_collections(matches_dict):
            overlap_collection_name = "_Overlapping"
            collectionFound = False
            for myCol in bpy.data.collections:
                if myCol.name == overlap_collection_name:
                    collectionFound = True
                    break

            if collectionFound == False and len(matches_dict) != 0:
                MakeCollections(overlap_collection_name, "COLOR_06", context.scene.my_settings.overlapVis)
    
            # Create the parent overlapping collection if not found
            if overlap_collection_name not in bpy.data.collections:
                overlap_collection = bpy.data.collections.new(overlap_collection_name)
                bpy.context.scene.collection.children.link(overlap_collection)
            
            bpy.ops.ed.undo_push()
            
            for match_key, data_list in matches_dict.items():
                sortMethod = context.scene.overlapSortMethod
                if sortMethod == "Highest":
                    name = str(data_list[1].name)
                            
                if sortMethod == "Lowest":
                    name = str(data_list[2].name)
                       
                child_collection_name = "Match: " +  name
                if child_collection_name not in bpy.data.collections:
                    child_collection = bpy.data.collections.new(child_collection_name)
                    bpy.data.collections[child_collection_name].color_tag = 'COLOR_08'
                    bpy.data.collections[overlap_collection_name].children.link(child_collection)
                else:
                    child_collection = bpy.data.collections[child_collection_name]
               
                objects_to_link = data_list[0]

                for obj_name in objects_to_link:
                    obj = bpy.data.objects.get(obj_name)
                    if sortMethod == "Highest":
                        if obj and obj != data_list[1]: #data_list[1] is highest vert count object
                            for coll in obj.users_collection:
                                coll.objects.unlink(obj)
                            child_collection.objects.link(obj)
                        else:
                            if "Match:" in obj.users_collection[0].name:
                                for coll in obj.users_collection:
                                    coll.objects.unlink(obj)
                                context.scene.collection.objects.link(obj)

                    if sortMethod == "Lowest":
                        if obj and obj != data_list[2]: #data_list[2] is lowest vert count object
                            for coll in obj.users_collection:
                                coll.objects.unlink(obj)
                            child_collection.objects.link(obj)
                        else:
                            if "Match:" in obj.users_collection[0].name:
                                for coll in obj.users_collection:
                                    coll.objects.unlink(obj)
                                context.scene.collection.objects.link(obj)

            bpy.ops.ed.undo_push()
            bpy.context.view_layer.update()

        search_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and obj.users_collection[0].name != "_Overlapping"]

        overlapping_objs = check_objs_overlap(search_objects)
        highestLODs = find_most_verts(overlapping_objs)
        move_to_collections(highestLODs)

        #print(highestLODs)

        return {'FINISHED'}

    def execute(self, context):
        context = bpy.context
        start_time = time.perf_counter()
        DarrowSetOverlap.find_overlapping_objects(DarrowSetOverlap, context)
        end_time = time.perf_counter()

        run_time = end_time - start_time
        execution_time_delta = datetime.timedelta(seconds=run_time)
        minutes = execution_time_delta.seconds // 60
        seconds = execution_time_delta.seconds % 60
        milliseconds = execution_time_delta.microseconds // 1000
        total_time = f"Time: {minutes} minutes and {seconds}.{milliseconds:03} seconds."
        self.report({'INFO'}, total_time)
        return {'FINISHED'}
    
class DarrowSetCollection(bpy.types.Operator):
    bl_idname = "set.empty_coll"
    bl_description = "Move all empties to a collection"
    bl_label = "Group All Empties and Lattices"

    def execute(self, context):
        collectionFound = False
        empty_collection_name = "_Empties"
        old_obj = bpy.context.selected_objects
        scene = bpy.context.scene.objects
        empties = []

        bpy.ops.object.select_all(action='DESELECT')
        for myCol in bpy.data.collections:
            if myCol.name == empty_collection_name:
                collectionFound = True
                break

        for obj in scene:
            if obj.type == "EMPTY" or obj.type == "LATTICE":
                empties.append(obj)

        if collectionFound == False and not len(empties) == 0:
            MakeCollections("_Empties", "COLOR_03",context.scene.my_settings.emptiesVis)
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
        empty_collection_name = "_Armatures"
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
            MakeCollections("_Armatures", "COLOR_04", context.scene.my_settings.armsVis)
        
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

class DarrowSetAllCollections(bpy.types.Operator):
    bl_idname = "set.all_coll"
    bl_description = "Sort all types and send to respective collections"
    bl_label = "Group All"

    def execute(self, context):
        DarrowSetCollectionCutter.execute(self,context)
        DarrowSetCurveCollection.execute(self,context)
        DarrowSetCollection.execute(self,context)
        DarrowSetArmsCollection.execute(self,context)
        if not bpy.context.scene.excludeOverlapSort:
            DarrowSetOverlap.execute(self,context)
        return {'FINISHED'}

class DARROW_MT_organizerPie(Menu):
    bl_label = "Scene Organizer"

    def draw(self, context):
        layout = self.layout
        yScale = 1.5
        xScale = 1.3
        pie = layout.menu_pie()
        pie.prop(context.scene.my_settings, 'booleanVis',text = "Cutters", toggle=True, icon="MOD_BOOLEAN")
        pie.prop(context.scene.my_settings, 'emptiesVis',text = "Empties", toggle=True, icon="EMPTY_AXIS")
        pie.prop(context.scene.my_settings, 'armsVis',text = "Armatures", toggle=True, icon="ARMATURE_DATA")
        pie.prop(context.scene.my_settings, 'curveVis',text = "Curves", toggle=True, icon="MOD_CURVE")
        pie.prop(context.scene.my_settings, 'overlapVis',text = "Overlap", toggle=True, icon="MESH_CUBE")
        pie.separator()
        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.separator()
        gap.separator()
        gap.scale_y = 7
        self.top_header(other)
        other_menu = other.box().column(align=True)
        other_menu.scale_y=yScale
        other_menu.scale_x=xScale
        other_menu.label(text="Sort by type")
        other_menu.operator("set.all_coll", text="Sort All", icon="OUTLINER_OB_GROUP_INSTANCE")
        other_menu.separator()
        other_menu.operator("set.arms_coll", text="Armatures", icon="ARMATURE_DATA")
        other_menu.operator("set.curve_coll", text="Curves", icon="MOD_CURVE")
        other_menu.operator("set.cutter_coll", text="Cutters",icon="MOD_BOOLEAN")
        other_menu.operator("set.empty_coll", text="Empties", icon="EMPTY_AXIS")
        other_menu.operator("set.overlap", text="Overlap", icon="MESH_CUBE")
        other = pie.column()
        gap = other.column()
        gap.separator()
        gap.separator()
        gap.separator()
        gap.scale_y = 7
        self.top_header(other)
        other_menu = other.box().column(align=True)
        other_menu.scale_y=yScale
        other_menu.scale_x=xScale
        other_menu.label(text="Other tools")
        other_menu.operator('collapse.scene', text="Collapse", icon="SORT_ASC")
        other_menu.operator('darrow.sort_outliner',text="Sort", icon="SORTALPHA")
        other_menu.separator()
        other_menu.operator("darrow.rename_high", text="Add 'high'",)
        other_menu.operator("darrow.rename_low", text="Add 'low'",)
        other_menu.operator("darrow.rename_clean", text="Strip Name", icon="TRASH")
        other_menu.operator("darrow.clear_annotations", text="Clear Pencil", icon="TRASH")
        
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)
        
    def top_header(self,layout):
        top_header = layout.column()
        top_header.scale_y = 0.8
        top_header.label(text="")

class SceneOrganizerPopUpCallback(bpy.types.Operator):
    bl_label = "Scene Organizer Popup"
    bl_idname = "darrow.organizer_popup_callback"

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="DARROW_MT_organizerPie")
        return {'FINISHED'}

def sceneDropdown(self, context):
    layout = self.layout
    layout.operator('darrow.organizer_popup_callback', icon="RESTRICT_VIEW_ON", text = "Scene Organizer")

classes = (ORGANIZER_OT_Dummy,StoredPosition,ORGANIZER_OT_StorePosition,ORGANIZER_OT_RetrievePosition,
            ORGANIZER_OT_AddPositionSlot,ORGANIZER_OT_RemovePositionSlot,
            DARROW_PT_organizePanel,OrganizerSettings,DarrowSort,
            DarrowRenameSelectedHigh,DarrowRenameSelectedLow,DarrowCleanName,DarrowToggleEmpty,DarrowSetCollectionCutter,
            DarrowToggleCutters, DarrowCollapseOutliner, DarrowToggleOverlap, DarrowSetOverlap, DarrowSetCollection, DarrowWireframe, DarrowSetCurveCollection, DarrowToggleCurves, DarrowToggleArms,DarrowSetArmsCollection,
            SceneOrganizerPopUpCallback,DARROW_MT_organizerPie,DarrowSetAllCollections, DarrowClearAnnotate)
addon_keymaps = []

def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(SceneOrganizerPopUpCallback.bl_idname, 'E', 'PRESS', shift=True)
        addon_keymaps.append((km, kmi))

    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.append(sceneDropdown)
    bpy.types.OUTLINER_HT_header.prepend(collapse_pop_up)

    bpy.types.Scene.my_settings = bpy.props.PointerProperty(type=OrganizerSettings)

    bpy.types.Scene.overlapSortMethod = bpy.props.EnumProperty(
        description="Which objects should stay visible and where they are when overlap has been found",
        default="Highest",
        items=[
            ('Highest', 'Keep Highest Visible', 'Most Verts'),
            ('Lowest', 'Keep Lowest Visible', 'Least Verts'),
        ],
    )

    bpy.types.Scene.cutterVis_Bool = bpy.props.BoolProperty(
        name="Vis Bool",
        description="Toggle visibility of cutters",
        default=False
    )

    bpy.types.Scene.maxSearchVerts = bpy.props.IntProperty(
        name="Max Vertex Search Count",
        description="Max vertices to search through in any given mesh when sorting by overlap",
        default=150,
        max=1000,
        min=0
    )

    bpy.types.Scene.excludeOverlapSort = bpy.props.BoolProperty(
        name="Exclude overlap",
        description="Exclude overlap from sorting",
        default=False
    )

    bpy.types.Scene.volumeCurves_Bool = bpy.props.BoolProperty(
        name="Volume Curves",
        description="Only sort curves that have non-zero volume",
        default=True
    )

    bpy.types.Scene.curveVis_Bool = bpy.props.BoolProperty(
        name="Vis Bool",
        description="Toggle visibility of curves",
        default=False
    )

    bpy.types.Scene.overlapVis_Bool = bpy.props.BoolProperty(
        name="Overlap Bool",
        description="Toggle visibility of overlapping mesh",
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

    bpy.types.Scene.originTolerance = bpy.props.FloatProperty(
        name="Origin Tolerance (Distance)",
        description="Amount of distance between object origin points when searching for overlapping faces",
        default = 0.01,
        soft_min = 0.01,
        soft_max = 1
    )

    bpy.types.Scene.boundsTolerance = bpy.props.FloatProperty(
        name="Bounds Tolerance (Distance)",
        description="Amount of bounding box padding when searching for overlapping faces",
        default = 0.35, 
        soft_min = 0.01,
        soft_max = 0.1
    )

    bpy.types.Scene.vertTolerance = bpy.props.FloatProperty(
        name="Vertex Tolerance (Distance)",
        description="Amount of vertex search distance when searching for overlapping faces",
        default = .5,
        soft_min = 0.1,
        soft_max = 2
    )

    # Register stored positions on objects
    bpy.types.Object.stored_positions = CollectionProperty(type=StoredPosition)

def unregister():

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # Unregister stored positions
    del bpy.types.Object.stored_positions

    for cls in classes:
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_object_context_menu.remove(sceneDropdown)
    bpy.types.OUTLINER_HT_header.remove(collapse_pop_up)

if __name__ == "__main__":
    register()