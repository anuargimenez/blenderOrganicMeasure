# Drop to plane draait soms 180 graden, dat is verbeterd.
# DXF exporter toegevoegd

bl_info = {
    "name": "Cross Sections",
    "author": "Tiemen Blankert",
    "version": (0, 2),
    "blender": (2, 93, 2),
    "location": "View3D > side bar > edit tab  ",
    "description": "by vfxemd.com Make a cross section from a mesh",
    "warning": "",
    "doc_url": "",
    "category": "deform",
}

import bpy
import math
import mathutils
import bmesh 
from mathutils import Vector,Matrix
from mathutils import Euler
v2 = Vector((0,0,1))
############################
####     PLANES   ##########
############################
class VIEW_PT_Snijvlakken(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"
    bl_options = {'DEFAULT_CLOSED'}    
    bl_label = "Cross section"
    #bl_context_mode = 'EDIT'
    #bl_context = "mesh_edit"
    def draw(self, context):

        layout = self.layout
        col = layout.column()
        box = layout.box()
        box.label(text = 'Create a cut plane')
        if bpy.context.mode == 'OBJECT':
            x = box.operator('mesh.snijvlakken_maken',
                                text = 'Cut plane New',
                                icon='EVENT_P')
        #col = layout.column()
        #col.separator()            
            
        if bpy.context.mode == 'EDIT_MESH':
            box.operator('mesh.snijvlakken_maken_editm',
                                text = 'Cut plane Copy',
                                icon='EVENT_P')
                
        col.separator()
        #col.label(text = 'snijden ')
        col.separator()
        box = layout.box()
        box.label(text = 'Cross section')
        #column = layout.column(align=True)
        
        box.operator('mesh.doorsnijden',
                                text = 'Make Cross section',
                                icon='EVENT_C')        
        box.operator('mesh.doorsnede_platleggen',
                                text = 'Drop on XY plane',
                                icon='AXIS_TOP')
                                
        if bpy.context.mode == 'OBJECT':
            layout = self.layout
            col = layout.column(align=True)
            box =layout.box()
            box.prop(context.scene,'dxf_export_los')# hier staat het file path(propperty)
            

            naam = bpy.path.display_name_from_filepath(bpy.context.scene.dxf_export_los)
            
            #naam_label = ('File Name;  '+naam)
            box.label(text = 'File name:  '+naam)

            box.prop(context.scene,'scale_factor_3')# hier de schaal factor
            box.operator('export_scene.export_dxf_file_los')# het uitvoeren van de export
            
            column = layout.column()
             
##############################################
####     CREATE CUTPLANE EDITMODE   ##########
##############################################                                
class MESH_OT_snijvlakken_maken_editm(bpy.types.Operator):
    """Select a plane, the cutting plane is created parallel to this plane """
    bl_idname = "mesh.snijvlakken_maken_editm"  
    bl_label = "snijvlakken_editm"
    bl_options = {'REGISTER', 'UNDO'} 
    

    
    def execute(self,context):
        

        
        # collectie maken alleen als nodig
        def nieuwe_collectie_maken():
            col = bpy.data.collections.new('Cut Planes')
            bpy.context.scene.collection.children.link(col)
            
        # kleur maken alleen als nodig    
        def nieuwe_kleur():
            kl = bpy.data.materials.new(name='kleur')
            kl.diffuse_color=(1,0.2,0.2,0.5)
            
        #vlak maken    
        def vlak_maken(lx,ly,lz,rx,ry,rz): 
            '''   
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False,
                                            size = 2,
                                             align='WORLD',
                                              location=(lx,ly,lz),
                                               scale=(1, 1, 1),
                                               rotation=(rx,ry,rz),
                                              )
            '''
            bpy.ops.mesh.primitive_circle_add(radius=1,
                                         fill_type='NGON',
                                          enter_editmode=False,
                                           align='WORLD',
                                           location=(lx,ly,lz),rotation=(rx,ry,rz), 
                                           scale=(1, 1, 1))
            
            ob = bpy.context.object
            ob.name = 'Cut Plane'
            col = ob.users_collection
            # kijken of kleur bestaat anders maken
            try:
                bpy.context.object.data.materials.append(bpy.data.materials['kleur'])
            except:
                nieuwe_kleur()
                bpy.context.object.data.materials.append(bpy.data.materials['kleur'])
                
            
            # kijken of collectie bestaat anders maken 
            try:
                bpy.data.collections['Cut Planes']
            except:
                nieuwe_collectie_maken()
            # als de snijvlak collectie al actief was is het object al in de goede collectie gemaakt
            # het kan dan niet nog een keer aan de collectie gelinked worden
            try:    
                bpy.data.collections['Cut Planes'].objects.link(ob)
            except:
                pass            
            if col[0].name != 'Cut Planes':
                col[0].objects.unlink(ob)                
                
        # vlak maken van een in editmode gekozen vlak, er wordt een nieuw object gemaakt        
        def vlak_van_bmesh():
            v1 = mathutils.Vector((0,0,1))
            ob = bpy.context.object
            me = ob.data
            bm = bmesh.from_edit_mesh(me)
            for f in bm.faces:
                if f.select:
                    normaal = f.normal
                    lok = f.calc_center_median()+ob.location
                    break
            verschil = v1.rotation_difference(normaal)
            verschil_eul = mathutils.Quaternion.to_euler(verschil)

            return(verschil_eul,lok)
        
        
        ######     PROGRAMMA    #######
        #if bpy.context.mode == 'OBJECT':

        vers,lok = vlak_van_bmesh()
        bpy.ops.object.editmode_toggle()
        vlak_maken(lok[0],lok[1],lok[2],vers[0],vers[1],vers[2],)
            
            
        return{'FINISHED'}                                         
##############################################
####     CREATE CUTPLANE OBJECTMODE   ########
############################################## 

class MESH_OT_snijvlakken_maken(bpy.types.Operator):
    """Create a new cutting plane at (0,0,0), the direction can be adjusted"""
    bl_idname = "mesh.snijvlakken_maken"  
    bl_label = "Cut Plane"
    bl_options = {'REGISTER', 'UNDO'} 
    
    vlakrichting: bpy.props.EnumProperty(
        name="Pane Direction",
        items =[('XY','XY',''),('XZ','XZ',''),('YZ','YZ','')],
        default = 'XY'
        )
   
   
    maat: bpy.props.FloatProperty(
        name="Size",
        default=1,
    )
    

    
    def execute(self,context):
        
        vlakrichting = self.vlakrichting
        maat = self.maat
        
        # collectie maken alleen als nodig
        def nieuwe_collectie_maken():
            col = bpy.data.collections.new('Cut Planes')
            bpy.context.scene.collection.children.link(col)
            
        # kleur maken alleen als nodig    
        def nieuwe_kleur():
            kl = bpy.data.materials.new(name='kleur')
            kl.diffuse_color=(1,0.2,0.2,0.5)
            
        #vlak maken    
        def vlak_maken(lx,ly,lz,rx,ry,rz,maat):    
            bpy.ops.mesh.primitive_plane_add(enter_editmode=False,
                                            size = maat,
                                             align='WORLD',
                                              location=(lx,ly,lz),
                                               scale=(1, 1, 1),
                                               rotation=(rx,ry,rz),
                                               )
            ob = bpy.context.object
            
            ob.name = 'Cut Plane'
            col = ob.users_collection
            
            # kijken of kleur bestaat anders maken
            try:
                bpy.context.object.data.materials.append(bpy.data.materials['kleur'])
            except:
                nieuwe_kleur()
                bpy.context.object.data.materials.append(bpy.data.materials['kleur'])
                
            
            # kijken of collectie bestaat anders maken 
            try:
                bpy.data.collections['Cut Planes']
            except:
                nieuwe_collectie_maken()
            # als de snijvlak collectie al actief was is het object al in de goede collectie gemaakt
            # het kan dan niet nog een keer aan de collectie gelinked worden
            try:    
                bpy.data.collections['Cut Planes'].objects.link(ob)
            except:
                pass
            if col[0].name != 'Cut Planes':
                col[0].objects.unlink(ob)
                
            col
        ######     PROGRAMMA    #######
        #if bpy.context.mode == 'OBJECT':
        hoek_x = 0
        hoek_y = 0
        hoek_z = 0

        if vlakrichting == 'XZ':
            hoek_x = math.radians(90)            
        if vlakrichting == 'YZ':
            hoek_y = math.radians(90) 
            
        vlak_maken(0,0,0,hoek_x,hoek_y,hoek_z,maat)           

        return{'FINISHED'}
    
##############################################
####     CREATE THE CUt GROUP         ########
############################################## 

    
class MESH_OT_samenvoegen(bpy.types.Operator):
    """Chose objects in object mode to make cross section from and finaly the cutting face"""
    bl_idname = "mesh.samenvoegen"  
    bl_label = "samenvoegen"
    # Ik denk dat undo hier niet hoeft omdat het gecopieerde object maar een keer gemaakt hoeft te worden
    # Waarschijlijk is het nu sneller
    #bl_options = {'REGISTER', 'UNDO'} 
    
    
    def execute(self,context):
        def samenvoegen():
            niet_actief = []
            snijvlak = 0
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            if bpy.context.mode == 'OBJECT':
                snijvlak = bpy.context.object.name
                for ob in bpy.context.selected_objects:
                    
                    if ob != bpy.context.object:
                        niet_actief.append(ob)
                # Het actieve object niet selecteren        
                bpy.context.object.select_set(False)
                #Het eerste object in de lijst actief maken
                bpy.context.view_layer.objects.active = niet_actief[0]
                # de objecten uit de lijst dupliceren en samenvoegen
                bpy.ops.object.duplicate()
                bpy.ops.object.join()
                
                #########      NIEUW    ###############
                # De modifiers van het gecopieerde object worden ge'applied'
                if len(bpy.context.object.modifiers)>0:
                    mod = []
                    for m in bpy.context.object.modifiers:
                        mod.append(m.name)
                      
                    for m in mod:
                        bpy.ops.object.modifier_apply(modifier=m)
                
                # Naam voor samenvoeging      
                bpy.context.object.name = 'Bewerken'
                bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

                #naam = bpy.context.object.name
                # In edit mode alle vlakken selecteren, anders gaat de bisect niet door alle vlakken
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action='SELECT')
                
            return(snijvlak)
        
        ###### PROGRAMMA  ######
            
        s = samenvoegen()
        
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects[s].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects[s]
        
        return{'FINISHED'}
    
    
