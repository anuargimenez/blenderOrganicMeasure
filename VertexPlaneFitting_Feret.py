bl_info = {
    "name": "CrossSectionFeret",
    "author": "Anuar R. Gimenez",
    "version": (0, 0, 1),
    "blender": (3, 2, 0),
    "location": "View3D > Sidebar > Edit",
    "description": "Extract cross sections from selected objects and measure Feret diameter",
    "warning": "",
    "category": "Object",
}

import bpy
import numpy as np
from mathutils import Matrix

def planeFit(points):
    ctr = points.mean(axis=0)
    x = points - ctr

    # Use least squares to solve the normal vector
    _, _, v = np.linalg.svd(x)
    normal = v[2]

    return ctr, normal

def orthopoints(normal):
    m = np.argmax(normal)
    x = np.ones(3, dtype=np.float32)
    x[m] = 0
    x /= np.linalg.norm(x)
    x = np.cross(normal, x)
    y = np.cross(normal, x)
    return x, y

def intersect_plane_segment(plane_loc, plane_rot, v1, v2):
    mat = (Matrix.Translation(plane_loc) @ plane_rot.to_matrix().to_4x4()).inverted()
    v1 = mat @ v1
    v2 = mat @ v2

    if v1.z * v2.z <= 0:
        t = -v1.z / (v2.z - v1.z)
        intersection = v1.lerp(v2, t)
        intersection = mat.inverted() @ intersection
        return intersection

    return None

class CrossSectionPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Edit"
    bl_options = {'DEFAULT_CLOSED'}    
    bl_label = "Vertex Plane and Feret"
    #bl_context_mode = 'EDIT'
    #bl_context = "mesh_edit"

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'MESH'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("object.create_plane", text="Create Plane")

        row = layout.row()
        row.operator("object.extract_cross_section", text="Extract Cross Section")

        row = layout.row()
        row.operator("object.measure_feret_diameter", text="Measure Feret Diameter")


class OBJECT_OT_CreatePlane(bpy.types.Operator):
    bl_idname = "object.create_plane"
    bl_label = "Create Plane"

    size: bpy.props.FloatProperty(
        name="Size",
        description="Size of the plane",
        default=1,
        min=0,
        soft_max=10
    )
    thickness: bpy.props.FloatProperty(
        name="Thickness",
        description="Thickness of the plane",
        default=0.0,
        min=0,
        soft_max=0.01
    )
    separate: bpy.props.BoolProperty(
        name="Separate",
        description="Generate the plane as a separate object",
        default=False
    )

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        ob = context.active_object
        me = ob.data
        count = len(me.vertices)
        if count > 0:  # degenerate mesh, but better safe than sorry
            shape = (count, 3)
            verts = np.empty(count*3, dtype=np.float32)
            selected = np.empty(count, dtype=np.bool)
            me.vertices.foreach_get('co', verts)
            me.vertices.foreach_get('select', selected)
            verts.shape = shape
            if np.count_nonzero(selected) >= 3 :
                ctr, normal = planeFit(verts[selected])
                dx, dy = orthopoints(normal)
                bpy.ops.mesh.primitive_plane_add(location = ob.location)
                me = context.active_object.data
                for vi,co in zip(me.polygons[0].vertices, [ctr+dx*self.size, ctr+dy*self.size, ctr-dx*self.size, ctr-dy*self.size]):
                    me.vertices[vi].co = co
                context.view_layer.objects.active = ob

                # Apply thickness to the plane
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value": (0, 0, self.thickness)})
                bpy.ops.object.mode_set(mode='OBJECT')

        else:
            self.report({'WARNING'}, "Need at least 3 selected vertices to fit a plane through")
        bpy.ops.object.editmode_toggle()
        return {'FINISHED'}


class OBJECT_OT_MeasureFeretDiameter(bpy.types.Operator):
    bl_idname = "object.measure_feret_diameter"
    bl_label = "Measure Feret Diameter"

    def execute(self, context):
        active_obj = bpy.context.object

        if active_obj is None or active_obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object.")
            return {'CANCELLED'}

        vertices = np.array([v.co for v in active_obj.data.vertices])
        max_distance = 0.0

        for i in range(len(vertices)):
            v1 = vertices[i]
            for j in range(i + 1, len(vertices)):
                v2 = vertices[j]
                distance = 1000*np.linalg.norm(v1 - v2)
                if distance > max_distance:
                    max_distance = distance

        self.report({'INFO'}, "Feret Diameter: {:.2f} mm".format(max_distance))
        return {'FINISHED'}


classes = (
    CrossSectionPanel,
    OBJECT_OT_CreatePlane,
    OBJECT_OT_MeasureFeretDiameter,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
