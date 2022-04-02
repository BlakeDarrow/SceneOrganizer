#-----------------------------------------------------#  
#
#    Copyright (c) 2022 Blake Darrow <contact@blakedarrow.com>
#
#    See the LICENSE file for your full rights.
#
#-----------------------------------------------------#  
#   Imports
#-----------------------------------------------------# 
import bpy
from bpy.props import StringProperty, BoolProperty, PointerProperty
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       )
def updateBooleanVisibility(self, context):
    DarrowToggleCutters.execute(self,context)

def updateEmptiesVisibility(self, context):
    DarrowToggleEmpty.execute(self,context)

def updateRandomVisibility(self, context):
    bpy.context.space_data.shading.color_type = 'RANDOM'
    
def updateMaterialVisibility(self, context):
    bpy.context.space_data.shading.color_type = 'MATERIAL'

def updateWireframeVisibility(self, context):
    DarrowWireframe.execute(self,context)

class OrganizerSettings(bpy.types.PropertyGroup):
    booleanVis : BoolProperty(
        name = "Boolean Visibility",
        update = updateBooleanVisibility,
    )
    emptiesVis : BoolProperty(
        name = "Empties Visibility",
        update = updateEmptiesVisibility,
    )
    randomVis : BoolProperty(
        name = "Random Visibility",
        update = updateRandomVisibility,
    )
    materialVis : BoolProperty(
        name = "Material Visibility",
        update = updateMaterialVisibility,
    )
    wireframeVis : BoolProperty(
        name = "Wireframe Visibility",
        update = updateWireframeVisibility,
    )

#-----------------------------------------------------#         
#     handles ui panel 
#-----------------------------------------------------#  

class DarrowOrganizePanel():
    bl_category = "DarrowToolkit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

class DARROW_PT_organizePanel(DarrowOrganizePanel, bpy.types.Panel):
    bl_label = "Scene Organizer"
    bl_category = "DarrowToolkit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_idname = "DARROW_PT_organizePanel"

    def draw(self, context):
        layout = self.layout
        scn = bpy.context.scene
        col = layout.column(align=True)
        col.scale_y = 1
        col.label(text="Sort Objects by Type")
        cf3 = layout.box().column_flow(columns=2, align=True)
        cf3.scale_y = 1.33
        cf3.operator('set.cutter_coll',text="Booleans", icon="MOD_BOOLEAN")
        cf3.operator('set.empty_coll',text="Empties", icon="EMPTY_AXIS")
        if context.mode != 'OBJECT':
            cf3.enabled = False

        col = layout.column(align=True)
        col.scale_y = 1
        col.label(text="Viewport Options")
        cf2 = layout.box().column_flow(columns=2, align=True)
        cf2.scale_y = 1.33
        cf2.prop(scn.my_settings, 'booleanVis', toggle=True, text = "Booleans", icon = "MOD_BOOLEAN")
        rand = cf2.column(align=True)
        rand.prop(scn.my_settings, 'randomVis', toggle=True, text = "Random", icon = "MATFLUID")
        cf2.prop(scn.my_settings, 'wireframeVis', toggle=True, text = "Wireframe", icon = "FILE_3D")
        cf2.prop(scn.my_settings, 'emptiesVis', toggle=True, text = "Empties", icon = "EMPTY_AXIS")

        mat = cf2.column(align=True)
        mat.prop(scn.my_settings, 'materialVis', toggle=True, text = "Material", icon = "SHADING_TEXTURE")

        if scn.my_settings.randomVis == True:
                mat.enabled = False
        if scn.my_settings.materialVis == True:
                rand.enabled = False

class DARROW_PT_organizePanel_2(DarrowOrganizePanel, bpy.types.Panel):
    bl_parent_id = "DARROW_PT_organizePanel"
    bl_label = "Outliner Options"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        cf = layout.column_flow(columns=2, align=True)
        cf.scale_y = 1.33
        cf.operator('collapse.scene', text="Collapse", icon="SORT_ASC")
        cf.operator('darrow.sort_outliner',text="Sort", icon="SORTALPHA")
        col = layout.row()
        col.prop(context.scene,'iconOnly_Bool', text ="Show only icons")
       
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

#-----------------------------------------------------#
#    Sort outliner
#-----------------------------------------------------#
class DarrowSort(bpy.types.Operator):
    bl_label = "Sort Outliner"
    bl_idname = "darrow.sort_outliner"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Sort Outliner"

    def execute(self,context):
        case_sensitive = False
        for scene in bpy.data.scenes:
            sort_collection(scene.collection, case_sensitive)
        return {'FINISHED'}

