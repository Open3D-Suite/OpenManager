"""OpenScene's own list of the settings each card can show (the Property Selector), per engine.

The property names are the ones each renderer / 3ds Max class exposes to MAXScript. Labels, ranges, defaults, order
and which ones are ticked by default are OpenScene's own choices. tools/make_props.py turns this into props.json.

Helpers: B bool, F float, I integer, S string, FN file name, C colour, T texture map, M matrix, D date, MAT material,
P pipeline. Arguments: name, short label (column / row), long label (Property Selector, tooltip), then for numbers
lo, hi, default, step. on=True: ticked by default.
"""


def _p(cls, name, short, long=None, lo=None, hi=None, value=None, step=None, on=False):
    d = {"name": name, "class": cls, "display": [short, long or short], "value": value, "enabled": on}
    if lo is not None:
        d["min"], d["max"] = lo, hi
    if step is not None:
        d["step"] = step
    return d


def B(name, short, long=None, value=False, on=False):
    return _p("BooleanClass", name, short, long, value=value, on=on)


def F(name, short, long=None, lo=None, hi=None, value=0.0, step=None, on=False):
    return _p("Float", name, short, long, lo, hi, value, step, on)


def INT(name, short, long=None, lo=None, hi=None, value=0, on=False):
    return _p("Integer", name, short, long, lo, hi, value, 1, on)


def S(name, short, long=None, value="", on=False):
    return _p("String", name, short, long, value=value, on=on)


def FN(name, short, long=None):
    return _p("Filename", name, short, long, value="")


def C(name, short, long=None):
    return _p("Color", name, short, long)


def T(name, short, long=None):
    return _p("Texturemap", name, short, long)


def M(name, short, long=None):
    return _p("Matrix3", name, short, long)


def D(name, short, long=None):
    return _p("Date", name, short, long, value=0)


def MAT(name, short, long=None, on=False):
    return _p("Material", name, short, long, on=on)


def PIPE(name, short, long=None):
    return _p("Pipeline", name, short, long)


# distances in scene units: wide on purpose, the number box takes any value
DIST = 100000.0