##############################################
####     DO THE CUT OPPERATION        ########
############################################## 


class MESH_OT_doorsnijden(bpy.types.Operator):
    """Make the cross cut"""
    bl_idname = "mesh.doorsnijden"  # komy in de afdeling mesh en heet planken
    bl_label = "Make Cross Section"
    bl_options = {'REGISTER', 'UNDO'}  # nodig voor menu in beeld te krijgen
    # hier staan waardes die je mee kan geven
    

    
    
    
    afstand: bpy.props.FloatProperty(
        name = "Distance from Start",
        default =0,
        unit='LENGTH',
        options={'SKIP_SAVE'}
    )
    
    projectie_afstand: bpy.props.FloatProperty(
        name = "Distance projection",
        default =0.1,
        unit='LENGTH',
        
    )
    def draw(self,context):
        layout = self.layout
        layout.label(text = 'Cutting plane')
        layout = self.layout
        
        layout.prop(self,'afstand')


        row = layout.row()
        layout.label(text = 'Cross Section Displacement')
        layout.prop(self,'projectie_afstand',text ='Dist. cent. object')  
           
    @classmethod
    def poll(cls, context):        
        return bpy.context.mode == 'OBJECT'    
    
    def execute(self,context):
        try:
            bpy.ops.mesh.samenvoegen()
        except:
            self.report({"ERROR"}, "Select an object and a cut plane!")            
            return{'CANCELLED'}
        
        afstand = self.afstand
        projectie_afstand = self.projectie_afstand
        # test of de collectie 'Doorsnedes' bestaat,andes maken
        def col_maken():
            bestaat = False
            for col in bpy.data.collections:
                if col.name == 'Cross sections':
                    bestaat = True
                    break
            if not bestaat:
                col = bpy.data.collections.new('Cross sections')
                bpy.context.scene.collection.children.link(col)            
            
        col_maken()
        ob = bpy.context.object
        # deze hoek is de hoek van het snijvlak, strakt de doorsnede tegengesteld terugdraaien
        hoek_voor_terugdraaien = ob.rotation_euler.copy()
        
 
        # De coordinaten van het snijvlak, het object wat doorgesneden moet worden het 'bewerken'        
        co = ob.location
        co_basis = ob.location.copy()
        m = ob.matrix_world
        m2 = Matrix.to_3x3(m)
        # De normaal van het snijvlak, dat is ook de normaal die ingevuld moet worden in de bisect
        normaal = m2 @ v2 
        # afstand is de verplaatsing in de richting van de normaal
        ob.location = ob.location + afstand*normaal       
        # Het snijvlak doet verder niets meer, nu verder met het te snijden opject
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['Bewerken'].select_set(True)
        bpy.context.view_layer.objects.active = bpy.data.objects['Bewerken']

        #loc = bpy.context.object.location
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='SELECT')
        geslaagd = False
        # als het vlak niet het object snijd lijd dat tot een error, daarom try
        try:
            bpy.ops.mesh.bisect(plane_co=co, plane_no=normaal, flip=False)
            
            geslaagd = True 
        except:
            pass 
        # de bisect is gemaakt, maar het 'bewerken, object is nog actief. Daarom dat object deselecteren, het is nog wel actief
        try:
            bpy.ops.mesh.duplicate()  
            bpy.ops.mesh.separate(type='SELECTED')
            bpy.ops.object.editmode_toggle()
            bpy.context.object.select_set(False)
            
           # De normaal van het snijvlak, hij wordt genormalizeerd, maar dat is eigenlijk niet nodig als het snijvlak een schaal 1 heeft
           # de matrix waar de normaal van is afgeleid, is de eenheidsmatrix als de schaal 1 is 
            norm_2 = normaal.copy()
            norm_2.normalize()
            #loc=co_basis+3*norm_2
            

            
            
            # Hier wordt de doorsnede het actieve object, nodig voor verplaatsen  
            # het 'bewerken' object wordt het reverentie punt voor de verplaatsing
            # de normaal wordt vermenevuldigd hier met 5 voor de afstand vanaf een centrum van 'bewerken'
            # de afstand van het snijvlak naar de het verplaatspunt wordt berekend
            #                                 
            bpy.context.view_layer.objects.active = bpy.context.selected_objects[0]
            coord_bewerken = bpy.data.objects['Bewerken'].location
            verplaatspunt = bpy.data.objects['Bewerken'].location + norm_2*projectie_afstand
            afstand = mathutils.geometry.distance_point_to_plane(verplaatspunt,co, norm_2)

            
            vactor = afstand
            x_verp = vactor*norm_2[0]
            y_verp = vactor*norm_2[1]
            z_verp = vactor*norm_2[2]
            bpy.ops.transform.translate(value=(x_verp,y_verp,z_verp), orient_type='GLOBAL', )

            
            bpy.context.object.name = 'Cross section'
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

            col_name = bpy.context.object.users_collection[0].name
            bpy.data.collections['Cross sections'].objects.link(bpy.context.object)
            bpy.data.collections[col_name].objects.unlink(bpy.context.object)

            
            # Het terugdraain van de doorsnede in het horizontale vlak
            '''
            bpy.ops.object.duplicate()
            hoek_voor_terugdraaien[0]=hoek_voor_terugdraaien[0]*-1
            hoek_voor_terugdraaien[1]=hoek_voor_terugdraaien[1]*-1
            hoek_voor_terugdraaien[2]=hoek_voor_terugdraaien[2]*-1
            bpy.context.object.rotation_euler = Euler((hoek_voor_terugdraaien),'ZYX')
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
            bpy.context.object.location[2] = 0
            ''' 

        except:
            pass
        bpy.data.objects.remove(bpy.data.objects['Bewerken'])
                                                  
        return{'FINISHED'}
    
