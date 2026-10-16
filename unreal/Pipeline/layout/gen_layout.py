#!/usr/bin/env python3
"""Generate layout.json for the UE5 rebuild of the XRLibraries Campus.
Every number is transcribed from parts/*.js (three.js campus source); derived values
(wax bays, shelf slots, UE conversions) are computed here exactly as the JS computes them.
Run: python3 gen_layout.py  -> writes layout.json next to this script and validates it."""
import json, math, os

PI = math.pi
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ coordinate conversion
# three.js campus: metres, +Y up, camera yaw 0 looks toward -Z ("north" on the minimap), +X east.
# UE: centimetres, +Z up, +X forward, left-handed. Chosen map (matches Blender->FBX->UE and the
# UE glTF importer's Y/Z swap, see layout.md): UE(X,Y,Z) = (100*x, 100*z, 100*y).
def ue_pos(x, y, z):
    return [round(100.0 * x, 2), round(100.0 * z, 2), round(100.0 * y, 2)]

def ue_yaw(yaw_three):
    """three.js yaw (rad, yaw 0 = -Z) -> UE yaw (deg, 0 = +X, + toward +Y)."""
    d = (-90.0 - math.degrees(yaw_three)) % 360.0
    if d > 180.0:
        d -= 360.0
    return round(d, 3)

def ue_pitch(pitch_three):
    return round(math.degrees(pitch_three), 3)

def view(x, z, yaw, pitch, note=None, src=None):
    v = {"three": {"x": x, "z": z, "eye_y": 1.62, "yaw_rad": round(yaw, 6), "pitch_rad": round(pitch, 6)},
         "ue": {"location_cm": ue_pos(x, 1.62, z), "rotation_deg": {"pitch": ue_pitch(pitch), "yaw": ue_yaw(yaw), "roll": 0.0}}}
    if note: v["note"] = note
    if src: v["src"] = src
    return v

def hexcol(h):
    return "#%06x" % h

def look_yaw(fx, fz, tx, tz):   # outdoor.js:12
    return math.atan2(-(tx - fx), -(tz - fz))

# ------------------------------------------------------------------ constants (world.js:10, nav.js:4)
H_ROOM, EYE, H_HALL, H_LIB, H_SCHOOL, H_WAX = 4.4, 1.62, 3.4, 7.6, 3.6, 5.2
M_WALL = 0.45

def room(id, name, kicker, x0, x1, z0, z1, ceil, floor_y=0.0, src="parts/nav.js:6-20", **kw):
    r = {"id": id, "display_name": name, "kicker": kicker,
         "bounds_m": {"x0": x0, "x1": x1, "z0": z0, "z1": z1},
         "size_m": {"w_x": round(x1 - x0, 3), "d_z": round(z1 - z0, 3)},
         "floor_y_m": floor_y, "ceiling_h_m": ceil,
         "ue_bounds_cm": {"min": ue_pos(x0, floor_y, z0), "max": ue_pos(x1, floor_y + (ceil or 0), z1)},
         "src": src}
    r.update(kw)
    return r

rooms = [
    room("lobby", "XRLibraries Campus", "Lobby", -6, 6, -6, 0, H_ROOM, wing="museum",
         walls="museum plaster, GALLERIES[0].wall #d6cbb6; back wall z=0 carries the title panel (3.6x1.9 at y 2.05) and plaque; directory/partners panels on the z=-6 partition faces",
         floor="museum floor tiles (canvasFloor) 12x42 plane centred (0,0,-21) shared by lobby+galleries",
         interior_wall_thickness_m=0.0, partition_thickness_m=0.3, exterior_shell_offset_m=0.2),
    room("g1", "Headsets in Libraries", "Gallery 1 of 3 · 2016 to 2022", -6, 6, -18, -6, H_ROOM, wing="museum", wall_color="#1f3d3a", partition_thickness_m=0.3, exterior_shell_offset_m=0.2),
    room("g2", "Learning That Works", "Gallery 2 of 3 · Careers and resources", -6, 6, -30, -18, H_ROOM, wing="museum", wall_color="#22304f", partition_thickness_m=0.3, exterior_shell_offset_m=0.2),
    room("g3", "Stories Worth Saving", "Gallery 3 of 3 · Equity, worlds, nature", -6, 6, -42, -30, H_ROOM, wing="museum", wall_color="#3e1f2c", partition_thickness_m=0.3, exterior_shell_offset_m=0.2,
         notes="end wall at z=-42 has the 3.2x3.1 opening to the Wax Hall; bench at (0,-35.4) 1.8x0.46; the Wax teaser panel 1.5x1.5 at (3.7,1.86,-41.994)"),
    room("wax", "The Wax Hall", "Museum · Living History", -8.5, 8.5, -81, -42.3, H_WAX, wing="wax", src="parts/nav.js:10, parts/waxhall.js:7",
         walls="deep plum plaster #3b1e28 with a brass rail at y 4.0; ceiling #1a1416",
         floor="dark parquet (tinted #d8c8bc) with a 3.2 m wide red runner (#5e1a22) down the centre from z -41.1 to -77.1",
         stage_height_m=0.2, stage_depth_m=3.9, bay_len_m=5.6, bay_gap_m=0.3, first_bay_z=-45.3, rope_line_from_wall_m=4.45,
         notes="12 stages: 5 bays per side (L/R) + 2 end bays on the north wall; dividers 3.9x3.95x0.3 between side bays; two benches at z -56.95 and -68.75; intro wall 6.2x3.6x0.3 at z=-44.6 (museum wing)"),
    room("hallL", "To the Library", "Hall", -12, -6, -4.6, -1.4, H_HALL, wing="lib", wall_color="#2a4438", notes="posters on both long walls at x=-9; ceiling lamp disc r0.22 at (-9,3.39,-3)"),
    room("lib", "The Reading Room", "Library", -32, -12, -13, 7, H_LIB, wing="lib", src="parts/world.js:411 (full room -32..-12 x -13..7); nav sub-rect parts/nav.js:12 is -23..-12.45 x -12.55..6.55",
         walls="baked Blender room (assets/lib/library.blend -> lib/lib.glb): green plaster walls, walnut trim, mezzanine slabs 0.95 m deep at y 3.6 (0.22 thick), coffered ceiling every 2.5 m, laylight x -30..-14 z -3.9..-2.1 at the 7.6 m ceiling",
         floor="wood floor with three 4.8x2.4 rugs at x -27, -21.8, -16.6 (z -4.2..-1.8)",
         nav_subrects={"lib": [-23, -12.45, -12.55, 6.55], "libAisle": [-32, -23, -5.2, -0.8]},
         notes="nav treats the stacks (x -32..-23 outside z -5.2..-0.8) as solid; the UE room is the full 20x20 m shell. Library exterior shell is 0.2 m out (x -32.2..-11.8, z -13.2..7.2), Blender jamb reveal thickness 0.45 m"),
    room("libAisle", "The Stacks", "Library", -32, -23, -5.2, -0.8, H_LIB, wing="lib", src="parts/nav.js:13", notes="nav-only region: the aisle between the north and south stacks, ends at the arched west window"),
    room("hallR", "To the Workshop School", "Hall", 6, 12, -4.6, -1.4, H_HALL, wing="school", wall_color="#2f4f63", notes="posters on both long walls at x=9; ceiling lamp disc r0.22 at (9,3.39,-3)"),
    room("school", "Main Hall", "Workshop School", 12, 34, -4.75, -1.25, H_SCHOOL, wing="school", src="parts/world.js:491 (built -4.75..-1.25); nav rect parts/nav.js:15 is -4.33..-1.67 because 0.42 m lockers line both walls",
         walls="painted school wall (canvasSchoolWall); lino floor #e6dfcc/#b9d0cc; acoustic tile ceiling",
         lockers=[{"wall": "south z=-4.75", "x_runs": [[12.8, 17.8], [21.4, 27.8], [30.2, 33.6]]}, {"wall": "north z=-1.25", "x_runs": [[12.8, 17.6], [20.2, 27.6], [30.2, 33.6]]}, {"size": "1.8 high x 0.42 deep, base 0.08"}],
         notes="cork boards 2.4x1.0 at x=24 y=2.5 on both walls; EXIT/RECESS YARD sign 2.3x0.506 on east wall at y 3.1; light boxes 1.2x0.5 at x=14,18,22,26,30 y=3.58 z=-3; blade signs stick out over each door at y 3.0"),
    room("studio", "3D Art Studio", "Room 101", 14, 24, -13, -4.75, H_SCHOOL, wing="school", src="parts/world.js:518",
         walls="plaster #e9e4da; wood floor (canvasFloor [118,90,62]); tile ceiling",
         notes="chalkboard 5.6x2.0 at (19,1.85,-12.935) on south wall; clock at (19,3.2,-12.98); teacher desk 1.6x0.8 at (16.4,0.37,-11.6); paint poster 2.4x1.6 on west wall at (14.032,1.85,-9.2); easel at (15.6,0,-6.4) ry 0.75; sculpture turntable r0.9 at (21.6,0.04,-10.2); 'window view' backdrop plane 9x4.2 at x 24.8 y 1.9 z -8.9 behind the 3 east windows; paint volume STUDIO_BOX 14.15..23.85 x 0.04..3.5 x -12.85..-4.9 (parts/paint.js:18)"),
    room("lab", "Science Lab", "Room 102", 25.6, 34, -13, -4.75, H_SCHOOL, wing="school", src="parts/rooms.js:4,186",
         walls="two-tone band wall #eef1ef over #c8d4d8 with a #2f8f9d band at 1.0 m; lino #e3e6e3/#d2d9d7; tile ceiling",
         furniture=["east bench 0.8x5.7 at (33.6,0.43,-9.05) epoxy top 0.88 (sieve station SV at 33.58,0.9,-9.0)",
                    "south bench 6.4x0.8 at (29.2,0.43,-12.6) with fume hood 1.6 wide at (26.95,0.9,-12.58), sink at (29.0,0.905,-12.58), reagent shelf 5.0 at (30.2,1.72,-12.86); titration station TT at (31.0,0.9,-12.6)",
                    "island 1.9x1.3 at (30.2,0.43,-9.05) with 4 stools and a microscope",
                    "glassware cabinet 0.5x2.1x1.4 at (25.85,1.05,-11.3); safety shower at (25.92,1.25,-5.55); periodic table 1.7x1.077 on west wall at (25.627,1.75,-7.35)",
                    "pendulum station PD at (25.9,2.62,-9.2) on the west wall, photogate display at (25.672,1.0,-9.58)",
                    "labs board 3.0x1.28 at (31.6,1.72,-4.805) and goggles sign on the north wall; coats at x 26.3..27.2, fire extinguisher at (27.62,0.36,-4.89)"]),
    room("blueprint", "Blueprint Lab", "Room 103", 12.2, 24, -1.25, 7, H_SCHOOL, wing="school", src="parts/rooms.js:5,275",
         walls="band wall #e4eaef over #24425e with #f2c14e band at 0.9 m; wood floor [138,104,70]; tile ceiling; skylight 6.0x1.1 at (20.8,3.585,2.6)",
         furniture=["5 blueprint boards 2.9x1.8125 centre y 1.75: car (14.45,6.97) N wall, excavator (18.1,6.97) N, bridge (21.75,6.97) N, house (12.23,2.875) W wall, computer (23.96,2.875) E wall (parts/blueprints.js:4-11)",
                    "pegboard 3.5x1.09 at (14.7,1.85,-1.2) south wall; kit shelf 3.0 wide at (22.0,-1.01)",
                    "drafting tables at (13.5,0.5) ry 0.5 and (13.4,5.4) ry 2.4; 3D printer cart at (23.25,0,0.0)",
                    "model bench BENCH at (18.1,0.925,2.4) (parts/blueprints.js:115)"]),
    room("world", "World Builder Studio", "Room 104", 24, 34, -1.25, 7, H_SCHOOL, wing="school", src="parts/rooms.js:6,335",
         walls="dark band wall #3a4654 over #26303b with #5ee6c8 band at 0.9 m; carpet tiles; grey tile ceiling #8a9098; LED strips #5ee6c8 (north wall) and #c38bff (east/west) at y 3.48",
         furniture=["layer table DIO 2.6x1.7 at (29.0,0.79,2.9), model origin (29.0,0.87,2.9) ry pi (parts/worldroom.js:5)",
                    "desk 6.8x0.72 at (29.0,0.75,6.58) with 3 monitors (x 25.7,29,32.3); chairs at x 26.6,29,31.4 z 5.75",
                    "toolkit shelves 0.44x4.6 on the west wall at (24.24,·,3.0); bean bags at (33.2,-0.4) and (32.3,-0.6)",
                    "stats screen 2.08x1.17 on east wall at (33.925,1.75,2.1); frosted window z 4.9..6.3"]),
    room("yard", "The Playground", "Recess Yard", 34, 92, -34, 26, None, wing="play", src="parts/nav.js:20, parts/outdoor.js:5",
         outdoor=True, fence_z=-8.6,
         notes="nav NOGO rect x 34..94 z -36..-8.15 is the coaster's ground (parts/nav.js:23); the walkable yard is z -8.6..26. Ground: 640x640 grass plane centred (30,-0.012,-8); grass instancing rect x 27..101 z -40..32 (parts/nature.js:6)")
]

