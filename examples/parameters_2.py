# ALL UNITS IN MM. #

# layer configuration - the layer each of these features should be on

top_layer_number = 16
bottom_layer_number = 1
via_layer_number = 18
outline_layer_number = 20
reinforcement_layer_number = 1

polygon_draw_width = 0.1  # when drawing polygons (for pad outlines) the width to use for the wire

# outline parameters

outline_corner_radius = 0.5  # on the overall outline, the radius to make the 90 degree corners
outline_angle_radius = 1.0  # on the overall outline, the radius to make the other corners.
outline_draw_width = 0.2  # the width to draw the outline

# parameters that affect the reinforcement overlay

triangles_across_width = 6  # the number of triangles that are used for stress relief spacing
triangle_height = 7  # the total height of each triangle
taper_distance_from_edge = 2.0  # the distance from the edge of the connector before the taper starts
pad_arc_height = 1.0  # the height of the arc - MUST BE >= smallest pad width / 2
distance_arc_from_edge = 1.0  # the distance of the pad arc start point from the edge of the connector - should really be above the via point

# all other parameters

track_to_edge_spacing = 0.5  # the distance from the edge of the outermost copper track to the kapton edge
inter_track_spacing_straight = 0.4  # the track-to-track spacing on straight parts of the connection
inter_track_spacing_angle = 0.4  # the track-to-track spacing on the angled parts of the connection - end segments need to be long enough

symmetry_on_shape = True  # if set to true, then symmetry is enforced on the overall shape

inter_pad_spacing = 0.9  # the spacing between the pads - will affect solderability
minimum_pad_width = 0.5  # the minimum pad width allowed regardless of track width
pad_width_to_track_ratio = 1.2  # the ratio of the pad width to track width e.g. at 1.2 a 1mm track would equate to a 1.2mm pad width
pad_length_to_max_track_ratio = 1.2  # this sets the pad length. This is worked out by taking the max track width, multiplied by pad_width_to_track_ratio, multiplied by this value.

additional_track_from_pad_length = -1.0  # the distance from the pad before starting the convergence of tracks on each end segment

preferred_via_drill_size = 0.3  # the preferred hole size
minimum_via_to_pad_edge = 0.1  # the minimum distance from the edge of the via annular ring to the pad edge
via_annular_ring = 0.1  # the annular ring to be shown on the drawing for each via - doesn't make much difference to manufacture as it's in-pad.

net_name_prefix = 'net_'  # the prefix used in the name of all nets

gradient_of_taper = 1.0  # the gradient of the taper that

# you can specify curved sections back to back by setting the corresponding length to 0

segment_length = [20, 5, 25.95, 25.95, 5, 20]  # this specifies both the length of each straight segment
segment_angle = [90, -180, 180, -180, 90]  # this specifies the angle of each join / curved section. There should be one less angle than connections in length list
segment_inner_radius = [2, 2, 2, 2, 2]  # the radius of each angle

track_widths = [0.15, 0.15, 0.15, 0.15, 0.5, 0.5, 0.5, 0.5, 1.0, 1.0, 1.0, 1.0, 0.15, 0.15]