##############################################
####     TO THE XY PLANE              ########
############################################## 
    
class MESH_OT_doorsnede_plat(bpy.types.Operator):
    """Put the cross section to the xy plROane to export with dxf exporter"""
    bl_idname = "mesh.doorsnede_platleggen"  
    bl_label = "Cross Section to XY Plane"
    bl_options = {'REGISTER', 'UNDO'}
    
    
    rotatie: bpy.props.FloatProperty(
        name = "Turn",
        default =0,
        precision = 0,
        step = 500,
        unit = 'ROTATION',
        options={'SKIP_SAVE'}
    )
    bool_flip:bpy.props.BoolProperty(
        name="flip",
        default=False
    ) 
    @classmethod
    def poll(cls, context):        
        return len(context.selected_objects) >0 and bpy.context.mode == 'OBJECT'
      
    def execute(self,context):
        rotatie = self.rotatie
        flip = self.bool_flip
        bpy.ops.object.duplicate()
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_all(action='DESELECT')
        richt_vector =Vector((0,0,1))
        ob = bpy.context.object
        me = ob.data
        bm = bmesh.from_edit_mesh(me)

        punten = []
        teller = 0
        for p in bm.verts:
            if teller < 3:
                p.select = True
                teller +=1
            else: break
        bpy.ops.mesh.duplicate()
        bpy.ops.mesh.edge_face_add()
        bm.faces.ensure_lookup_table()
        normaal = bm.faces[0].normal
        if flip:
            normaal=normaal*-1
        print('Normaal = ',normaal[2])
        #hoek = normaal.angle(richt_vector)
        hoek = normaal.rotation_difference(richt_vector)
        print('Hoek is;',hoek)
        mat_rot = hoek.to_matrix().to_3x3()

        for v in bm.verts:    
            v.co = mat_rot @  (v.co)
            
        bpy.ops.mesh.delete(type='FACE')
        bpy.ops.object.editmode_toggle()
        bpy.context.object.location[2]=0
        #rotatie = rotatie*((2*(math.pi))/360)
        bpy.ops.transform.rotate(value=rotatie, orient_axis='Z',
         orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)),
          orient_matrix_type='GLOBAL')
 
        return{'FINISHED'}      