# ------------------------------------------------------------------ doors (openings) ------------------------------
# axis 'z' = opening in a wall that runs along X at z=at; axis 'x' = wall runs along Z at x=at.
def door(id, frm, to, axis, at, a, b, h, src, nav=None, notes=None):
    c = (a + b) / 2.0
    d = {"id": id, "from": frm, "to": to, "wall_axis": axis, "wall_at_m": at, "span_m": [a, b], "centre_m": c, "width_m": round(b - a, 3), "height_m": h,
         "ue_centre_cm": (ue_pos(c, 0, at) if axis == "z" else ue_pos(at, 0, c)), "src": src}
    if nav: d["nav"] = nav
    if notes: d["notes"] = notes
    return d

doors = [
    door("lobby-g1", "lobby", "g1", "z", -6, -1.6, 1.6, 3.1, "parts/world.js:179-190 (wallShape), parts/nav.js:42", {"w": 3.2, "band": 0.6}, "partition is two faces at z=-5.85/-6.15 (0.3 thick) with a wood frame 0.1x3.15 posts at x ±1.65 and a 3.4x0.1 lintel at y 3.15; door sign 3.1x0.53 at y 3.76"),
    door("g1-g2", "g1", "g2", "z", -18, -1.6, 1.6, 3.1, "parts/world.js:183-190, parts/nav.js:42", {"w": 3.2, "band": 0.6}, "same partition as lobby-g1"),
    door("g2-g3", "g2", "g3", "z", -30, -1.6, 1.6, 3.1, "parts/world.js:183-190, parts/nav.js:42", {"w": 3.2, "band": 0.6}, "same partition as lobby-g1"),
    door("g3-wax", "g3", "wax", "z", -42.15, -1.6, 1.6, 3.1, "parts/world.js:174-177 (end wall z=-42), parts/world.js:243-245 (frame at -42.15), parts/waxhall.js:273-282 (wax south wall z=-42.3), parts/nav.js:42", {"w": 3.2, "band": 0.75}, "double-sided: museum end wall at z=-42 and Wax Hall south wall at z=-42.3 both have the 3.2x3.1 opening; velvet curtains tied back at x ±1.85 on the wax side, valance 4.2x0.36 at y 3.3"),
    door("lobby-hallL", "lobby", "hallL", "x", -6, -4.2, -1.8, 3.1, "parts/world.js:356-360, parts/nav.js:43", {"w": 2.4, "band": 0.6}, "wood frame posts 0.38x3.15x0.1 at z -4.25/-1.75, lintel at y 3.15; wing sign 'The Library' 2.7x0.46 at y 3.62"),
    door("hallL-lib", "hallL", "lib", "x", -12, -4.6, -1.4, H_HALL, "parts/world.js:415 (library east wall), parts/nav.js:43", {"w": 3.2, "band": 1.0}, "the hall has no wall at x=-12: it opens straight into the library door; exterior shell door at x=-11.8 is z -4.8..-1.2 h 3.65 (parts/outdoor.js:299)"),
    door("lib-libAisle", "lib", "libAisle", "x", -23, -5.2, -0.8, None, "parts/nav.js:43", {"w": 4.4, "band": 0.6}, "nav-only link, there is no wall here (aisle between the stacks)"),
    door("lobby-hallR", "lobby", "hallR", "x", 6, -4.2, -1.8, 3.1, "parts/world.js:356-360, parts/nav.js:44", {"w": 2.4, "band": 0.6}, "mirror of lobby-hallL; wing sign 'Workshop School'"),
    door("hallR-school", "hallR", "school", "x", 12, -4.6, -1.4, H_HALL, "parts/world.js:497 (school west wall), parts/nav.js:44", {"w": 3.2, "band": 0.6}, "exterior shell door at x=6.2 (museum east wall, where the hall attaches) is z -4.8..-1.2 h 3.65 (parts/outdoor.js:286)"),
    door("school-101", "school", "studio", "z", -4.75, 18.1, 19.9, 2.6, "parts/world.js:495,522; parts/rooms.js:7,143", {"w": 1.8, "band": 1.0}, "door trim 2.0 wide x 2.65 high x 0.24 deep; room sign 1.5x0.643 at y 3.04; blade sign at x 20.2"),
    door("school-102", "school", "lab", "z", -4.75, 28.1, 29.9, 2.6, "parts/world.js:495; parts/rooms.js:191", {"w": 1.8, "band": 1.0}, "blade sign at x 27.75"),
    door("school-103", "school", "blueprint", "z", -1.25, 18.1, 19.9, 2.6, "parts/world.js:496; parts/rooms.js:280", {"w": 1.8, "band": 1.0}, "blade sign at x 17.75"),
    door("school-104", "school", "world", "z", -1.25, 28.1, 29.9, 2.6, "parts/world.js:496; parts/rooms.js:340", {"w": 1.8, "band": 1.0}, "blade sign at x 27.75"),
    door("school-yard", "school", "yard", "x", 34, -4.2, -1.8, 2.7, "parts/world.js:498 (interior), parts/outdoor.js:313,322-327 (exterior), parts/nav.js:49", {"w": 2.4, "band": 1.0}, "steel frame at x 34.11, threshold plate, canopy 1.5x3.6 at (34.95,3.0,-3), 'WORKSHOP SCHOOL' letters 5.4x0.66 at (34.22,3.68,-3); the campus has NO exterior front door: the lobby back wall at z=0 is solid")
]

# ------------------------------------------------------------------ windows --------------------------------------
def window(id, roomid, axis, at, a, b, y0, y1, src, arch=False, kind="glazed", notes=None):
    c = (a + b) / 2.0
    w = {"id": id, "room": roomid, "wall_axis": axis, "wall_at_m": at, "span_m": [a, b], "y_m": [y0, y1], "width_m": round(b - a, 3), "height_m": round(y1 - y0, 3), "arch": arch, "kind": kind,
         "ue_centre_cm": (ue_pos(c, (y0 + y1) / 2, at) if axis == "z" else ue_pos(at, (y0 + y1) / 2, c)), "src": src}
    if arch: w["arch_apex_y_m"] = round(y1 + (b - a) / 2, 3)
    if notes: w["notes"] = notes
    return w