TABLES = {
    # ------------------------------------------------------------------ cameras
    "max_standard_cam": [
        F("fov", "FOV", "Field of view (degrees)", 1, 175, 45),
        B("orthoProjection", "Ortho", "Orthographic view"),
        B("clipManually", "Clipping", "Clipping planes on"),
        F("near_clip", "Clip near", "Clipping: near plane", 0, DIST, 1),
        F("far_clip", "Clip far", "Clipping: far plane", 0, DIST, 1000),
        B("showRanges", "Show ranges", "Environment ranges: show in viewport"),
        F("nearrange", "Env near", "Environment range: near", 0, DIST, 0),
        F("farrange", "Env far", "Environment range: far", 0, DIST, 1000),
    ],
    "max_physical_cam": [
        F("focal_length_mm", "Focal length", "Focal length (mm)", 5, 300, 35),
        F("film_width_mm", "Sensor width", "Sensor width (mm)", 1, 100, 36),
        B("specify_fov", "Use FOV", "Set the field of view instead of the focal length"),
        F("fov", "FOV", "Field of view (degrees)", 1, 175, 54),
        F("zoom_factor", "Zoom", "Zoom factor", 0.1, 10, 1, 0.01),
        F("target_distance", "Target dist.", "Target distance", 0, DIST, 100),
        F("f_number", "f-number", "Aperture (f-number)", 0.5, 32, 8, 0.1),
        B("use_dof", "DOF", "Depth of field on"),
        F("focus_distance", "Focus", "Focus distance", 0, DIST, 100),
        F("lens_breathing_amount", "Lens breathing", "Lens breathing amount", 0, 10, 1, 0.01),
        F("exposure_value", "EV", "Exposure value (EV)", -6, 24, 6, 0.1),
        F("iso", "ISO", "Film speed (ISO)", 25, 12800, 100),
        F("white_balance_kelvin", "White balance", "White balance (K)", 1000, 20000, 6500, 50),
        B("vignetting_enabled", "Vignette", "Vignetting on"),
        F("vignetting_amount", "Vignette amount", "Vignetting amount", 0, 10, 1, 0.01),
        B("motion_blur_enabled", "Motion blur", "Motion blur on"),
        F("shutter_length_seconds", "Shutter (s)", "Shutter duration (seconds)", 0, 10, 0.004, 0.0001),
        F("shutter_length_frames", "Shutter (frames)", "Shutter duration (frames)", 0, 10, 0.5, 0.01),
        B("shutter_offset_enabled", "Shutter offset", "Shutter offset on"),
        F("shutter_offset_seconds", "Offset (s)", "Shutter offset (seconds)", 0, 10, 0, 0.0001),
        F("shutter_offset_frames", "Offset (frames)", "Shutter offset (frames)", 0, 10, 0, 0.01),
        F("horizontal_shift", "Shift H", "Lens shift, horizontal (%)", -100, 100, 0, 0.1),
        F("vertical_shift", "Shift V", "Lens shift, vertical (%)", -100, 100, 0, 0.1),
        F("horizontal_tilt_correction", "Tilt H", "Tilt correction, horizontal", -1, 1, 0, 0.01),
        F("vertical_tilt_correction", "Tilt V", "Tilt correction, vertical", -1, 1, 0, 0.01),
        B("clip_on", "Clipping", "Clipping planes on"),
        F("clip_near", "Clip near", "Clipping: near plane", 0, DIST, 0),
        F("clip_far", "Clip far", "Clipping: far plane", 0, DIST, 1000),
        F("environment_near", "Env near", "Environment range: near", 0, DIST, 0),
        F("environment_far", "Env far", "Environment range: far", 0, DIST, 1000),
    ],
    "vray_cam": [
        F("focal_length", "Focal length", "Focal length (mm)", 5, 300, 40),
        F("film_width", "Sensor width", "Sensor width (mm)", 1, 100, 36),
        F("fov", "FOV", "Field of view (degrees)", 1, 175, 48),
        F("zoom_factor", "Zoom", "Zoom factor", 0.1, 10, 1, 0.01),
        F("target_distance", "Target dist.", "Target distance", 0, DIST, 200),
        F("f_number", "f-number", "Aperture (f-number)", 0.5, 32, 8, 0.1),
        B("use_dof", "DOF", "Depth of field on"),
        F("focus_distance", "Focus", "Focus distance", 0, DIST, 200),
        F("exposure_value", "EV", "Exposure value (EV)", -6, 24, 13, 0.1),
        F("ISO", "ISO", "Film speed (ISO)", 25, 12800, 100),
        F("shutter_speed", "Shutter", "Shutter speed (1/s)", 1, 8000, 200),
        F("temperature", "White balance", "White balance (K)", 1000, 20000, 6500, 50),
        B("vignetting", "Vignette", "Vignetting on"),
        F("vignetting_amount", "Vignette amount", "Vignetting amount", 0, 10, 1, 0.01),
        B("use_moblur", "Motion blur", "Motion blur on"),
        F("horizontal_shift", "Shift H", "Lens shift, horizontal", -1, 1, 0, 0.01),
        F("vertical_shift", "Shift V", "Lens shift, vertical", -1, 1, 0, 0.01),
        F("lens_horTilt", "Tilt H", "Lens tilt, horizontal", -1, 1, 0, 0.01),
        F("lens_tilt", "Tilt V", "Lens tilt, vertical", -1, 1, 0, 0.01),
        B("clip_on", "Clipping", "Clipping planes on"),
        F("clip_near", "Clip near", "Clipping: near plane", 0, DIST, 0),
        F("clip_far", "Clip far", "Clipping: far plane", 0, DIST, 1000),
        F("environment_near", "Env near", "Environment range: near", 0, DIST, 0),
        F("environment_far", "Env far", "Environment range: far", 0, DIST, 1000),
    ],
    "corona_cam": [
        F("focalLength", "Focal length", "Focal length (mm)", 5, 300, 35),
        F("sensorWidth", "Sensor width", "Sensor width (mm)", 1, 100, 36),
        F("fov", "FOV", "Field of view (degrees)", 1, 175, 54),
        F("zoomFactor", "Zoom", "Zoom factor", 0.1, 10, 1, 0.01),
        F("fStop", "f-number", "Aperture (f-number)", 0.5, 32, 16, 0.1),
        F("ISO", "ISO", "Film speed (ISO)", 25, 12800, 100),
        F("shutterSpeed", "Shutter", "Shutter speed (1/s)", 1, 8000, 50),
        B("enableDof", "DOF", "Depth of field on"),
        B("overrideFocusDistance", "Own focus", "Depth of field: use its own focus distance"),
        F("dofOverrideFocusDistance", "Focus", "Focus distance", 0, DIST, 100),
        B("enableCameraMb", "Camera blur", "Motion blur from the camera moving"),
        B("enableGeometryMb", "Object blur", "Motion blur from objects moving"),
        B("autoVerticalTilt", "Auto tilt", "Correct the vertical tilt automatically"),
        F("verticalTilt", "Tilt V", "Tilt, vertical", -1, 1, 0, 0.01),
        F("horizontalTilt", "Tilt H", "Tilt, horizontal", -1, 1, 0, 0.01),
        F("verticalShift", "Shift V", "Lens shift, vertical", -1, 1, 0, 0.01),
        F("horizontalShift", "Shift H", "Lens shift, horizontal", -1, 1, 0, 0.01),
        B("overrideBloomGlare", "Own bloom", "Bloom & glare: override the render settings"),
        B("enableBloomGlare", "Bloom on", "Bloom & glare on", True),
        F("bloomIntensity", "Bloom", "Bloom intensity", 0, 50, 1, 0.1),
        F("glareIntensity", "Glare", "Glare intensity", 0, 50, 1, 0.1),
        F("bloomGlareThreshold", "Threshold", "Bloom & glare threshold", 0, 20, 1, 0.1),
        F("clippingNear", "Clip near", "Clipping: near plane", 0, DIST, 0),
        F("clippingFar", "Clip far", "Clipping: far plane", 0, DIST, 1000),
        F("enviroNear", "Env near", "Environment range: near", 0, DIST, 0),
        F("enviroFar", "Env far", "Environment range: far", 0, DIST, 1000),
    ],
    "fstorm_cam": [
        INT("type", "Type", "Camera type", 0, 3),
        F("lens", "Focal length", "Focal length (mm)", 5, 300, 35),
        INT("fov_type", "FOV mode", "Field of view mode", 0, 1, 1),
        F("fov", "FOV", "Field of view (degrees)", 1, 175, 54),
        B("targeted", "Targeted", "Camera with target", True),
        F("targ_dist", "Target dist.", "Target distance", 0, DIST, 100),
        F("hor_shift", "Shift H", "Lens shift, horizontal", -1, 1, 0, 0.01),
        F("ver_shift", "Shift V", "Lens shift, vertical", -1, 1, 0, 0.01),
        F("hor_tilt", "Tilt H", "Tilt, horizontal", -1, 1, 0, 0.01),
        F("ver_tilt", "Tilt V", "Tilt, vertical", -1, 1, 0, 0.01),
        F("near_clipping", "Clip near", "Clipping: near plane", 0, DIST, 0),
        B("dof_override", "Own DOF", "Depth of field: override the render settings"),
        B("dof_enabled", "DOF", "Depth of field on"),
        INT("dof_type", "DOF mode", "Depth of field mode", 0, 1),
        F("dof_fnumber", "f-number", "Aperture (f-number)", 0.5, 32, 4, 0.1),
        F("dof_radius", "Aperture", "Aperture radius", 0, 100, 1, 0.01),
        B("dof_targeted", "Focus on target", "Focus on the camera target", True),
        F("dof_focaldist", "Focus", "Focus distance", 0, DIST, 100),
        INT("dof_blades", "Blades", "Aperture blades (0 = round)", 0, 16),
        F("dof_rotation", "Blade rotation", "Aperture blade rotation (degrees)", 0, 360, 0),
        B("tonemap_override", "Own tone map", "Tone mapping: override the render settings"),
        B("do_tonemapping", "Tone map", "Tone mapping on", True),
        F("exposure", "Exposure", "Exposure", 0, 20, 1, 0.01),
        F("contrast", "Contrast", "Contrast", 0, 1, 0.3, 0.01),
        F("saturation", "Saturation", "Saturation", 0, 5, 1, 0.01),
        F("high_saturation", "High sat.", "Saturation of the highlights", 0, 5, 1, 0.01),
        F("burn_value", "Burn", "Highlight burn", -5, 1, 0.2, 0.01),
        F("gamma", "Gamma", "Gamma", 0.1, 5, 1, 0.01),
        F("vignetting", "Vignette", "Vignetting", 0, 100, 0, 0.1),
        F("image_blur", "Blur", "Image blur", 0, 1, 0, 0.01),
        F("image_sharp", "Sharpen", "Image sharpening", 0, 1, 0, 0.01),
    ],
    # ------------------------------------------------------------------ suns and skies
    "vray_sun": [
        F("intensity_multiplier", "Intensity", "Intensity multiplier", 0, 10, 1, 0.01),
        F("size_multiplier", "Size", "Size multiplier (softer shadows)", 0, 64, 1, 0.1),
        F("turbidity", "Turbidity", "Air turbidity", 2, 20, 2.5, 0.1),
        F("ozone", "Ozone", "Ozone", 0, 1, 0.35, 0.01),
        F("indirect_horiz_illum", "Horizon light", "Indirect horizontal illumination (lx)", 0, 200000, 25000, 100),
        F("horizon_offset", "Horizon offset", "Horizon offset (degrees)", -90, 90, 0, 0.1),
        F("blend_angle", "Blend angle", "Horizon blend angle (degrees)", 0, 90, 5.7, 0.1),
    ],
    "vray_cloud": [
        B("clouds_on", "Clouds", "Clouds on"),
        B("ground_shadows", "Ground shadows", "Clouds cast shadows on the ground"),
        F("cloud_density", "Density", "Cloud density", 0, 1, 0.5, 0.01),
        F("clouds_density_multiplier", "Density mult.", "Cloud density multiplier", 0, 10, 1, 0.01),
        F("cloud_variety", "Variety", "Cloud variety", 0, 1, 0.3, 0.01),
        F("cirrus_amount", "Cirrus", "Cirrus amount", 0, 1, 0.2, 0.01),
        INT("clouds_seed", "Seed", "Random seed", 0, 99999),
        F("height", "Height", "Cloud height (m)", 0, 20000, 1000, 10),
        F("thickness", "Thickness", "Cloud layer thickness (m)", 0, 5000, 500, 10),
        F("offset_X", "Offset X", "Cloud offset X (m)", -DIST, DIST, 0),
        F("offset_Y", "Offset Y", "Cloud offset Y (m)", -DIST, DIST, 0),
        F("phase_X", "Phase X", "Cloud phase X (%)", 0, 100, 0, 0.1),
        F("phase_Y", "Phase Y", "Cloud phase Y (%)", 0, 100, 0, 0.1),
        B("clouds_contrails_enabled", "Contrails", "Contrails on"),
        INT("clouds_contrails_num_planes", "Contrail count", "Number of contrails", 0, 50, 5),
        F("clouds_contrails_strength", "Contrail strength", "Contrail strength", 0, 1, 0.5, 0.01),
        F("clouds_contrails_distortion", "Contrail distortion", "Contrail distortion", 0, 1, 0.5, 0.01),
        F("clouds_contrails_offset_X", "Contrail X", "Contrail offset X (m)", -DIST, DIST, 0),
        F("clouds_contrails_offset_Y", "Contrail Y", "Contrail offset Y (m)", -DIST, DIST, 0),
        F("clouds_contrails_time", "Contrail time", "Contrail time", -1000, 1000, 0, 0.1),
    ],
    "corona_sun": [
        F("intensity", "Intensity", "Intensity", 0, 10, 1, 0.01),
        F("sizeMultiplier", "Size", "Size multiplier (softer shadows)", 0, 64, 1, 0.1),
        B("visibleDirectly", "Seen", "Visible to the camera", True),
        B("visibleRefl", "In refl.", "Visible in reflections", True),
        B("visibleRefr", "In refr.", "Visible in refractions", True),
        B("visibleCaustics", "Caustics", "Makes caustics", True),
    ],
    "fstorm_sun": [
        F("power", "Power", "Sun power", 0, 50, 1, 0.01),
        F("size", "Size", "Sun size", 0, 64, 1, 0.1),
        F("turbidity", "Turbidity", "Air turbidity", 0, 10, 2, 0.01),
        F("density", "Density", "Air density", 0, 10, 1, 0.01),
        F("hour", "Hour", "Hour of the day", 0, 24, 12, 0.05),
        F("month", "Month", "Month", 1, 12, 6, 1),
        F("latitude", "Latitude", "Latitude (degrees)", -90, 90, 40, 0.01),
        F("north_direction", "North", "North direction (degrees)", 0, 360, 0, 0.1),
        B("targeted", "Targeted", "Sun with target"),
        F("target_distance", "Target dist.", "Target distance", 0, DIST, 100),
    ],
    "max_daylight": [
        F("controller.solar_time.controller.value", "Time", "Time of day (hours)", 0, 24, 12, 0.05),
        D("controller.solar_date.controller.value", "Date", "Date"),
        F("controller.latitude", "Latitude", "Latitude (degrees)", -90, 90, 40, 0.01),
        F("controller.longitude", "Longitude", "Longitude (degrees)", -180, 180, 0, 0.01),
    ],
    "corona_cloud": [
        F("intensityMultiplier", "Intensity", "Sky intensity", 0, 10, 1, 0.01),
        F("turbidity", "Turbidity", "Air turbidity", 1.7, 10, 2.5, 0.1),
        F("HorizonBlur", "Horizon blur", "Horizon blur", 0, 1, 0, 0.01),
        F("altitude", "Altitude", "Altitude above the ground", 0, 10, 0, 0.01),
        B("enableVolumeEffect", "Volume", "Volume effect on"),
        F("volumeEffectScale", "Volume scale", "Volume effect scale", 0, 10, 1, 0.01),
        B("cloudsEnable", "Clouds", "Clouds on"),
        F("cloudsAmount", "Cover", "Cloud cover", 0, 1, 0.5, 0.01),
        F("cloudsVariety", "Variety", "Cloud variety", 0, 1, 0.5, 0.01),
        F("cloudsCirrusAmount", "Cirrus", "Cirrus amount", 0, 1, 0.5, 0.01),
        F("cloudsPhase", "Phase", "Cloud phase (how they evolve)", 0, 1, 0, 0.01),
        INT("cloudsSeed", "Seed", "Random seed", 0, 99999),
        F("cloudsAltitude", "Cloud altitude", "Cloud altitude (m)", 0, 20000, 1000, 10),
        F("cloudsHeight", "Cloud height", "Cloud layer height (m)", 0, 10000, 1000, 10),
        B("cloudsContrailsEnable", "Contrails", "Contrails on"),
        INT("cloudsContrailsNumPlanes", "Contrail count", "Number of contrails", 0, 50, 5),
        F("cloudsContrailsStrength", "Contrail strength", "Contrail strength", 0, 1, 0.5, 0.01),
        F("cloudsContrailsDistortion", "Contrail distortion", "Contrail distortion", 0, 1, 0.5, 0.01),
        F("cloudsContrailsTime", "Contrail time", "Contrail time", 0, 100, 0, 0.1),
    ],
    # ------------------------------------------------------------------ maps
    "max_bitmap": [
        FN("filename", "File", "Image file"),
        F("coords.U_Offset", "Offset U", "Offset, horizontal (U)", -1, 1, 0, 0.01),
        F("coords.V_Offset", "Offset V", "Offset, vertical (V)", -1, 1, 0, 0.01),
        F("gamma", "Gamma", "Gamma", 0.1, 5, 1, 0.01),
        F("output.output_amount", "Output", "Output amount (brightness)", 0, 10, 1, 0.01),
    ],
    "max_cc": [
        F("hueShift", "Hue", "Hue shift (degrees)", -180, 180, 0, 0.1),
        F("saturation", "Saturation", "Saturation (%)", -100, 100, 0, 0.1),
        F("brightness", "Brightness", "Brightness (%)", -100, 100, 0, 0.1),
        F("contrast", "Contrast", "Contrast (%)", -100, 100, 0, 0.1),
    ],
    "vray_bitmap": [
        FN("HDRIMapName", "File", "Image file"),
        F("horizontalRotation", "Rotation H", "Rotation, horizontal (degrees)", -360, 360, 0, 0.1),
        F("verticalRotation", "Rotation V", "Rotation, vertical (degrees)", -180, 180, 0, 0.1),
        F("multiplier", "Multiplier", "Overall multiplier", 0, 10, 1, 0.01),
        F("renderMultiplier", "Render mult.", "Render multiplier", 0, 10, 1, 0.01),
        F("gamma", "Gamma", "Gamma", 0.1, 5, 1, 0.01),
        F("output.output_amount", "Output", "Output amount (brightness)", 0, 10, 1, 0.01),
    ],
    "corona_bitmap": [
        FN("filename", "File", "Image file"),
        F("uAngle", "Rotation H", "Rotation, horizontal (degrees)", -360, 360, 0, 0.1),
        F("uvwOffset.y", "Offset V", "Offset, vertical (V)", -1, 1, 0, 0.01),
        F("filteringBlur", "Blur", "Filtering blur", 0, 100, 0, 0.1),
        F("output.output_amount", "Output", "Output amount (brightness)", 0, 10, 1, 0.01),
    ],
    "fstorm_bitmap": [
        FN("filename", "File", "Image file"),
        F("rotation.z", "Rotation H", "Rotation, horizontal (degrees)", -360, 360, 0, 0.1),
        F("rotation.x", "Rotation V", "Rotation, vertical (degrees)", -180, 180, 0, 0.1),
        F("offset.x", "Offset U", "Offset, horizontal (U)", -1, 1, 0, 0.01),
        F("offset.y", "Offset V", "Offset, vertical (V)", -1, 1, 0, 0.01),
        F("gamma", "Gamma", "Gamma", 0.1, 5, 1, 0.01),
        F("output.output_amount", "Output", "Output amount (brightness)", 0, 10, 1, 0.01),
    ],
    "corona_cc": [
        F("exposure", "Exposure", "Exposure (EV)", -10, 10, 0, 0.01),
        F("gamma", "Gamma", "Gamma", 0.1, 5, 1, 0.01),
        F("brightness", "Brightness", "Brightness", -1, 1, 0, 0.01),
        F("contrast", "Contrast", "Contrast", 0, 10, 1, 0.01),
        F("saturation", "Saturation", "Saturation", -1, 1, 0, 0.01),
        F("hue", "Hue", "Hue shift (degrees)", -180, 180, 0, 0.1),
        F("temperature", "White balance", "White balance (K)", 1000, 20000, 6500, 50),
        F("greenMagentaTint", "Tint", "Green / magenta tint", -1, 1, 0, 0.01),
        B("invert", "Invert", "Invert the colours"),
    ],
    "fstorm_cc": [
        F("gamma", "Gamma", "Gamma", 0.1, 5, 1, 0.01),
        F("contrast", "Contrast", "Contrast", 0, 1, 0.5, 0.01),
        F("offset", "Offset", "Offset", 0, 1, 0.5, 0.01),
        F("saturation", "Saturation", "Saturation", 0, 5, 1, 0.01),
        F("hue", "Hue", "Hue shift", -1, 1, 0, 0.01),
        B("invert", "Invert", "Invert the colours"),
    ],
    "corona_select": [
        INT("selected", "Input", "Selected input", 0, 50),
    ],
    # ------------------------------------------------------------------ dome light (V-Ray)
    "vray_dome": [
        F("multiplier", "Multiplier", "Intensity multiplier", 0, 100, 1, 0.01),
        F("rotation.z_rotation", "Rotation", "Rotation around Z (degrees)", -360, 360, 0, 0.1),
        B("invisible", "Invisible", "Invisible to the camera"),
        B("castShadows", "Shadows", "Casts shadows", True),
        B("affect_diffuse", "Diffuse", "Lights diffuse", True),
        B("affect_specualr", "Specular", "Lights specular", True),  # the property is spelt so in V-Ray
        B("affect_reflections", "Reflections", "Shows in reflections", True),
        B("dome_spherical", "Full sphere", "Spherical dome (full sphere)", True),
        B("dome_affect_alpha", "Alpha", "Dome affects the alpha"),
        INT("texmap_locktodome", "Lock map", "Lock the texture to the dome", 0, 1),
    ],
    # ------------------------------------------------------------------ layers and objects (table columns)
    "max_layers": [
        S("name", "Name", "Layer name", on=True),
        B("on", "Visible", "Visible", on=True),
        B("isfrozen", "Frozen", "Frozen", on=True),
        B("renderable", "Renders", "Renderable", on=True),
        B("primaryVisibility", "Camera", "Visible to the camera", on=True),
        B("secondaryVisibility", "Refl./refr.", "Visible to reflections and refractions"),
        B("castShadows", "Casts shadows", "Casts shadows"),
        B("receiveShadows", "Gets shadows", "Receives shadows"),
        B("applyAtmospherics", "Atmosphere", "Takes atmospheric effects"),
        B("boxmode", "Box", "Shown as a box"),
        B("current", "Current", "Current layer"),
    ],
    "max_objects": [
        S("name", "Name", "Object name", on=True),
        B("isNodeHidden", "Hidden", "Hidden", on=True),
        B("isNodeFrozen", "Frozen", "Frozen"),
        B("renderable", "Renders", "Renderable", on=True),
        B("primaryVisibility", "Camera", "Visible to the camera", on=True),
        B("secondaryVisibility", "Refl./refr.", "Visible to reflections and refractions"),
        B("castShadows", "Casts shadows", "Casts shadows"),
        B("receiveShadows", "Gets shadows", "Receives shadows"),
        B("applyAtmospherics", "Atmosphere", "Takes atmospheric effects"),
        B("boxmode", "Box", "Shown as a box"),
        MAT("material", "Material", "Material", on=True),
        M("transform", "Transform", "Position, rotation and scale"),
    ],
    "vray_objects": [
        B("VRay_Matte_Enable", "Matte", "V-Ray matte object"),
        F("VRay_Matte_Alpha", "Matte alpha", "V-Ray matte: alpha contribution", -1, 1, 1, 0.01),
        F("VRay_Matte_ReflectionAmount", "Matte refl.", "V-Ray matte: reflection amount", 0, 1, 1, 0.01),
        F("VRay_Matte_RefractionAmount", "Matte refr.", "V-Ray matte: refraction amount", 0, 1, 1, 0.01),
        F("VRay_Matte_GIAmount", "Matte GI", "V-Ray matte: GI amount", 0, 1, 1, 0.01),
    ],
    # ------------------------------------------------------------------ render settings
    "vray_render": [
        INT("progressive_minSamples", "Progressive min", "Progressive: min subdivs", 1, 100, 1, on=True),
        INT("progressive_maxSamples", "Progressive max", "Progressive: max subdivs", 1, 1000, 100, on=True),
        F("progressive_noise_threshold", "Progressive noise", "Progressive: noise limit", 0, 1, 0.01, 0.001, on=True),
        F(
            "progressive_max_render_time",
            "Progressive time",
            "Progressive: time limit (minutes, 0 = none)",
            0,
            1440,
            0,
            0.5,
            on=True,
        ),
        INT("twoLevel_baseSubdivs", "Bucket min", "Bucket: min subdivs", 1, 100, 1),
        INT("twoLevel_fineSubdivs", "Bucket max", "Bucket: max subdivs", 1, 100, 24),
        F("twoLevel_threshold", "Bucket noise", "Bucket: noise limit", 0, 1, 0.01, 0.001),
        INT("imageSampler_shadingRate", "Shading rate", "Image sampler: shading rate", 1, 64, 6),
        INT("lightcache_subdivs", "Light cache", "Light cache subdivs", 100, 20000, 1000),
    ],
    "vraygpu_render": [
        F("max_render_time", "Time limit", "Time limit (minutes, 0 = none)", 0, 1440, 0, 0.5, on=True),
        INT("max_paths_per_pixel", "Samples", "Sample limit (0 = none)", 0, 100000, 0, on=True),
        F("aa_threshold", "Noise limit", "Noise limit", 0, 1, 0.01, 0.001, on=True),
        INT("raysPerPixel", "Rays / pixel", "Rays per pixel", 1, 128, 16),
        INT("bundleSize", "Bundle size", "Ray bundle size", 32, 4096, 256),
        INT("ipr_raysPerPixel", "IPR rays", "Rays per pixel in interactive", 1, 128, 1),
        INT("undersampling", "Undersampling", "Interactive undersampling", 0, 8, 2),
    ],
    "corona_render": [
        INT("progressive_passLimit", "Passes", "Pass limit (0 = none)", 0, 1000, 0, on=True),
        F("adaptivity_targetError", "Noise limit", "Noise level limit (%, 0 = none)", 0, 50, 0, 0.1, on=True),
        INT("progressive_timeLimit", "Time limit", "Time limit (minutes, 0 = none)", 0, 1440, 0, on=True),
        INT("shading_maxRayDepth", "Ray depth", "Max ray depth", 1, 256, 25),
        INT("shading_giToAaRatio", "GI vs AA", "GI / AA balance", 1, 64, 16),
        F("lights_samplesMult", "Light samples", "Light samples multiplier", 0, 64, 2, 0.1),
        F("shading_maxSampleIntensity", "Max intensity", "Max sample intensity (0 = off)", 0, 500, 20, 0.5),
        B("caustics_use", "Caustics", "Caustics solver on"),
        B("lights_renderHidden", "Hidden lights", "Render hidden lights"),
    ],
    "fstorm_render": [
        INT("max_samples", "Samples", "Sample limit", 1, 100000, 1000, on=True),
        F("time_limit", "Time limit", "Time limit (minutes)", 0, 1440, 0, 0.5, on=True),
        F("noise_threshold", "Noise limit", "Noise limit", 0, 1, 0.01, 0.001, on=True),
        INT("light_samples", "Light samples", "Light samples", 1, 64, 4),
        INT("max_depth", "Ray depth", "Max ray depth", 1, 64, 8),
        B("min_samples_enabled", "Min samples", "Minimum samples on"),
        F("min_samples_ratio", "Min ratio", "Minimum samples ratio", 0, 100, 3, 0.1),
        B("process_alpha", "Alpha", "Compute the alpha"),
        B("rendermask_on", "Mask", "Render mask on"),
        S("rendermask_ids", "Mask IDs", "Render mask: object IDs"),
        B("do_tonemapping", "Tone map", "Tone mapping on", True),
        F("exposure", "Exposure", "Exposure", 0, 20, 1, 0.01),
        F("kernel_exposure", "Kernel exposure", "Exposure inside the render kernel", 0, 20, 1, 0.01),
        F("contrast", "Contrast", "Contrast", 0, 1, 0.3, 0.01),
        F("saturation", "Saturation", "Saturation", 0, 5, 1, 0.01),
        F("high_saturation", "High sat.", "Saturation of the highlights", 0, 5, 1, 0.01),
        F("burn_value", "Burn", "Highlight burn", -5, 1, 0.2, 0.01),
        F("gamma", "Gamma", "Gamma", 0.1, 5, 1, 0.01),
        C("white_balance", "White balance", "White balance colour"),
        F("vignetting", "Vignette", "Vignetting", 0, 100, 0, 0.1),
        F("image_blur", "Blur", "Image blur", 0, 1, 0, 0.01),
        F("image_sharp", "Sharpen", "Image sharpening", 0, 1, 0, 0.01),
        B("lut_enabled", "LUT", "LUT on"),
        FN("lut_file", "LUT file", "LUT file"),
        F("lut_powr", "LUT amount", "LUT amount", 0, 1, 1, 0.01),
        F("environment_power", "Env. power", "Environment power", 0, 10, 1, 0.01),
        B("environment_texture_on", "Env. map", "Environment map on", True),
        B("environment_sampling_on", "Env. sampling", "Environment lights the scene directly"),
        # the property names below are spelt so in FStorm
        B("environment_atmoshpere_on", "Atmosphere", "Atmosphere on"),
        F("environment_atmoshpere_height", "Atm. height", "Atmosphere height", 0, DIST, 1000, 1),
        F("environment_atmoshpere_distance", "Atm. distance", "Atmosphere distance", 0, 10 * DIST, 10000, 1),
    ],
    # ------------------------------------------------------------------ lights (table columns)
    "vray_light": [
        S("name", "Name", "Light name", on=True),
        B("on", "On", "Light on", on=True),
        F("multiplier", "Intensity", "Intensity multiplier", on=True),
        F("color_temperature", "Kelvin", "Colour temperature (K)"),
        F("sizeLength", "Length", "Size: length"),
        F("sizeWidth", "Width", "Size: width"),
        B("invisible", "Invisible", "Invisible to the camera"),
        B("castShadows", "Shadows", "Casts shadows", True),
        B("affect_diffuse", "Diffuse", "Lights diffuse", True),
        B("affect_specualr", "Specular", "Lights specular", True),  # the property is spelt so in V-Ray
        B("affect_reflections", "Reflections", "Shows in reflections", True),
        M("transform", "Transform", "Position, rotation and scale"),
    ],
    "corona_light": [
        S("name", "Name", "Light name", on=True),
        B("on", "On", "Light on", on=True),
        F("intensity", "Intensity", "Intensity", on=True),
        F("blackbodyTemp", "Kelvin", "Colour temperature (K)"),
        F("width", "Width", "Size: width / radius"),
        F("height", "Height", "Size: height"),
        F("directionality", "Direction", "Directionality"),
        B("visibleDirectly", "Seen", "Visible to the camera"),
        B("visibleRefl", "In refl.", "Visible in reflections"),
        B("visibleRefr", "In refr.", "Visible in refractions"),
        B("occludeOtherLights", "Occludes", "Blocks other lights"),
        M("transform", "Transform", "Position, rotation and scale"),
    ],
    "fstorm_light": [
        S("name", "Name", "Light name", on=True),
        B("enabled", "On", "Light on", on=True),
        F("power", "Power", "Light power", on=True),
        F("temperature", "Kelvin", "Colour temperature (K)"),
        F("size_x", "Size X", "Size: X"),
        F("size_y", "Size Y", "Size: Y"),
        B("visible", "Seen", "Visible to the camera"),
        M("transform", "Transform", "Position, rotation and scale"),
    ],
}