############################################
####### DXF Exporter  ######################
############################################

class EXP_dxf_file_los(bpy.types.Operator):
    '''Export the active object to DXF file, DXF import export addon needs to be installed
    DXF exporter is shipped with blender'''
    bl_idname = 'export_scene.export_dxf_file_los'
    bl_label = 'DXF export'
    
    @classmethod
    def poll(cls, context):        
        return len(context.selected_objects) == 1  
    
    def execute(self,context):
        
        path = bpy.path.abspath(context.scene.dxf_export_los) # path halen uit de propperty
        #path = str(context.scene.dxf_export)
        
        obj = bpy.context.object
        if len(bpy.context.selected_objects) >1:
            print('Teveel elementen')
            self.report({"ERROR"}, "More then one object selected!!!!")
            return {'CANCELLED'}
        
        bpy.ops.object.duplicate() # nieuw ofject om te verschalen
        obj = bpy.context.object
        
        # alles wordt geexporteerd in blender schalen, daarom keer 100 om in centimeters te krijven
        schaal = context.scene.scale_factor_3
        mat_sca_x = mathutils.Matrix.Scale(schaal, 4,(1,0,0))
        mat_sca_y = mathutils.Matrix.Scale(schaal, 4,(0,1,0))
        
        
        obj.matrix_world = obj.matrix_world @ mat_sca_x @ mat_sca_y

        
        
        
        
        #obj.matrix_world = obj.matrix_world @ mat_sca_z         
        
        #  exporteren
        bpy.ops.export.dxf(filepath=path,
                    projectionThrough='NO', 
                    onlySelected=True, apply_modifiers=True,
                     mesh_as='LINEs',
                     entitylayer_from='obj.data.name',
                      entitycolor_from='default_COLOR',
                       entityltype_from='CONTINUOUS',
                        layerName_from='LAYERNAME_DEF',
                         verbose=False)                            
                                 

        # het gedupliceerde object weghalen eventueel uitzetten om de geexporteerde form te zien      
        bpy.ops.object.delete(use_global=False)
        #bpy.data.objects.remove(export_vlak)
        return {'FINISHED'} 
    
    
                            