windows = [
    window("lib-west-arch", "lib", "x", -32, -5.2, -0.8, 1.0, 4.6, "parts/world.js:418, bl/library.py:230, docs/realism-plan.md:11", arch=True, notes="semicircular arch radius 2.2 (apex 6.8); walnut frame, mullions at z -4.1/-3/-1.9, transoms at y 2.4/3.6; glass at x -32.2; low western sun rakes through it in the bake"),
    window("lib-laylight", "lib", "ceiling", 7.6, -30, -14, -3.9, -2.1, "bl/library.py:206-219", kind="laylight", notes="span is x -30..-14, 'y' field here holds z -3.9..-2.1; glowing panel 0.3 above the ceiling with a 0.3x0.2 frame and mullions every 2 m"),
    window("studio-e1", "studio", "x", 24, -11.9, -10.5, 1.0, 2.7, "parts/world.js:525-531", notes="white frame, mullion; looks at a painted 'window view' backdrop plane at x 24.8"),
    window("studio-e2", "studio", "x", 24, -9.6, -8.2, 1.0, 2.7, "parts/world.js:525"),
    window("studio-e3", "studio", "x", 24, -7.3, -5.9, 1.0, 2.7, "parts/world.js:525"),
    window("lab-e1", "lab", "x", 34, -12.1, -10.7, 1.12, 2.62, "parts/rooms.js:194-196", kind="frosted"),
    window("lab-e2", "lab", "x", 34, -9.6, -8.2, 1.12, 2.62, "parts/rooms.js:194-196", kind="frosted"),
    window("lab-e3", "lab", "x", 34, -7.1, -5.7, 1.12, 2.62, "parts/rooms.js:194-196", kind="frosted"),
    window("world-e1", "world", "x", 34, 4.9, 6.3, 1.12, 2.62, "parts/rooms.js:343-344", kind="frosted"),
    window("blueprint-skylight", "blueprint", "ceiling", 3.6, 17.8, 23.8, 2.05, 3.15, "parts/rooms.js:285-288", kind="skylight", notes="6.0x1.1 frosted panel at (20.8, 3.585, 2.6) with wood edge beams; 'y' field holds z extent"),
    window("school-facade-e1", "school(exterior)", "x", 34.215, -12.15, -10.65, 1.05, 2.65, "parts/outdoor.js:331-337", kind="exterior glass pane", notes="centre z -11.4, 1.5x1.6, dark reflective glass; behind it the lab's frosted window"),
    window("school-facade-e2", "school(exterior)", "x", 34.215, -9.65, -8.15, 1.05, 2.65, "parts/outdoor.js:331", kind="exterior glass pane"),
    window("school-facade-e3", "school(exterior)", "x", 34.215, -7.15, -5.65, 1.05, 2.65, "parts/outdoor.js:331", kind="exterior glass pane"),
    window("school-facade-e4", "school(exterior)", "x", 34.215, 4.85, 6.35, 1.05, 2.65, "parts/outdoor.js:331", kind="exterior glass pane"),
    window("school-facade-mural", "school(exterior)", "x", 34.215, -0.25, 3.95, 0.505, 3.395, "parts/outdoor.js:338-339", kind="mural (opaque painting 4.2x2.89)"),
    window("museum-roof-glass", "museum(exterior)", "roof", 4.7, -1.3, 1.3, -39, -3, "parts/outdoor.js:289-290", kind="exterior roof glazing strip 2.6x36 (no interior opening: museum ceiling is solid at 4.4)"),
    window("lib-roof-lantern", "lib(exterior)", "roof", 8.7, -27.1, -16.9, -4.5, -1.5, "parts/outdoor.js:303-305", kind="exterior roof lantern 10.2x0.9 glass band at y 8.7 (sits above the laylight)"),
    window("school-roof-glass-1", "school(exterior)", "roof", 4.36, 17.5, 24.5, -9.5, -8.3, "parts/outdoor.js:319", kind="exterior roof glazing 7x1.2"),
    window("school-roof-glass-2", "school(exterior)", "roof", 4.36, 17.5, 24.5, 2.0, 3.2, "parts/outdoor.js:319", kind="exterior roof glazing 7x1.2 (over the Room 103 skylight)")
]

# ------------------------------------------------------------------ lights ---------------------------------------
# three.js PointLight(color, intensity, distance, decay) as authored; gfxLights() (parts/gfx.js:129-142) then
# multiplies intensity by 10, sets decay 1, distance = max(distance, 22) and lowers any lamp that is closer
# than 1.1 m to the ceiling above it. 'runtime' = values after gfxLights (confirmed by unreal/Pipeline/out/campus/lights.json).
def plight(id, wingid, x, y, z, col, i, dist, decay, src, y_rt=None, i_rt=None, notes=None):
    L = {"id": id, "type": "point", "wing": wingid, "pos_m": [x, y, z], "color_srgb": hexcol(col), "authored": {"intensity": i, "distance_m": dist, "decay": decay},
         "runtime": {"pos_m": [x, (y if y_rt is None else y_rt), z], "intensity": (i * 10 if i_rt is None else i_rt), "distance_m": max(dist, 22), "decay": 1},
         "ue_location_cm": ue_pos(x, (y if y_rt is None else y_rt), z), "src": src}
    if notes: L["notes"] = notes
    return L

lights = [
    {"id": "sun", "type": "directional", "color_srgb": "#fff0dc", "color_authored_srgb": "#fff0d8", "intensity_three": 3.1,
     "dir_to_sun_three": [40, 62, 30], "dir_to_sun_unit": [0.5022, 0.7784, 0.3766], "elevation_deg": 51.1, "azimuth_from_north_cw_deg": 126.9,
     "ue_rotation_deg": {"pitch": -51.1, "yaw": -143.1, "roll": 0.0},
     "shadow": {"map": 2048, "ortho_half_extent_m": 34, "near": 1, "far": 320, "bias": -0.0004, "normal_bias": 0.035, "follows_camera": True},
     "src": "parts/outdoor.js:4 (SUN_DIR), parts/world.js:258, parts/gfx.js:12,146-154,188-205",
     "notes": "three.js DirectionalLight; intensity = SUN_I(3.1) * LIGHTS.k where k fades 1 outdoors -> 0 indoors (parts/rides.js:236-244), so the sun and its shadow map are OFF inside the buildings and the hemisphere/env light cross-fade HEMI_IN 0.32->HEMI_OUT 0.55, ENV_IN 0.8->ENV_OUT 0.95. UE DirectionalLight forward vector must be -(dir_to_sun) mapped to UE = (-0.502, -0.377, -0.778). The Blender library bake used a DIFFERENT, low western sun (see lights 'lib-blender-sun'); pick one global sun in UE."},
    {"id": "hemisphere", "type": "hemisphere/ambient", "sky_srgb": "#d9e8ff", "ground_srgb": "#6a5a46", "intensity_indoor": 0.32, "intensity_outdoor_const": 0.55, "authored": {"sky": "#fff1dc", "ground": "#2a2118", "intensity": 0.62, "ambient": "#ffffff 0.1 -> 0 at runtime"},
     "src": "parts/world.js:236, parts/gfx.js:12,144-145", "notes": "UE: replace with Sky Light + Lumen GI; no direct equivalent"},
    {"id": "env-maps", "type": "image-based", "outdoor": "PMREM of the procedural sky (clouds 0.6) + green ground disc, intensity ENV_OUT 0.95", "indoor": "PMREM of a warm 24x9x24 box with 5 warm ceiling panels (1.0,0.86,0.68 x5.5) and 2 cool windows (0.75,0.85,1.0 x2.4), intensity ENV_IN 0.8",
     "src": "parts/gfx.js:94-119", "notes": "switches to 'out' when roomAt is yard or school hall x>31.5"},
    plight("museum-lobby", "museum", 0, 3.9, -3, 0xffe2b9, 0.75, 19, 1.6, "parts/world.js:169", y_rt=3.3, notes="lowered 0.6 m by the ceiling rule (ceiling 4.4)"),
    plight("museum-g1", "museum", 0, 3.9, -12, 0xffe2b9, 0.9, 19, 1.6, "parts/world.js:169", y_rt=3.3),
    plight("museum-g2", "museum", 0, 3.9, -24, 0xffe2b9, 0.9, 19, 1.6, "parts/world.js:169", y_rt=3.3),
    plight("museum-g3", "museum", 0, 3.9, -36, 0xffe2b9, 0.9, 19, 1.6, "parts/world.js:169", y_rt=3.3),
    plight("wax-entry", "museum", 0, 3.8, -43.4, 0xffdcb2, 0.7, 14, 1.6, "parts/waxhall.js:385", notes="over the intro wall, just inside the Wax Hall door"),
]
for zc in [-43.8, -48.1, -54.0, -59.9, -65.8, -71.7, -76.4]:
    lights.append(plight("wax-%g" % -zc, "wax" if zc < -44.4 else "museum", 0, 4.6, zc, 0xffdcb2, 0.95, 19, 1.6, "parts/waxhall.js:348-351", y_rt=(3.815 if zc == -76.4 else 4.09),
                         notes="ceiling disc r0.2 glow at y 5.19 above each; last one lowered to 3.815 by the end-bay header beam"))
lights += [
    plight("lib-main", "lib", -17.5, 6.4, -3, 0xffe2b9, 0.95, 26, 1.3, "parts/world.js:419", notes="the only three.js light in the baked library; the bake's own lights are listed as lib-blender-*"),
    plight("school-hall", "school", 23, 3.3, -3, 0xfff5e8, 0.85, 26, 1.4, "parts/world.js:512", y_rt=2.5),
    plight("studio-101", "school", 19, 3.2, -9, 0xfff3e2, 0.8, 18, 1.4, "parts/world.js:560", y_rt=2.5),
    plight("lab-102", "school", 29.8, 3.2, -8.9, 0xf2f7ff, 0.85, 18, 1.4, "parts/rooms.js:199", y_rt=2.5),
    plight("blueprint-103", "school", 18.1, 3.2, 2.9, 0xfff4e6, 0.85, 18, 1.4, "parts/rooms.js:291", y_rt=2.485),
    plight("world-104", "school", 29.0, 3.2, 0.9, 0xeef3ff, 0.8, 18, 1.4, "parts/rooms.js:352", y_rt=2.5),
]
# Blender bake lights for the Reading Room (unreal/Pipeline/out/reading_room/lights.json, from assets/lib/library.blend)
for name, p, w, c in [("L", [-18.3, 1.35, -7.0], 18, [1.0, 0.75, 0.45]), ("L.001", [-18.7, 1.09, -10.8], 18, [1.0, 0.75, 0.45]), ("L.002", [-17.5, 1.09, -10.8], 18, [1.0, 0.75, 0.45]),
                     ("L.003", [-16.3, 1.09, -10.8], 18, [1.0, 0.75, 0.45]), ("L.004", [-18.7, 1.09, 4.6], 18, [1.0, 0.75, 0.45]), ("L.005", [-17.5, 1.09, 4.6], 18, [1.0, 0.75, 0.45]),
                     ("L.006", [-16.3, 1.09, 4.6], 18, [1.0, 0.75, 0.45]), ("L.007", [-27.5, 5.45, -9.5], 200, [1.0, 0.88, 0.72]), ("L.008", [-16.5, 5.45, -9.5], 200, [1.0, 0.88, 0.72]),
                     ("L.009", [-27.5, 5.45, 3.5], 200, [1.0, 0.88, 0.72]), ("L.010", [-16.5, 5.45, 3.5], 200, [1.0, 0.88, 0.72])]:
    lights.append({"id": "lib-blender-" + name, "type": "point", "wing": "lib", "pos_m": p, "color_linear": c, "blender_watts": w, "radius_m": 0.08, "ue_location_cm": ue_pos(*p),
                   "src": "unreal/Pipeline/out/reading_room/lights.json (bl/library.py)", "notes": "desk/reading lamps (18 W) and 4 ceiling pendants (200 W); Blender point-light watts, not candela"})