# Corona Camera > Overrides: tone mapping and what the camera sees directly / in reflections / refractions
TABLES["corona_cam_overrides"] = [
    B("colorMappingOverride", "Own tone map", "Tone mapping: override the render settings"),
    B("colorMappingEnabled", "Tone map", "Tone mapping on"),
    PIPE("colorMappingPipeline", "Tone map operators", "Tone mapping: operators (taken from the camera)"),
    B("directOverride", "Direct override", "Environment seen directly: override"),
    C("directOverrideColor", "Direct colour", "Environment seen directly: colour"),
    B("directOverrideTexmapUse", "Direct uses map", "Environment seen directly: use the map"),
    T("directOverrideTexmap", "Direct map", "Environment seen directly: map"),
    B("reflectOverride", "Refl. override", "Environment in reflections: override"),
    C("reflectOverrideColor", "Refl. colour", "Environment in reflections: colour"),
    B("reflectOverrideTexmapUse", "Refl. uses map", "Environment in reflections: use the map"),
    T("reflectOverrideTexmap", "Refl. map", "Environment in reflections: map"),
    B("refractOverride", "Refr. override", "Environment in refractions: override"),
    C("refractOverrideColor", "Refr. colour", "Environment in refractions: colour"),
    B("refractOverrideTexmapUse", "Refr. uses map", "Environment in refractions: use the map"),
    T("refractOverrideTexmap", "Refr. map", "Environment in refractions: map"),
    B("enviroOverride", "Env override", "Whole environment: override"),
    C("enviroOverrideColor", "Env colour", "Whole environment: colour"),
    B("enviroOverrideTexmapUse", "Env uses map", "Whole environment: use the map"),
    T("enviroOverrideTexmap", "Env map", "Whole environment: map"),
    B("overrideVisibility", "Own visibility", "Visibility: use the camera's exclude list"),
    B("overrideSharpening", "Own sharpening", "Sharpening / blurring: override"),
    B("enableSharpening", "Sharpening", "Sharpening / blurring on"),
    F("sharpeningAmount", "Sharpen amount", "Sharpening amount", 0, 10, 1, 0.01),
    F("sharpeningRadius", "Sharpen radius", "Sharpening radius", 0, 10, 0.5, 0.01),
    F("blurringRadius", "Blur radius", "Blurring radius", 0, 10, 1.5, 0.01),
    F("bloomGlareSize", "Bloom size", "Bloom & glare size", 0, 100, 15, 0.1),
    F("bloomGlareColorIntensity", "Bloom colour", "Bloom & glare colour intensity", 0, 1, 0.3, 0.01),
    F("bloomGlareColorShift", "Colour shift", "Bloom & glare colour shift", 0, 1, 0.5, 0.01),
    INT("glareStreakCount", "Streaks", "Glare streak count", 1, 8, 3),
    F("glareRotation", "Glare rotation", "Glare rotation (degrees)", 0, 360, 15, 1),
    F("glareStreakBlur", "Streak blur", "Glare streak blur", 0, 1, 0.2, 0.01),
    B("overrideBokeh", "Own bokeh", "Bokeh: override"),
    INT("bokehBladeCount", "Blades", "Aperture blades", 3, 12, 6),
    F("bokehRotation", "Blade rotation", "Aperture blade rotation (degrees)", 0, 360, 0, 1),
    F("shutterAngle", "Shutter angle", "Shutter angle (degrees)", 0, 360, 180, 1),
    INT(
        "projection",
        "Projection",
        "Projection (0 perspective, 1 cylindrical, 2 spherical, 3 VR, 4 fisheye, 5 ortho)",
        0,
        5,
    ),
]

# a few more Corona render settings
TABLES["corona_render"] += [
    INT("denoise_filterType", "Denoiser", "Denoiser (0 none, 1 high quality, 2 NVIDIA, 3 Intel)", 0, 3),
    F("denoise_blendAmount", "Denoise amount", "Denoise amount", 0, 1, 0.65, 0.01),
    INT("shading_secondarySolver", "Secondary GI", "Secondary GI solver (0 path tracing, 3 UHD cache)", 0, 4, 3),
    B("lockSampling", "Lock sampling", "Lock the sampling pattern"),
    INT("system_numThreads", "Threads", "Render threads (0 = all)", 0, 256),
]