def register():
    
        # propperties om eigenschappen in op te slaan                           
    bpy.types.Scene.dxf_export_los = bpy.props.StringProperty(
        name='DXF Folder',
        subtype='FILE_PATH',
        )
    bpy.types.Scene.scale_factor_3 = bpy.props.FloatProperty(
        name = 'Scale',
        default = 100,
        )
    bpy.utils.register_class(VIEW_PT_Snijvlakken)
    bpy.utils.register_class(MESH_OT_snijvlakken_maken_editm)
    bpy.utils.register_class(MESH_OT_snijvlakken_maken)
    bpy.utils.register_class(MESH_OT_samenvoegen)
    bpy.utils.register_class(MESH_OT_doorsnijden)
    bpy.utils.register_class(MESH_OT_doorsnede_plat)
    bpy.utils.register_class(EXP_dxf_file_los)
    
def unregister():
    bpy.utils.unregister_class(VIEW_PT_Snijvlakken)
    bpy.utils.register_class(MESH_OT_snijvlakken_maken_editm)
    bpy.utils.register_class(MESH_OT_snijvlakken_maken)
    bpy.utils.register_class(MESH_OT_samenvoegen)
    bpy.utils.unregister_class(MESH_OT_doorsnijden)
    bpy.utils.register_class(MESH_OT_doorsnede_plat)
    bpy.utils.register_class(EXP_dxf_file_los)
    del bpy.types.Scene.dxf_export_los
    del bpy.types.Scene.scale_factor_3
    
    
if __name__ == '__main__':
    register()