lights.append({"id": "lib-blender-sun", "type": "directional", "wing": "lib", "dir_of_light_three": [0.9056, -0.3256, -0.2717], "blender_strength": 26.0, "color_linear": [1.0, 0.93, 0.84],
               "elevation_deg": 19.0, "notes": "low sun from the WEST through the arched window (bl/library.py:507-511); conflicts with SUN_DIR (sun in the south-east at 51 deg). If UE keeps one global sun, add a local light through the library window instead.",
               "src": "unreal/Pipeline/out/reading_room/lights.json, bl/library.py:511"})

emissive_fixtures = [
    {"id": "museum-ceiling-discs", "shape": "disc r0.12", "color": "#ffe9c8", "positions_m": [[dx, H_ROOM - 0.01, zc + dz] for zc, ln in [(-3, 6), (-12, 12), (-24, 12), (-36, 12)] for dz in [-ln / 4, ln / 4] for dx in [-2.4, 2.4]], "src": "parts/world.js:170"},
    {"id": "hall-lamps", "shape": "disc r0.22", "color": "#ffe9c8", "positions_m": [[-9, H_HALL - 0.01, -3], [9, H_HALL - 0.01, -3]], "src": "parts/world.js:374"},
    {"id": "school-hall-troffers", "shape": "box 1.2x0.03x0.5", "color": "#fffaf0", "positions_m": [[x, H_SCHOOL - 0.02, -3] for x in [14, 18, 22, 26, 30]], "src": "parts/world.js:509-510"},
    {"id": "studio-troffers", "shape": "box 1.2x0.03x0.5", "color": "#fffaf0", "positions_m": [[19, H_SCHOOL - 0.02, -10.8], [19, H_SCHOOL - 0.02, -7.0]], "src": "parts/world.js:559"},
    {"id": "lab-panels", "shape": "box 1.2x0.03x0.6", "color": "#f6fbff", "positions_m": [[x, H_SCHOOL - 0.02, z] for x in [28.2, 31.6] for z in [-6.9, -10.8]], "src": "parts/rooms.js:197-198"},
    {"id": "blueprint-panels", "shape": "box 1.2x0.03x0.5", "color": "#fffaf0", "positions_m": [[14.6, 3.58, 0.8], [14.6, 3.58, 4.8], [18.1, 3.58, 0.6], [18.1, 3.58, 5.0]], "src": "parts/rooms.js:289-290"},
    {"id": "world-panels", "shape": "box 1.2x0.03x0.5", "color": "#f3f6ff", "positions_m": [[26.4, 3.58, 1.0], [31.6, 3.58, 1.0], [26.4, 3.58, 4.8], [31.6, 3.58, 4.8]], "src": "parts/rooms.js:350-351"},
    {"id": "world-led-strips", "shape": "0.025 square strips at y 3.48 along the north wall (z 6.97, #5ee6c8) and the east/west walls (x 24.04 / 33.97, #c38bff)", "src": "parts/rooms.js:346-349"},
    {"id": "wax-ceiling-discs", "shape": "disc r0.2", "color": "#fff1d6", "positions_m": [[0, H_WAX - 0.01, zc] for zc in [-43.8, -48.1, -54.0, -59.9, -65.8, -71.7, -76.4]], "src": "parts/waxhall.js:350"},
    {"id": "wax-stage-spot-cans", "shape": "2 per stage at local x ±0.28*L, y 3.48, z -3.48 on the header beam, lens r0.075 aimed down-forward", "color": "#fff1d6", "src": "parts/waxhall.js:321-325"},
    {"id": "yard-lamp-globes", "shape": "sphere r0.19 on 3.3 m posts", "color": "#fff3d6", "positions_m": [[x, 3.42, z] for x, z in [[38.6, -5.1], [44.2, -0.9], [47.6, -8.0], [56.4, -8.0], [60.4, 3.9], [46.6, 5.0], [65.6, 9.2], [50.3, 9.6]]], "src": "parts/outdoor.js:397-401"},
    {"id": "school-facade-lamps", "shape": "box 0.08x0.2x0.12", "color": "#fff1c8", "positions_m": [[34.35, 2.3, -4.75], [34.35, 2.3, -1.25]], "src": "parts/outdoor.js:340-341"},
    {"id": "drop-tower-strips", "shape": "4 vertical 0.06 strips (h-3 tall) at r 0.76 around the tower, plus red beacon r0.22 at the top (y 35.8)", "colors": ["#ffd27a", "#ff5a4a"], "src": "parts/outdoor.js:619-625"},
    {"id": "dive-dome-portholes", "shape": "7 discs r0.34 on the dome at elevation 0.5 rad", "color": "#9fe9ff", "src": "parts/outdoor.js:656-661"},
    {"id": "blueprint-board-lamps", "shape": "brass picture lights with a 1.5x0.014 glow bar over each of the 5 boards and each museum frame", "color": "#fff3d6 / #ffe9c8", "src": "parts/blueprints.js:21-23, parts/world.js:223-225"}
]

# ------------------------------------------------------------------ wax hall layout (computed like parts/waxhall.js:11-23)
WH = {"x0": -8.5, "x1": 8.5, "z0": -81, "z1": -42.3, "h": 5.2, "stage": 0.2, "depth": 3.9, "bay": 5.6, "gap": 0.3, "first": -45.3, "rope": 4.45, "door": -42.15}
scenes = [("wax-2016", 1, "2016", "The First Headsets", "library", "carpet"), ("wax-2017a", 2, "2017", "VR Goes Statewide", "calmap", "boards"), ("wax-2017b", 3, "2017", "Story Time in 3D", "storyroom", "rug"),
          ("wax-2018a", 4, "2018", "Nevada Opens Its Stations", "reopening", "tile"), ("wax-2019a", 5, "By 2019", "VR on the Road", "shelter", "gym"), ("wax-2019b", 6, "2019", "VR in the World’s Catalog", "catalog", "office"),
          ("wax-2019c", 7, "2019", "XR Marin and the XR Stars", "farm", "grass"), ("wax-2020", 8, "2020", "Project SANDI", "careers", "concrete"), ("wax-2022a", 9, "2022", "360° Stories in Washington", "forest360", "meeting"),
          ("wax-2022b", 10, "2022", "Lost Stories", "shipyard", "dock"), ("wax-2024", 11, "2024", "Children Draw War, Not Flowers", "vrgallery", "grid"), ("wax-2025", 12, "2025", "Pollinators at the Fair", "fair", "fair")]
bays = []
for k in range(5):
    zc = WH["first"] - WH["bay"] / 2 - k * (WH["bay"] + WH["gap"])
    bays.append({"side": "L", "x": WH["x0"] + WH["depth"], "z": round(zc, 3), "ry": PI / 2, "len": WH["bay"]})
    bays.append({"side": "R", "x": WH["x1"] - WH["depth"], "z": round(zc, 3), "ry": -PI / 2, "len": WH["bay"]})
ez = WH["z0"] + WH["depth"]
bays.append({"side": "E", "x": -4.15, "z": ez, "ry": 0.0, "len": 8.0})
bays.append({"side": "E", "x": 4.15, "z": ez, "ry": 0.0, "len": 8.0})
wax_stages = []
for i, (sid, n, year, title, backdrop, floor) in enumerate(scenes):
    b = bays[i]
    fx, fz = math.sin(b["ry"]), math.cos(b["ry"])    # local +z (toward the walkway) in world
    if b["side"] == "E":
        vx, vz = b["x"] * 0.62, b["z"] + 3.4
        vyaw = math.atan2(vx - b["x"], vz - (b["z"] - 1.6))
    else:
        vx, vz = b["x"] + fx * 4.6, b["z"] + fz * 4.6
        vyaw = math.atan2(fx, fz)
    if b["side"] == "L":
        fp = {"x0": -8.5, "x1": b["x"], "z0": b["z"] - b["len"] / 2, "z1": b["z"] + b["len"] / 2}
    elif b["side"] == "R":
        fp = {"x0": b["x"], "x1": 8.5, "z0": b["z"] - b["len"] / 2, "z1": b["z"] + b["len"] / 2}
    else:
        fp = {"x0": b["x"] - b["len"] / 2, "x1": b["x"] + b["len"] / 2, "z0": -81, "z1": b["z"]}
    wax_stages.append({"id": sid, "n": n, "year": year, "title": title, "backdrop": backdrop, "floor": floor, "bay": b,
                       "origin_m": [b["x"], WH["stage"], b["z"]], "origin_note": "stage group origin = centre of the front (rope) edge at platform-top height; local +z faces the walkway, platform extends 3.9 m behind",
                       "footprint_m": fp, "ue_origin_cm": ue_pos(b["x"], WH["stage"], b["z"]), "ue_yaw_deg": ue_yaw(b["ry"] + PI), "ue_yaw_note": "direction the stage faces (its local +z, toward the walkway): L bays face east (UE yaw 0), R bays face west (180), end bays face south toward the door (+90)",
                       "view": view(round(vx, 3), round(vz, 3), vyaw, -0.04, src="parts/waxhall.js:438-443 (waxView)"),
                       "medallion_m": ([b["x"], 0.007, b["z"] + 1.55] if b["side"] == "E" else [math.copysign(3.3, b["x"]), 0.007, b["z"] + (1.9 if b["side"] == "L" else -1.9)]),
                       "src": "parts/waxscenes.js (scene meta), parts/waxhall.js:7-23,286-334"})
dividers = []
for sx in [-1, 1]:
    for k in range(6):
        zc = WH["first"] + 0.15 if k == 0 else WH["first"] - k * (WH["bay"] + WH["gap"]) + WH["gap"] / 2
        dividers.append({"centre_m": [sx * (WH["x1"] - WH["depth"] / 2), 1.975, round(zc, 3)], "size_m": [WH["depth"], 3.95, 0.3]})
dividers.append({"centre_m": [0, 1.975, WH["z0"] + WH["depth"] / 2], "size_m": [0.3, 3.95, WH["depth"] - 0.2], "notes": "between the two end stages"})