#-----------------------------------------------------#
#    Toggle cutter visibility
#-----------------------------------------------------#
class DarrowToggleCutters(bpy.types.Operator):
    bl_label = "Toggle Cutters"
    bl_idname = "darrow.toggle_cutters"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Toggle the visabilty of boolean cutters."

    def execute(self, context):
        bpy.context.scene.cutterVis_Bool = not bpy.context.scene.cutterVis_Bool
        print(bpy.context.scene.cutterVis_Bool)
        for ob in bpy.data.objects:
            if ob.display_type == 'BOUNDS':
                parent = ob.users_collection[0].name
                try:
                    vlayer = bpy.context.scene.view_layers["View Layer"]
                except:
                    vlayer = bpy.context.scene.view_layers["ViewLayer"]
                if str(ob.users_collection[0].name) == "Darrow_Booleans":
                    vlayer.layer_collection.children[parent].hide_viewport = bpy.context.scene.cutterVis_Bool
                    vlayer.layer_collection.children[parent].hide_viewport = not vlayer.layer_collection.children[parent].hide_viewport

                ob.hide_set(bpy.context.scene.cutterVis_Bool)
                ob.hide_set(not bpy.context.scene.cutterVis_Bool)

        return {'FINISHED'}

# -----------------------------------------------------#
#    Toggle empty visibility
#-----------------------------------------------------#
class DarrowToggleEmpty(bpy.types.Operator):
    bl_label = "Toggle Empty"
    bl_idname = "darrow.toggle_empty"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Toggle the visabilty of empties"

    def execute(self, context):
        bpy.context.scene.emptyVis_Bool = not bpy.context.scene.emptyVis_Bool
        print(bpy.context.scene.emptyVis_Bool)

        for ob in bpy.data.objects:
            if ob.type == 'EMPTY':
                parent = ob.users_collection[0].name
                try:
                    vlayer = bpy.context.scene.view_layers["View Layer"]
                except:
                    vlayer = bpy.context.scene.view_layers["ViewLayer"]
                if str(ob.users_collection[0].name) == "Darrow_Empties":
                    vlayer.layer_collection.children[parent].hide_viewport = bpy.context.scene.emptyVis_Bool
                    vlayer.layer_collection.children[parent].hide_viewport = not vlayer.layer_collection.children[parent].hide_viewport

                ob.hide_set(bpy.context.scene.emptyVis_Bool)
                ob.hide_set(not bpy.context.scene.emptyVis_Bool)

            
        return {'FINISHED'}

#-----------------------------------------------------#
#     Collapse outliner
#-----------------------------------------------------#
class DarrowCollapseOutliner(bpy.types.Operator):
    bl_label = "Collapse Outliner"
    bl_idname = "collapse.scene"
    bl_description = "Collapse all items in the outliner"

    def execute(self, context):
        toggle_expand(context, 2)
        return {'FINISHED'}

#-----------------------------------------------------#  
#     handles wireframe display   
#-----------------------------------------------------#                 
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
    
#-----------------------------------------------------#
#    handles moving all Booleans's
#-----------------------------------------------------#
class DarrowSetCollectionCutter(bpy.types.Operator):
    bl_idname = "set.cutter_coll"
    bl_description = "Move all booleans to 'Darrow_Booleans' collection"
    bl_label = "Group All Booleans"

    def execute(self, context):
        collectionFound = False
        empty_collection_name = "Darrow_Booleans"
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

        if collectionFound == False and not len(bools) == 0:
            empty_collection = bpy.data.collections.new(empty_collection_name)
            bpy.context.scene.collection.children.link(empty_collection)
            bpy.data.collections[empty_collection_name].color_tag = 'COLOR_01'
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

#-----------------------------------------------------#
#    handles moving all empty's
#-----------------------------------------------------#
class DarrowSetCollection(bpy.types.Operator):
    bl_idname = "set.empty_coll"
    bl_description = "Move all empties to 'Darrow_Empties' collection"
    bl_label = "Group All Empties"

    def execute(self, context):
        collectionFound = False
        empty_collection_name = "Darrow_Empties"
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
            empty_collection = bpy.data.collections.new(empty_collection_name)
            bpy.context.scene.collection.children.link(empty_collection)
            bpy.data.collections[empty_collection_name].color_tag = 'COLOR_01'
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

def toggle_expand(context, state):
    area = next(a for a in context.screen.areas if a.type == 'OUTLINER')
    bpy.ops.outliner.show_hierarchy({'area': area}, 'INVOKE_DEFAULT')
    for i in range(state):
        bpy.ops.outliner.expanded_toggle({'area': area})
    area.tag_redraw()

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

#-----------------------------------------------------#  
#   Registration classes
#-----------------------------------------------------#
classes = (ORGANIZER_OT_Dummy,DARROW_PT_organizePanel,DARROW_PT_organizePanel_2,OrganizerSettings,DarrowSort,DarrowToggleEmpty,DarrowSetCollectionCutter,DarrowToggleCutters, DarrowCollapseOutliner, DarrowSetCollection, DarrowWireframe,)

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

def unregister():

    for cls in classes:
        bpy.utils.unregister_class(cls)
        
    bpy.types.OUTLINER_HT_header.remove(collapse_pop_up)

if __name__ == "__main__":
    register()