# ------------------------------------------------------------------ library stacks (parts/world.js:423-439, parts/data.js:133-141)
subjects = [("basics", "XR Basics", "N", 0), ("programs", "Library Programs", "N", 1), ("careers", "Careers", "N", 2), ("story", "Storytelling", "N", 3),
            ("equity", "Lost Stories", "S", 0), ("environment", "Environment", "S", 1), ("worlds", "Shared Worlds", "S", 2), ("tech", "Technology", "S", 3)]
stacks = []
for sid, name, side, slot in subjects:
    sx = -24.0 - 2.2 * slot
    north = side == "N"
    za, zb = (-12.4, -5.6) if north else (-0.4, 6.4)
    stacks.append({"subject": sid, "name": name, "side": side, "x": round(sx, 2), "z0": za, "z1": zb, "proxy_size_m": [0.62, 2.3, round(zb - za + 0.1, 2)],
                   "aisle_end_z": round(zb + 0.045 if north else za - 0.045, 3), "sign_y": 2.08,
                   "shelf_view": view(round(sx, 2), -2.6 if north else -3.4, 0.0 if north else PI, -0.12, src="parts/world.js:438")})

# ------------------------------------------------------------------ exterior & yard -------------------------------
def feat(id, name, x, z, y=0.0, src=None, **kw):
    f = {"id": id, "name": name, "pos_m": [x, y, z], "ue_location_cm": ue_pos(x, y, z)}
    if src: f["src"] = src
    f.update(kw)
    return f

coaster_pts = [[54, 0.8, -11.5], [57, 0.85, -11.5], [60, 1.6, -11.5], [63, 4.0, -11.5], [70, 10.0, -11.5], [76.5, 15.6, -11.5], [79.5, 18.0, -11.5],
               [82, 18.9, -11.6], [85.6, 18.8, -12.9], [87.9, 18.6, -15.8], [87.9, 18.3, -19.2], [85.6, 18.0, -22.1], [82, 17.6, -23.4],
               [79.2, 16.4, -23.5], [76.6, 12.4, -23.5], [74.2, 7.0, -23.5], [71.8, 2.6, -23.5], [69.2, 1.0, -23.5], [66.8, 0.9, -23.5]]
LC = {"x": 61.5, "y": 5.6, "r": 4.6}
for i in range(17):
    ph = i / 16 * 2 * PI
    coaster_pts.append([round(LC["x"] - LC["r"] * math.sin(ph), 4), round(LC["y"] - LC["r"] * math.cos(ph), 4), round(-23.5 - 3.0 * (i / 16), 4)])
coaster_pts += [[57, 1.1, -26.7], [53.5, 3.0, -26.9], [50.5, 6.0, -27], [47.5, 6.6, -27], [44.6, 4.6, -27], [42, 2.2, -26.8],
                [39, 1.7, -26.6], [35.6, 1.6, -24.6], [33.6, 1.6, -21.2], [33.6, 1.6, -17.6], [35.4, 1.5, -14.3], [38.6, 1.2, -12.2],
                [42, 1.0, -11.55], [46, 0.85, -11.5], [50, 0.8, -11.5]]

exterior = {
    "building_shells": [
        {"id": "museum", "bounds_m": {"x0": -6.2, "x1": 6.2, "z0": -42.2, "z1": 0.2}, "height_m": 4.6, "material": "pale stone courses (canvasStone 2.4 m tile), grey roof slab #5d6164 with a #d8cfbf cap", "roof_glass": "2.6x0.22x36 strip at y 4.7 (z -39..-3)", "src": "parts/outdoor.js:286-290", "notes": "only the EAST wall (x 6.2) and the SOUTH/back wall (z 0.2) are modelled; west wall is hidden by the library/hall"},
        {"id": "wax-annex", "bounds_m": {"x0": -8.7, "x1": 8.7, "z0": -81.3, "z1": -42.0}, "height_m": 5.4, "material": "stone, 12.4x0.8 parapet at (0,5.0,-42)", "letters": "'LIVING HISTORY' 7.2x0.88 on the east face at (8.72,4.45,-61.5)", "src": "parts/outdoor.js:292-297"},
        {"id": "library", "bounds_m": {"x0": -32.2, "x1": -11.8, "z0": -13.2, "z1": 7.2}, "height_m": 7.9, "material": "warm stone (tint #e2d3b6)", "roof_lantern": "10x1.5x3.2 stone at (-22,8.65,-3), 10.2x0.9x3.0 glass at (-22,8.7,-3), cap 10.4x0.16x3.6 at y 9.45", "door": "east wall z -4.8..-1.2 h 3.65", "src": "parts/outdoor.js:299-305"},
        {"id": "halls", "bounds_m": [{"x0": -11.8, "x1": -6.2, "z0": -4.8, "z1": -1.2}, {"x0": 6.2, "x1": 11.8, "z0": -4.8, "z1": -1.2}], "height_m": 3.65, "material": "stone", "src": "parts/outdoor.js:307-311"},
        {"id": "school", "bounds_m": {"x0": 11.8, "x1": 34.2, "z0": -13.2, "z1": 7.2}, "height_m": 4.3, "material": "red brick (canvasBrick 1.35x1.2 tile), roof cap #cdc4b4", "rooftop_units": [[18, 4.8, 2.5, "1.8x1.0x1.3"], [28, 4.75, -9.5, "1.4x0.9x1.1"], [22, 4.55, 4.5, "0.5 cube"]],
         "east_facade": "back door frame x 34.11, canopy 1.5x3.6 navy at (34.95,3.0,-3), 'WORKSHOP SCHOOL' letters, 4 windows, mural 4.2x2.89 at z 1.85, 2 wall lamps, concrete plinths 0.42 high along the base", "src": "parts/outdoor.js:313-341"}
    ],
    "ground": {"grass_plane": "640x640 m, 120x120 segments, centred (30,-0.012,-8), vertex-colour mottling", "horizon": "two vertex-coloured rings around (30,-8): hills r176 (base -2, 13-25 m tall, #6f8a78->#8aa596) and a tree line r142 (#22392a->#35553c, 8-segment rounded crowns)", "fog": {"color_linear_rgb": [0.5952, 0.7469, 0.88], "near_m": 70, "far_m": 245}, "src": "parts/outdoor.js:247-278, parts/gfx.js:89-90"},
    "yard": {
        "bounds_m": {"x0": 34, "x1": 92, "z0": -34, "z1": 26}, "fence_z": -8.6,
        "paths": [{"kind": "paver strip", "from": [34.05, -3], "to": [46.2, -3], "width": 2.4}, {"kind": "paver plaza circle", "centre": [52, -1.5], "r": 6.5, "ring": "0.35 edge #8d877c"},
                  {"kind": "paver strip", "from": [52, -7.4], "to": [52, -9.4], "width": 3.2}, {"kind": "paver strip", "from": [57.6, 1.3], "to": [73.4, 10.3], "width": 2.2},
                  {"kind": "paver strip", "from": [52.8, 4.6], "to": [54, 11.1], "width": 2.2}, {"kind": "paver strip", "from": [41.2, -1.9], "to": [41.2, 10.2], "width": 2.0},
                  {"kind": "wood chips", "rect": [35.5, 46.1, 10, 24], "edge": "0.14 timber"}, {"kind": "hopscotch decal", "centre": [41.2, -3], "size": [3.6, 0.98]}],
        "fences": [{"from": [34.3, -8.6], "to": [91.9, -8.6], "gap_x": [49.6, 54.4]}, {"from": [91.9, -33.9], "to": [91.9, 25.9]}, {"from": [34.1, 25.9], "to": [91.9, 25.9]}, {"from": [32.2, -33.9], "to": [91.9, -33.9]},
                   {"from": [32.2, -33.9], "to": [32.2, -13.2]}, {"from": [34.1, 7.2], "to": [34.1, 25.9]}, {"ring": "r 4.6 around the Sky Drop (78,13), 18 segments, gap toward (73.4,10.3)"}],
        "fence_spec": "posts 0.08x1.2 every ~2.4 m, two rails 0.05x0.04 at y 0.55 and 1.08, green #2e4b3c",
        "src": "parts/outdoor.js:356-453"
    },
    "features": [
        feat("entrance-arch", "Recess Yard arch", 36.2, -3, 3.05, "parts/outdoor.js:375-380", posts="r0.1 x 3.3 at z -4.6 and -1.4", sign="3.36x0.67 two-sided at y 3.05"),
        feat("signpost", "Plaza signpost (3 arrow boards)", 52, -1.5, 1.55, "parts/outdoor.js:383-394", boards=[{"ride": "coaster", "points_to": [51.6, -9], "y": 2.75}, {"ride": "drop", "points_to": [78, 13], "y": 2.3}, {"ride": "dive", "points_to": [54, 16], "y": 1.85}]),
        feat("coaster", "Comet Coaster", 50.9, -11.0, 0.0, "parts/outdoor.js:456-610", track_points_m=coaster_pts, track="closed CatmullRom (centripetal), rails 0.055 r at ±0.5, spine 0.15 r at -0.42; stats height 19 m, loop ~10 m, length ~170 m, top ~62 km/h",
             station={"ground": "16x5.2 at (50.9,-11.0)", "platform": "13.6x0.85x1.85 at (50.9,0.425,-9.8)", "canopy": "14.4x0.2x4.8 at y 3.9 on 6 posts (x 44.4/50.9/57.4, z -13.1/-8.95)", "sign": "6.4x0.88 at (50.9,3.35,-8.86)", "booth": [49.1, -7.7], "entry_gate": "posts at x 49.4/54.6 on the fence line, lintel at y 2.5"},
             train="3 cars 1.32 wide x 1.7 long, 2.15 m apart", exit_view=view(52, -6.4, 0.0, 0.14, src="parts/rides.js:5")),
        feat("drop-tower", "Sky Drop", 78, 13, 0.0, "parts/outdoor.js:6,613-647", base_y=1.0, top_y=31, tower_h=34, base="concrete r2.3-2.5 x0.5", column="r0.72-0.82", head="navy cone 1.25 at y 34.75, band with 'SKY DROP' at 34.8, beacon at 35.8",
             ring="8 seats on r1.95 around a navy hub, rides from y 1.0 to 31", booth=[70.3, 11.1], fence_r=4.6, exit_view=view(68.6, 6.6, look_yaw(68.6, 6.6, 78, 13), 0.34, src="parts/rides.js:6")),
        feat("dive-dome", "Ocean Dive", 54, 16, 0.3, "parts/outdoor.js:7,650-678", dome_r=4.2, entrance="teal block 2.7x2.75x1.9 at (54,1.375,11.5)", portal="1.8x2.0 at (54,1.1,10.54) facing -z, yellow frame", sign="2.4x0.48 at y 2.48", booth=[51.4, 9.65],
             exit_view=view(54, 8.4, 0.0, 0.02, src="parts/rides.js:7"), notes="the underwater world (WING.dive, parts/dive.js) is a separate hidden level loaded for the ride; not part of the walkable campus"),
        feat("swings", "Swing set", 40.8, 13.6, 0.0, "parts/outdoor.js:449,681-693", frame="A-frame legs at x ±2.5 (z ±0.475, 0.33 rad splay) 2.85 tall red, top bar r0.06 x 5.2 at y 2.7", seats="3 at dx -1.4/0/1.4, chains 2.1 m, seat 0.52x0.05x0.22 at y 0.56"),
        feat("slide", "Slide", 41.4, 20.4, 0.0, "parts/outdoor.js:450,694-707", platform="1.3x1.3 at y 1.6 on 4 posts (±0.6), ladder on the -x side at x 40.45", chute="3.3 long teal, from (42.02,1.62) sloping -0.52 rad toward +x, landing pad at x 45.0"),
        feat("merry-go-round", "Spinner", 66.5, 20, 0.0, "parts/outdoor.js:451,708-717", deck="r1.6 x0.12 yellow at y 0.32, 6 wedge panels, 6 handle posts at r1.25, rim r1.25 at y 1.18, hub r0.12"),
        feat("soccer-goal", "Soccer goal (youth 5x2)", 86.6, -2.0, 0.0, "parts/phys.js:21, parts/soccer.js:7,100-135", width=5.0, height=2.0, depth=1.6, faces="-x (shots travel toward +x)", penalty_spot=[79.1, -2.0], pitch_markings="70.5..91.5 x -8.4..6.2, goal area 2.2 deep, box 10 deep, arc r4.6", keeper_home=[86.15, -2.0], scoreboard=[87.6, -7.3],
             view=view(77.75, -2.0, -PI / 2, -0.1, src="parts/engine.js:102")),
        feat("block-tower", "Foam block tower", 64.5, 1.5, 0.0, "parts/phys.js:19", block_size=0.45, rows=["PLAY", "LAB", "XR", "★"], view=view(61.2, 1.5, -PI / 2, -0.08, src="parts/engine.js:103")),
        feat("balls", "Physics balls", 0, 0, 0, "parts/phys.js:11-15", items=[{"id": "soccer", "r": 0.11, "at": [79.1, -2.0]}, {"id": "kick-red", "r": 0.125, "at": [61.6, 2.6]}, {"id": "kick-blue", "r": 0.125, "at": [72.4, -6.5]}, {"id": "beach", "r": 0.3, "at": [58.6, 8.0]}]),
        feat("yard-benches", "Park benches (4)", 52, -1.5, 0.0, "parts/outdoor.js:403-410", positions_m=[[round(52 + math.cos(a) * 7.7, 3), round(-1.5 + math.sin(a) * 7.7, 3)] for a in [-0.8, -2.35, 0.2, 2.6]], notes="on the r7.7 circle around the plaza centre, backs facing outward"),
        feat("picnic-tables", "Picnic tables (3)", 0, 0, 0, "parts/outdoor.js:411-418", positions_m=[[63.2, -4.6, 0.3], [67.4, -1.6, -0.2], [48.8, 12.2, 1.4]], notes="[x, z, ry]"),
        feat("yard-lamps", "Lamp posts (8)", 0, 0, 0, "parts/outdoor.js:397-401", positions_m=[[38.6, -5.1], [44.2, -0.9], [47.6, -8.0], [56.4, -8.0], [60.4, 3.9], [46.6, 5.0], [65.6, 9.2], [50.3, 9.6]], height=3.3),
        feat("yard-trees", "Yard trees (18)", 0, 0, 0, "parts/outdoor.js:421-424", positions_m=[[47.5, 23.4], [54, 23.8], [60.5, 23.2], [71.5, 23.6], [78, 23.2], [84.5, 23.6], [90, 22], [89.8, 15.5], [90, 8], [89.6, 1.2], [89.8, -5.5], [61.2, 11.6], [69.5, 1.6], [84.8, 7.4], [46.7, 8.4], [69.5, 16.6], [58.2, -6.2], [37.2, 6.4]], scale="1.05..1.4 (seeded rnd(2024))", obstacle_r=0.75),
        feat("campus-trees", "Trees around the buildings (18)", 0, 0, 0, "parts/outdoor.js:351", positions_m=[[9, -9.5], [9, -17], [9, -25], [9, -34], [9, 3.8], [16, 11.5], [24.5, 12.5], [-2, 6], [-20, 12], [-28.5, 11], [27, -18.5], [19, -17.5], [14, -25], [-8.5, -20], [-9, -31], [-22, -18], [-30, -21], [2, 9.5]], scale="1.1..1.6"),
        feat("far-trees", "Far trees (140, random)", 0, 0, 0, "parts/outdoor.js:344-350", rule="seeded rnd(99): x in [-84,144], z in [-96,72], rejecting the campus box -40<x<97 and -50<z<31; scale 1.3..2.7", tree_model="trunk h=(1.7..2.5)*s, two leaf crowns (ellipsoids 1.55x1.25 and 1.08x1.0 scaled) #4a7a36/#5d8f43 (parts/outdoor.js:223-234, parts/nature.js)")
    ]
}

# ------------------------------------------------------------------ staff, stations, tokens ----------------------
staff = [
    {"id": "margaret", "name": "Margaret", "role": "Museum guide", "pos_m": [0.68, 0, -4.0], "faces_m": [0, -0.7], "rooms": ["lobby", "g1", "g2", "g3", "wax"], "avatar": "Rocketbox bf02", "lectern": "0.4x0.98x0.3 oak at local (0.58,0,0.08)", "view": view(-0.2, -2.0, -0.41, 0.0), "src": "parts/people.js:5-8"},
    {"id": "rosa", "name": "Rosa", "role": "Reference librarian", "pos_m": [-17.2, 0, -7.75], "faces_m": [-13, -3], "rooms": ["hallL", "lib", "libAisle"], "avatar": "Rocketbox fa14", "view": view(-17.2, -5.0, 0.0, 0.0), "src": "parts/people.js:9-12"},
    {"id": "hale", "name": "Mr. Hale", "role": "Workshop teacher", "pos_m": [17.4, 0, -10.6], "faces_m": [19, -4.75], "rooms": ["hallR", "school", "studio", "lab", "blueprint", "world"], "avatar": "Rocketbox ma05", "view": view(18.7, -7.6, 0.42, 0.0), "src": "parts/people.js:13-16"},
    {"id": "rae", "name": "Coach Rae", "role": "Recess coach", "pos_m": [46.4, 0, 0.4], "faces_m": [38, -3], "rooms": ["yard"], "avatar": "Rocketbox sf02", "view": view(44.3, -0.45, look_yaw(44.3, -0.45, 46.4, 0.4), 0.0), "src": "parts/people.js:17-20"},
    {"id": "keeper", "name": "Goalkeeper", "role": "soccer NPC", "pos_m": [86.15, 0, -2.0], "src": "parts/socplay.js:9-11"}
]
for s in staff:
    s["ue_location_cm"] = ue_pos(*s["pos_m"])
    if "faces_m" in s:
        yaw = math.atan2(s["faces_m"][0] - s["pos_m"][0], s["faces_m"][1] - s["pos_m"][2])   # people.js:25 (root.rotation.y, model faces +z local)
        s["three_rotation_y_rad"] = round(yaw, 4)
        s["ue_yaw_deg"] = ue_yaw(yaw + PI)   # model's +z is its front; camera forward is -z, so add pi for the 'look' yaw convention
        s["ue_yaw_note"] = "root.rotation.y = atan2(dx, dz) makes the model's local +z face the target; ue_yaw_deg is the facing direction in UE"

stations = [
    {"id": "sieve", "room": "lab", "anchor_m": [33.58, 0.9, -9.0], "view": view(32.1, -9.0, -PI / 2, -0.28, src="parts/lab.js:334"), "src": "parts/lab.js:41"},
    {"id": "titration", "room": "lab", "anchor_m": [31.0, 0.9, -12.6], "view": view(30.95, -11.3, 0.0, -0.14, src="parts/lab.js:577"), "src": "parts/lab.js:435"},
    {"id": "pendulum", "room": "lab", "anchor_m": [25.9, 2.62, -9.2], "view": view(28.25, -9.2, PI / 2, 0.1, src="parts/lab.js:702"), "src": "parts/lab.js:631"},
    {"id": "bench", "room": "blueprint", "anchor_m": [18.1, 0.925, 2.4], "view": view(18.1, 1.1, PI, -0.32, src="parts/blueprints.js:366"), "src": "parts/blueprints.js:115"},
    {"id": "diorama", "room": "world", "anchor_m": [29.0, 0.87, 2.9], "view": view(29.0, 1.05, PI, -0.3, src="parts/worldroom.js:135"), "src": "parts/worldroom.js:5"},
    {"id": "easel", "room": "studio", "anchor_m": [15.6, 0, -6.4], "view": view(19, -6.4, 0.0, 0.06, note="PAINT_SPOT", src="parts/paint.js:17"), "src": "parts/world.js:545"}
]
for s in stations:
    s["ue_location_cm"] = ue_pos(*s["anchor_m"])

tokens = [{"id": i, "place": p, "at_m": a, "ue_location_cm": ue_pos(*a)} for i, p, a in [
    ("t-museum", "Museum", [-5.35, 0.36, -41.35]), ("t-library", "Library", [-31.64, 1.2, -4.95]), ("t-school", "Workshop School", [33.0, 2.1, -4.52]), ("t-studio", "Room 101", [21.6, 1.0, -12.86]),
    ("t-lab", "Room 102", [25.86, 2.32, -11.3]), ("t-blueprint", "Room 103", [23.25, 1.58, 0.0]), ("t-world", "Room 104", [24.26, 2.42, 5.2]), ("t-yard", "Recess Yard", [55.4, 0.4, 21.6])]]
tokens += [{"id": "t-coaster", "place": "Comet Coaster", "on_ride": "coaster", "at": "P[iLoopTop] + 1.15*N (inside the loop)"}, {"id": "t-drop", "place": "Sky Drop", "on_ride": "drop"}, {"id": "t-dive", "place": "Ocean Dive", "on_ride": "dive"}]

# ------------------------------------------------------------------ museum exhibits (parts/data.js:36-105, parts/world.js:127-137,208-229)
items = [("ca-200", 1, "L", -9, None, [1.5, 1.05]), ("mission", 1, "R", -9, None, [1.5, 1.05]), ("headset", 1, "P", -12, -2.6, None), ("nv-2017", 1, "L", -15, None, [1.5, 1.05]), ("cil-talks", 1, "R", -15, None, [1.0, 1.32]),
         ("sandi", 2, "L", -21, None, [1.5, 1.05]), ("nv-1100", 2, "R", -21, None, [1.5, 1.05]), ("dialysis", 2, "L", -27, None, [1.15, 1.15]), ("playbooks", 2, "P", -24, -2.6, None), ("showcase", 2, "R", -27, None, [1.15, 1.15]),
         ("way-out", 3, "L", -33, None, [1.5, 1.05]), ("charleston", 3, "R", -33, None, [1.0, 1.32]), ("seeking", 3, "L", -39, None, [1.5, 1.05]), ("ukraine", 3, "R", -39, None, [1.15, 1.15]), ("pollinators", 3, "E", -42, -3.6, [1.7, 1.7])]
exhibits = []
for iid, g, wall, z, x, size in items:
    if wall == "L":
        pos, ry, vw = [-5.995, 1.74, z], PI / 2, view(-6 + 4.0, z, PI / 2, -0.14, note="d = clamp(fitDist,2.75,5.6); 4.0 shown")
    elif wall == "R":
        pos, ry, vw = [5.995, 1.74, z], -PI / 2, view(6 - 4.0, z, -PI / 2, -0.14, note="d = clamp(fitDist,2.75,5.6); 4.0 shown")
    elif wall == "E":
        pos, ry, vw = [x, 1.9, -41.995], 0.0, view(x, -42 + 5.0, 0.0, -0.08, note="d = clamp(fitDist,3.5,8); 5.0 shown")
    else:
        pos, ry, vw = [x, 1.28, z], (PI / 2 if x < 0 else -PI / 2), view(x + (2.5 if x < 0 else -2.5), z, PI / 2 if x < 0 else -PI / 2, -0.3, note="pedestal 0.62x1.0 + glass case; d = clamp(fitDist,2.0,3.2)")
    exhibits.append({"id": iid, "gallery": g, "wall": wall, "pos_m": pos, "size_m": size, "three_rotation_y": round(ry, 4), "ue_location_cm": ue_pos(*pos), "ue_yaw_deg": ue_yaw(ry + PI), "ue_yaw_note": "direction the artwork/object faces (group local +z)", "view": vw})

# ------------------------------------------------------------------ tour stops (parts/ui.js:127-139, engine.js:69-104)
tour = [
    {"n": 1, "kind": "lobby", "title": "Welcome to the XRLibraries Campus", "view": view(0, -4.4, PI, 0.05, note="lobbyView(): z = -clamp(fitDist(1.95,1.1,3.4),3.4,5.4); looks back at the title panel on the z=0 wall", src="parts/world.js:137")},
    {"n": "2-16", "kind": "items", "title": "each museum exhibit in ITEMS order (15)", "views": "see exhibits[].view"},
    {"n": 17, "kind": "wax", "title": "The Wax Hall", "view": view(0, -43.2, 0.0, 0.06, note="just inside the door, facing the intro wall", src="parts/ui.js:131")},
    {"n": "18-29", "kind": "wax-items", "title": "each Wax Hall scene in order (12)", "views": "see wax_hall.stages[].view"},
    {"n": 30, "kind": "library", "title": "The Reading Room", "view": view(-13.4, -3, PI / 2, 0.08, src="parts/ui.js:133")},
    {"n": 31, "kind": "studio", "title": "Room 101: 3D Art Studio", "view": view(19, -6.4, 0.0, 0.06, note="PAINT_SPOT", src="parts/paint.js:17")},
    {"n": 32, "kind": "lab", "title": "Room 102: Science Lab", "view": view(29, -5.9, 0.0, -0.06, src="parts/ui.js:135")},
    {"n": 33, "kind": "blueprint", "title": "Room 103: Blueprint Lab", "view": view(18.1, 3.6, PI, 0.03, src="parts/ui.js:136")},
    {"n": 34, "kind": "world", "title": "Room 104: World Builder Studio", "view": view(29, 0.6, PI, -0.18, src="parts/ui.js:137")},
    {"n": 35, "kind": "yard", "title": "The Recess Yard", "view": view(38.6, -3, -PI / 2, 0.06, src="parts/ui.js:138")}
]
places = {pid: view(x, z, yaw, pitch, src="parts/engine.js:%d" % ln) for pid, x, z, yaw, pitch, ln in [
    ("lobby", 0, -2.2, 0.0, 0.02, 70), ("g1", 0, -8.4, 0.0, 0.02, 71), ("g2", 0, -20.4, 0.0, 0.02, 72), ("g3", 0, -32.4, 0.0, 0.02, 73), ("library", -13.4, -3, PI / 2, 0.08, 74),
    ("featured", -15, -0.9, PI, -0.32, 76), ("freedomBoard", -18.9, 1.0, PI / 2, -0.02, 77), ("window", -29.5, -3, PI / 2, 0.14, 78), ("school", 12.9, -3, -PI / 2, 0.02, 79), ("studio", 19, -5.7, 0.0, 0.02, 80),
    ("lab", 29, -5.9, 0.0, -0.06, 81), ("blueprints", 18.1, 3.6, PI, 0.03, 85), ("worldroom", 29, 0.6, PI, -0.18, 92), ("sculpture", 21.6, -7.6, 0.0, 0.12, 94), ("wax", 0, -46.4, 0.0, 0.02, 96),
    ("yard", 38.6, -3, -PI / 2, 0.06, 97), ("coaster", 50.2, -3.4, look_yaw(50.2, -3.4, 58, -14), 0.2, 98), ("drop", 64.5, 4.5, look_yaw(64.5, 4.5, 78, 13), 0.32, 99), ("dive", 54, 4.2, PI, 0.1, 100),
    ("field", 77.75, -2.0, -PI / 2, -0.1, 102), ("blocks", 61.2, 1.5, -PI / 2, -0.08, 103)]}

# ------------------------------------------------------------------ minimap (parts/ui.js:672-736)
minimap = {
    "bounds_m": {"x0": -33, "x1": 92, "z0": -82, "z1": 26}, "canvas_css_px": [180, 150], "dpr_cap": 2, "orientation": "x right (east), -z up (north); uniform scale fitted into the canvas with 4 px margin",
    "rooms": [{"id": "lobby", "rect": [-6, 6, -6, 0], "label": "L"}, {"id": "g1", "rect": [-6, 6, -18, -6], "label": "1"}, {"id": "g2", "rect": [-6, 6, -30, -18], "label": "2"}, {"id": "g3", "rect": [-6, 6, -42, -30], "label": "3"},
              {"id": "wax", "rect": [-8.5, 8.5, -81, -42.3], "label": "WAX HALL"}, {"id": "hallL", "rect": [-12, -6, -4.6, -1.4]}, {"id": "lib", "rect": [-32, -12, -13, 7], "label": "LIBRARY", "also": "libAisle"}, {"id": "hallR", "rect": [6, 12, -4.6, -1.4]},
              {"id": "school", "rect": [12, 34, -4.75, -1.25]}, {"id": "studio", "rect": [14, 24, -13, -4.75], "label": "101"}, {"id": "lab", "rect": [25.6, 34, -13, -4.75], "label": "102"}, {"id": "blueprint", "rect": [12.2, 24, -1.25, 7], "label": "103"},
              {"id": "world", "rect": [24, 34, -1.25, 7], "label": "104"}, {"id": "yard", "rect": [34, 92, -8.6, 26], "label": "RECESS YARD", "outdoor": True}, {"id": "coasterZone", "rect": [32, 92, -34, -8.6], "label": "COASTER", "outdoor": True},
              {"id": "dropMap", "rect": [73.4, 82.6, 8.4, 17.6], "label": "DROP", "round": True}, {"id": "diveMap", "rect": [49.8, 58.2, 11.8, 20.2], "label": "DIVE", "round": True}],
    "style": {"room_fill": "rgba(239,231,213,0.06)", "current_room_fill": "rgba(205,169,97,0.32)", "outdoor_fill": "rgba(120,170,100,0.12)", "stroke": "rgba(205,169,97,0.75)", "outdoor_stroke": "rgba(150,196,128,0.6)", "round_fill": "rgba(242,193,78,0.22)", "label_font": "7-8px Courier Prime", "player": "dot r2.6 #efe7d5 with a view cone r11 ±0.55 rad rgba(205,169,97,0.55)"},
    "click": "nearest room rect (within 4 m) -> MAP_GO[id] -> PLACES[id].view(); keyboard activation cycles lobby,g1,g2,g3,wax,library,studio,lab,blueprints,worldroom,yard",
    "map_go": {"lobby": "lobby", "g1": "g1", "g2": "g2", "g3": "g3", "wax": "wax", "hallL": "library", "lib": "library", "hallR": "school", "school": "school", "studio": "studio", "lab": "lab", "blueprint": "blueprints", "world": "worldroom", "yard": "yard", "coasterZone": "coaster", "dropMap": "drop", "diveMap": "dive"},
    "src": "parts/ui.js:672-736"
}

spec = {
    "$schema_note": "XRLibraries Campus / Walk the Archive - layout spec for the UE5 rebuild. Generated by gen_layout.py from parts/*.js (three.js r170). All *_m values are three.js campus metres (Y up); *_cm values are Unreal centimetres (Z up).",
    "generated": "2026-10-16",
    "source": {"repo": "/home/user/xr-campus-assets", "files": ["parts/nav.js", "parts/world.js", "parts/rooms.js", "parts/outdoor.js", "parts/waxhall.js", "parts/waxscenes.js", "parts/gfx.js", "parts/ui.js", "parts/engine.js", "parts/people.js", "parts/data.js", "parts/phys.js", "parts/soccer.js", "parts/rides.js", "parts/progress.js", "parts/lab.js", "parts/blueprints.js", "parts/worldroom.js", "parts/paint.js", "parts/nature.js", "bl/library.py", "docs/realism-plan.md", "unreal/Pipeline/out/campus/lights.json", "unreal/Pipeline/out/reading_room/lights.json"]},
    "units": {"three": "metres, right-handed, +Y up, camera yaw 0 looks toward -Z (minimap 'north'), +X east, +Z south", "ue": "centimetres, left-handed, +Z up, +X forward, +Y right"},
    "coordinate_conversion": {
        "position": "UE_X = 100 * x_three ; UE_Y = 100 * z_three ; UE_Z = 100 * y_three",
        "position_inverse": "x = UE_X/100 ; y = UE_Z/100 ; z = UE_Y/100",
        "direction_vector": "(dx, dy, dz)_three -> (dx, dz, dy)_UE (no scale)",
        "yaw": "UE_yaw_deg = (-90 - degrees(yaw_three)) mod 360  [three yaw 0 (looks -Z) -> UE -90 (looks -Y); three +pi/2 (looks -X) -> UE 180; three -pi/2 (+X) -> UE 0; three pi (+Z) -> UE +90]",
        "pitch": "UE_pitch_deg = degrees(pitch_three)  (positive = look up in both)",
        "roll": "0",
        "campus_compass": {"north(-z)": "UE -Y", "south(+z)": "UE +Y", "east(+x)": "UE +X", "west(-x)": "UE -X", "up(+y)": "UE +Z"},
        "handedness_check": "UE basis in three.js coordinates: X=(1,0,0), Y=(0,0,1), Z=(0,1,0); X x Y (right-handed) = -Z, i.e. a left-handed triple, so the map is a proper (non-mirroring) transform. A test cube at three (1,0,0) must land at UE (100,0,0) and one at three (0,0,1) at UE (0,100,0); if a glTF/FBX import mirrors it, fix the importer axis settings rather than the data.",
        "blender_cross_check": "docs/realism-plan.md:25 and bl/library.py:4,29: Blender (bx,by,bz) = (x, -z, y). Blender->glTF (export_yup) gives (bx, bz, -by) = (x, y, z) = three.js, so lib.glb is already in campus axes (parts/baked.js:73). Blender->UE (FBX, UE's Y mirrored vs Blender) gives (bx, -by, bz) = (x, z, y) = this spec's UE map, and unreal/Pipeline/blender/export_reading_room.py:18-20 documents the same glTF->UE map (X=x, Y=z, Z=y). All three routes agree.",
        "alternative_not_used": "UE_X=-100*z, UE_Y=100*x, UE_Z=100*y (campus north = UE +X forward) is also a proper transform but is a 90 deg yaw of the chosen one; it would NOT match meshes imported from the existing glTF/FBX exports, so it is not used."
    },
    "global": {
        "eye_height_m": EYE, "camera": {"fov_vertical_deg": 66, "fov_portrait_deg": 80, "near_m": 0.05, "far_m": 260},
        "player": {"walk_mps": 3.0, "run_mps": 5.6, "jump_v_mps": 5.2, "gravity_mps2": 16, "head_bob_amp_m": 0.026, "nav_cell_m": 0.25, "nav_wall_pad_m": M_WALL, "nav_bounds_m": {"x0": -33, "x1": 93, "z0": -82, "z1": 27}, "src": "parts/nav.js:77-79,158-166, parts/world.js:10"},
        "heights_m": {"H_ROOM(museum)": H_ROOM, "H_HALL": H_HALL, "H_LIB": H_LIB, "H_SCHOOL": H_SCHOOL, "H_WAX": H_WAX, "wax_stage": 0.2, "lib_mezzanine_centre": 3.6, "src": "parts/world.js:10, parts/waxhall.js:7, bl/library.py:197"},
        "wall_thickness_m": {"interior_room_walls": 0.0, "museum_gallery_partitions": 0.3, "exterior_shell_offset_from_interior": 0.2, "library_jamb_reveal_blender": 0.45, "nav_wall_padding": M_WALL, "lockers_depth": 0.42, "wax_dividers": 0.3, "src": "parts/world.js:183-186, parts/outdoor.js:286-316, bl/library.py:248-253, parts/nav.js:4"},
        "stairs_ramps": "none: every walkable floor is at y=0. Raised but non-walkable: wax stages (0.2), coaster station platform (0.85), library mezzanine slabs (3.6, 0.95 deep, decorative), drop-tower seat ring (base 1.0).",
        "sky": {"zenith_linear": [0.105, 0.30, 0.68], "horizon_linear": [0.62, 0.77, 0.88], "ground_linear": [0.40, 0.46, 0.40], "sun_disc_linear": [1.0, 0.86, 0.64], "clouds": "fbm noise cover 0.5-0.8, drifting 0.006/s", "indoor_clear_srgb": "#0d1613", "fog": {"color_linear": [0.5952, 0.7469, 0.88], "near_m": 70, "far_m": 245}, "canvas_dome_fallback_srgb": ["#3b72b2", "#6e9fd0", "#b6d1e4", "#d6e5e9"], "src": "parts/gfx.js:13,53-91, parts/outdoor.js:95-118, parts/world.js:142,277"},
        "tonemapping": {"three": "ACESFilmic, exposure 1.0, sRGB output; post: GTAO r0.55, bloom 0.3/0.42/1.2, grade sat 1.12 vignette 0.32 lift 0.012", "src": "parts/gfx.js:42-50,280-320"},
        "quality_reference": {"shadow_map": 2048, "shadow_extent_m": 34, "grass_blades": 46000, "src": "parts/gfx.js:5-9"}
    },
    "wings": {"museum": ["lobby", "g1", "g2", "g3"], "wax": ["wax"], "lib": ["hallL", "lib", "libAisle"], "school": ["hallR", "school", "studio", "lab", "blueprint", "world"], "play": ["yard"], "note": "WING groups in parts/world.js:248-264; lamp wing assignment parts/gfx.js:159-166"},
    "rooms": rooms,
    "doors": doors,
    "windows": windows,
    "lights": lights,
    "emissive_fixtures": emissive_fixtures,
    "wax_hall": {"WH": WH, "stages": wax_stages, "dividers": dividers, "benches_m": [[0, 0, -56.95], [0, 0, -68.75]], "intro_wall": {"centre_m": [0, 1.8, -44.6], "size_m": [6.2, 3.6, 0.3], "faces": "intro card toward +z (door side), timeline toward -z"}, "runner": {"width": 3.2, "z0": -77.1, "z1": -41.1}, "track_lights": "two 0.06 black rails at x ±3.6, y 4.85, from z -45.3 to -79", "src": "parts/waxhall.js:7-23,256-372"},
    "library": {"bounds_m": {"x0": -32, "x1": -12, "z0": -13, "z1": 7}, "ceiling_m": H_LIB, "stacks": stacks, "aisle_z": [-5.6, -0.4],
                "furniture": [{"id": "reference-desk", "centre_m": [-17.2, 0, -6.9], "approx_size": "3.0 x 1.5 (3 obstacle circles r0.75 at x -18.2/-17.2/-16.2)", "card": "1.5x0.333 at (-17.2,0.62,-6.498)"},
                              {"id": "reading-tables", "centres_m": [[-17.5, 0, -10.8], [-17.5, 0, 4.6]], "approx_size": "~3.6 x 1.4 each (obstacles r1.05 at x -18.7/-17.5/-16.3)", "lamps": "3 reading lamps per table at y 1.09 (Blender L.001-L.006)"},
                              {"id": "featured-table", "centre_m": [-15.0, 0, 0.9], "approx_size": "~3.2 x 1.4", "books": "two rows of covers at z 0.62 (y 0.95) and 1.15 (y 1.13), card 1.4x0.31 facing +z"},
                              {"id": "freedom-board", "centre_m": [-21.4, 0, 1.0], "faces": "+x", "panel": "1.3x0.975 at y 1.35"}, {"id": "hanging-sign", "centre_m": [-14.4, 5.4, -3], "size": "3.2x0.87 facing ±x, hung on brass rods from the ceiling"},
                              {"id": "extra-obstacle", "centre_m": [-21.3, 0, -9.2], "r": 0.5}],
                "blender_shell": {"mezzanine": "slabs 0.95 deep, centre y 3.6, 0.22 thick, along N, S and E walls and the W wall outside z -5.6..-0.4", "laylight": [-30, -14, -3.9, -2.1], "coffers": "beams 0.28x0.34 every 2.5 m both ways", "rugs": "3 x (4.8x2.4) at x -27/-21.8/-16.6, z -4.2..-1.8", "src": "bl/library.py:196-317"},
                "baked_assets": {"web": "lib/lib.glb + lib/probe.hdr (parts/baked.js)", "ue": "unreal/Pipeline/out/reading_room/ReadingRoom.glb (lightmaps stripped) + lights.json"}, "src": "parts/world.js:410-469"},
    "exterior": exterior,
    "staff": staff,
    "stations": stations,
    "tokens": tokens,
    "exhibits": exhibits,
    "spawn": {"three": {"x": 0, "z": -0.7, "yaw_rad": 0, "pitch_rad": 0.02, "eye_y": EYE}, "ue": {"location_cm": ue_pos(0, 0, -0.7), "camera_cm": ue_pos(0, EYE, -0.7), "rotation_deg": {"pitch": ue_pitch(0.02), "yaw": ue_yaw(0.0), "roll": 0}},
              "notes": "lobby, 0.7 m in from the back (title) wall, facing north down the galleries; yaw reset to 0 on 'Enter' (parts/ui.js:45); attract mode sways yaw ±0.32 rad while the intro card is open (parts/ui.js:778)", "src": "parts/world.js:11"},
    "tour_stops": tour,
    "places": places,
    "minimap": minimap,
    "existing_ue_exports": {"campus_glb": "unreal/Pipeline/out/campus/{museum,waxIntro,wax,lib,school,outside,play,dive}.glb (three.js GLTFExporter greybox, metres, three.js axes; name tags item__/staff__/ride__/token__)", "reading_room_glb": "unreal/Pipeline/out/reading_room/ReadingRoom.glb", "lights_json": ["unreal/Pipeline/out/campus/lights.json (runtime point lights + sun)", "unreal/Pipeline/out/reading_room/lights.json (Blender lights)"], "note": "unreal/Pipeline/README.md is referenced by export_reading_room.py but does not exist in the repo"}
}

out = os.path.join(HERE, "layout.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(spec, f, indent=1, ensure_ascii=False)
json.load(open(out, encoding="utf-8"))
print("wrote", out, os.path.getsize(out), "bytes;", len(rooms), "rooms,", len(doors), "doors,", len(windows), "windows,", len(lights), "lights,", len(wax_stages), "stages,", len(exterior["features"]), "exterior features")
