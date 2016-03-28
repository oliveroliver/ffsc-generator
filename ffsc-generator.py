# FFSC (Flat Flexible Soldered Connector) Generator for use with Eagle
# Copyright (C) 2016 Oliver S
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import subprocess
import datetime
import math

########################################################################################################################

from parameters_1 import *    #  the user parameters should be in parameters_x.py

########################################################################################################################

now = datetime.datetime.now()

eagle_path = "C:\\EAGLE-7.2.0\\bin\\eaglecon.exe"
working_path = ".\\exports\\"
drc_path = ".\\drc-disable.dru"
filename = "ffsc-" + now.strftime("%Y-%m-%d-%H%M%S-%f")

override_inter_track_spacing_angle = 0

#   rotates a point around a point
def rotate_2d(degrees, point, origin):

    degrees *= -1

    x = point[0] - origin[0]
    y = point[1] - origin[1]

    new_x = (x*math.cos(math.radians(degrees))) - (y*math.sin(math.radians(degrees)))
    new_y = (x*math.sin(math.radians(degrees))) + (y*math.cos(math.radians(degrees)))

    new_x += origin[0]
    new_y += origin[1]

    return new_x, new_y

def draw_part_poly_eagle(signal_name, layer_number, width, poly_point_x, poly_point_y, radius, state):

    if (state == 0):        # if it's the first point
        text_file.write("LAYER {0:d};\n" .format(layer_number))
        text_file.write("POLYGON {0:s}{1:s} {2:.6g} ({3:.6g} {4:.6g}) @{5:+.6g} " \
                    .format(net_name_prefix, signal_name, width, poly_point_x, poly_point_y, radius))
    elif (state == 1):      # if it's a mid point
        text_file.write("({0:.6g} {1:.6g}) @{2:+.6g} " \
                    .format(poly_point_x, poly_point_y, radius))
    else:                   # if it's a end point
        text_file.write("({0:.6g} {1:.6g});\n" \
                    .format(poly_point_x, poly_point_y))

#   draw part of the poly needed, state: 0 = first point, 1 = any mid point, 2 = last point and radius: 0 = straight line, any other value = radius of arc
def draw_part_poly_transform(segment_number, signal_name, layer_number, width, poly_point_x, poly_point_y, radius, state):
    poly_point_x,poly_point_y = calc_new_point(segment_number,(poly_point_x,poly_point_y))
    draw_part_poly_eagle(signal_name, layer_number, width, poly_point_x, poly_point_y, radius, state)

#   this is like drawing a normal rectangle, except drawn as a poly, with transform functions included. origin and translation are (x,y) tuples
def draw_rect_poly_transform(segment_number, signal_name, layer_number, width, pad_start_x, pad_start_y, pad_finish_x, pad_finish_y):    # pass the signal name as a string
    draw_part_poly_transform(segment_number, signal_name, layer_number, width, pad_start_x+(polygon_draw_width/2), pad_start_y+(polygon_draw_width/2), 0, 0)
    draw_part_poly_transform(segment_number, signal_name, layer_number, width, pad_finish_x-(polygon_draw_width/2),pad_start_y+(polygon_draw_width/2), 0, 1)
    draw_part_poly_transform(segment_number, signal_name, layer_number, width, pad_finish_x-(polygon_draw_width/2),pad_finish_y-(polygon_draw_width/2), 0, 1)
    draw_part_poly_transform(segment_number, signal_name, layer_number, width, pad_start_x+(polygon_draw_width/2),pad_finish_y-(polygon_draw_width/2), 0, 1)
    draw_part_poly_transform(segment_number, signal_name, layer_number, width, pad_start_x+(polygon_draw_width/2),pad_start_y+(polygon_draw_width/2), 0, 2)

#   abstract drawing of wire
def draw_wire(signal_name, layer_number, wire_width, wire_start_x, wire_start_y, wire_finish_x, wire_finish_y):    
    text_file.write("LAYER {0:d};\n" .format(layer_number))
    text_file.write("WIRE '{0:s}{1:s}' {2:.6g} ({3:.6g} {4:.6g}) ({5:.6g} {6:.6g});\n" .format(net_name_prefix, signal_name, wire_width, wire_start_x, wire_start_y, wire_finish_x, wire_finish_y))
    
#   origin and translation are (x,y) tuples
def draw_wire_transform(segment_number, signal_name, layer_number, wire_width, (wire_start_x, wire_start_y), (wire_finish_x, wire_finish_y)):
    wire_start_x, wire_start_y = calc_new_point(segment_number, (wire_start_x, wire_start_y))
    wire_finish_x, wire_finish_y = calc_new_point(segment_number, (wire_finish_x, wire_finish_y))

    draw_wire(signal_name, layer_number, wire_width, wire_start_x, wire_start_y, wire_finish_x, wire_finish_y)
    
#   place a via at the location specified
def draw_via(signal_name, via_diameter, drill_diameter, layer_range, via_position_x, via_position_y):
     text_file.write("CHANGE DRILL {0:.6g};\n" .format(drill_diameter))
     text_file.write("VIA '{0:s}{1:s}' {2:.6g} Round {3:s} ({4:.6g} {5:.6g});\n" .format(net_name_prefix, signal_name, via_diameter, layer_range, via_position_x, via_position_y))
     
def draw_via_transform(segment_number, signal_name, via_diameter, drill_diameter, layer_range, via_position_x, via_position_y):
    via_position_x, via_position_y = calc_new_point(segment_number, (via_position_x, via_position_y))
    draw_via(signal_name, via_diameter, drill_diameter, layer_range, via_position_x, via_position_y)

#   abstract drawing of wire
def draw_arc(signal_name, layer_number, wire_width, clockwise, arc_start_x, arc_start_y, arc_diameter_x, arc_diameter_y, arc_finish_x, arc_finish_y):
    if clockwise == True:
        clockwise_verbose = "CW"
    else:
        clockwise_verbose = "CCW"
        
    text_file.write("LAYER {0:d}\n" .format(layer_number))
    text_file.write("ARC '{0:s}{1:s}' {2:s} ROUND {3:.6g} ({4:.6g} {5:.6g}) ({6:.6g} {7:.6g}) ({8:.6g} {9:.6g});\n" .format(net_name_prefix, signal_name, clockwise_verbose, wire_width, arc_start_x, arc_start_y, arc_diameter_x, arc_diameter_y, arc_finish_x, arc_finish_y))

def mitre_point(radius, (mitre_x, mitre_y)):
    text_file.write("MITER {0:.6g} ({1:.6g} {2:.6g});\n" .format(radius,mitre_x,mitre_y))

def mitre_point_transform(segment_number, radius, (mitre_x, mitre_y)):
    mitre_x, mitre_y = calc_new_point(segment_number, (mitre_x, mitre_y))
    mitre_point(radius, (mitre_x, mitre_y))


#   return the pad width according to the pad to track ratio and minimum pad size
def calc_pad_width(connection_number):

    if (track_widths[connection_number] * pad_width_to_track_ratio) < minimum_pad_width:
        return minimum_pad_width
    else:
        return (track_widths[connection_number] * pad_width_to_track_ratio)

#   calculate and return the start and end co-ordinates and the centre value
def calc_pad_coordinates(segment_number, connection_number):

    pad_length = pad_length_to_max_track_ratio * (pad_width_to_track_ratio * max(track_widths)) # work out the pad length

    sum_of_pad_widths = 0

    for i in range (0,len(track_widths)):
        sum_of_pad_widths += calc_pad_width(i)

    sum_of_pad_widths += (inter_pad_spacing*(len(track_widths)-1))  # sum the pad widths and add inter pad spacing

    pad_finish_y = segment_length[segment_number]
    pad_start_y = pad_finish_y - pad_length

    # now calculate the width, start x, finish x and centre
    pad_offset_x = 0

    for i in range (0,connection_number):
        pad_offset_x += calc_pad_width(i)

    pad_offset_x += (inter_pad_spacing*connection_number)  # sum the pad widths and add inter pad spacing

    pad_width = calc_pad_width(connection_number)
    pad_start_x = 0 - (sum_of_pad_widths / 2) + pad_offset_x
    pad_finish_x = 0 - (sum_of_pad_widths / 2) + pad_offset_x + pad_width
    pad_centre_x = 0 - (sum_of_pad_widths / 2) + pad_offset_x + (pad_width / 2)

    return pad_start_x, pad_start_y, pad_finish_x, pad_finish_y, pad_centre_x, pad_width, pad_length

#   calculate the x coordinate of the centre of the track requested, relative to the centre of all tracks and spacings added up together
def calc_track_centre_x(connection_number):

    sum_of_track_widths = sum(track_widths) + (inter_track_spacing_straight *(len(track_widths)-1))   # add up the track widths

    # now work out the x value of each track centre
    track_offset_x = 0
    for i in range (0,connection_number):
        track_offset_x += track_widths[i]

    track_offset_x += (inter_track_spacing_straight * connection_number)    # sum the track widths and add inter pad spacing
    track_left_x = 0 - (sum_of_track_widths / 2) + track_offset_x
    track_centre_x  = track_left_x + ((track_widths[connection_number])/2)

    return track_centre_x

#   calculate the perpendicular offset during the taper from the centre connection
def calc_perpendicular_offset(segment_number, connection_number, closest_centre_x_connection):

    next_angle_track_offset = 0

    # if the track centre x is less than the pad centre x, then its routing to the right hand side.
    if calc_track_centre_x(connection_number) < calc_pad_coordinates(segment_number, connection_number)[4]:
        step = 1        # if its routing the centre connection or right hand side
    else:
        step = -1       # if its routing the left hand side

    for i in range (closest_centre_x_connection,connection_number,step):
        if (override_inter_track_spacing_angle != 0):
            next_angle_track_offset += (track_widths[i]/2) + override_inter_track_spacing_angle + (track_widths[i+step]/2)
        else:
            next_angle_track_offset += (track_widths[i]/2) + inter_track_spacing_angle + (track_widths[i+step]/2)

    return next_angle_track_offset


def calc_meeting_y(segment_number, connection_number, centre_x_connection, m, x, additional_hyp_offset, c):

    y_intersect = (calc_pad_coordinates(segment_number, centre_x_connection)[1] - additional_track_from_pad_length) - (m * calc_pad_coordinates(segment_number, centre_x_connection)[4])   # c=y-(mx), calculate where it intersects the y axis
    y_offset = ((1 / math.cos(math.atan(m))) * (calc_perpendicular_offset(segment_number,connection_number, centre_x_connection) + additional_hyp_offset))                              # calculate the y offset using trig
    meet_y = (m * x) + (y_intersect - y_offset - c)                                                                                                                                     # y=mx+c

    return y_intersect, y_offset, meet_y

#   returns the distance on y axis between (pad_centre_x, pad_start_y) and track that may intersect it IF it overshoots, otherwise return 0
def calc_minimum_pad_length_ajustment(segment_number, connection_number, closest_centre_x_connection):

    pad_start_x, pad_start_y, pad_finish_x, pad_finish_y, pad_centre_x, pad_width, pad_length = calc_pad_coordinates(segment_number, connection_number)     # calc pad dimensions / coords for the connection number
    track_centre_x = calc_track_centre_x(connection_number)                                                                                                 # calc track centres for the connection number

    if track_centre_x < pad_centre_x:
        m = gradient_of_taper
    else:
        m = -gradient_of_taper

    total_additional_y_offset = 0

    # see if the connection intersects above the additional_track_from_pad_length, then calculate the maximum y_offset needed
    if (connection_number <= closest_centre_x_connection):  # if its left of centre (x = 0)
        track_y_intersect, track_y_offset, track_meet_pad_centre_y = calc_meeting_y(segment_number, connection_number, closest_centre_x_connection, m, calc_pad_coordinates(segment_number, connection_number)[4], 0, 0)
    else:
        track_y_intersect, track_y_offset, track_meet_pad_centre_y = calc_meeting_y(segment_number, connection_number, closest_centre_x_connection+1, m, calc_pad_coordinates(segment_number, connection_number)[4], 0, 0)

    if track_meet_pad_centre_y > (pad_start_y - additional_track_from_pad_length):
        total_additional_y_offset = track_meet_pad_centre_y - (pad_start_y - additional_track_from_pad_length)

    return total_additional_y_offset

# finds the maximum value returned from any connection using the calc_minimum_pad_length_adjustment
def find_max_overshoot(segment_number,closest_centre_x_connection):

    max_overshoot_y = 0

    for i in range(0, (len(track_widths)-1), 1):     # loop through every connection
        if (calc_minimum_pad_length_ajustment(segment_number, i, closest_centre_x_connection) > max_overshoot_y):
            max_overshoot_y = calc_minimum_pad_length_ajustment(segment_number, i, closest_centre_x_connection)     # set a new max_overshoot value

    return max_overshoot_y

# calculate the difference between the track y intersect on the outer tracks, return a +ve if left side needs to come down, -ve if right side needs to come down
def calc_symmetrical_offset(segment_number, closest_centre_x_connection): #left/right side pad adjustments should be 1 or 0. Whether to factor in the 'pad adjustments'

    if (symmetry_on_shape == False):
        return 0
    else:
        # work out the left and right outer track edges on segment 0, with track adjustment, to determine which side needs bringing down
        left_track_edge_intersect_y = calc_meeting_y(segment_number, 0, closest_centre_x_connection, -gradient_of_taper, (calc_track_centre_x(0)-(track_widths[0]/2)), (track_widths[0]/2), find_max_overshoot(segment_number,closest_centre_x_connection))[2]

        right_track_edge_intersect_y = calc_meeting_y(segment_number, len(track_widths)-1, closest_centre_x_connection+1, gradient_of_taper, (calc_track_centre_x(len(track_widths)-1)+(track_widths[len(track_widths)-1]/2)),(track_widths[len(track_widths)-1]/2), find_max_overshoot(segment_number,closest_centre_x_connection))[2]

        symmetrical_edge_offset_y = left_track_edge_intersect_y - right_track_edge_intersect_y

        return symmetrical_edge_offset_y


def draw_connection(segment_number, connection_number, closest_centre_x_connection):

    # 1/ get pad coords
    # 2/ work out what the max_overshoot needs to be (the potential overlap between an angled track and pad, before adjustments)
    # 3/ work out symmetry differences
    # 4/ draw the connection offsetting on Y by the max_overshoot and dividing the symmetry differences by number of connections on shorter side and adding it on to each spacing per connection

    pad_start_x, pad_start_y, pad_finish_x, pad_finish_y, pad_centre_x, pad_width, pad_length = calc_pad_coordinates(segment_number, connection_number)     # calc pad dimensions / coords for the connection number
    track_centre_x = calc_track_centre_x(connection_number)                                                                                 # calc track centres for the connection number

    if track_centre_x < pad_centre_x:
        m = gradient_of_taper
    else:
        m = -gradient_of_taper

    total_additional_spacing = find_max_overshoot(segment_number,closest_centre_x_connection)
    symmetrical_edge_offset_y = calc_symmetrical_offset(segment_number, closest_centre_x_connection)

    # now correct for any symmetry indifferences
    global override_inter_track_spacing_angle

    if (symmetrical_edge_offset_y > 0) and (connection_number <= closest_centre_x_connection):                  # if the left side needs to come down then calculate the intersect again, but without the calc_minimum_pad_length_adjustment
        symmetrical_edge_offset_y = calc_symmetrical_offset(segment_number, closest_centre_x_connection)        # recalculate the difference, but without pad adjustments on the LEFT side that would normally prevent pad collisions
        override_inter_track_spacing_angle = (abs((math.cos(math.atan(m)) * symmetrical_edge_offset_y )) / (closest_centre_x_connection)) + inter_track_spacing_angle   # calculate the perpendicular distance divided by the number of spaces to spread across
    elif (symmetrical_edge_offset_y < 0) and (connection_number > closest_centre_x_connection):                 # if the right side needs to come down then calculate the intersect again, but without the calc_minimum_pad_length_adjustment
        symmetrical_edge_offset_y = calc_symmetrical_offset(segment_number, closest_centre_x_connection)        # recalculate the difference, but without pad adjustments on the RIGHT side that would normally prevent pad collisions
        override_inter_track_spacing_angle = (abs((math.cos(math.atan(m)) * symmetrical_edge_offset_y )) / ((len(track_widths)-1) - (closest_centre_x_connection+1))) + inter_track_spacing_angle   # calculate the perpendicular distance divided by the number of spaces to spread across

    if (connection_number <= closest_centre_x_connection):  # if its left of centre (x = 0)
        y_intersect, y_offset, meet_pad_centre_y = calc_meeting_y(segment_number, connection_number, closest_centre_x_connection, m, pad_centre_x, 0, total_additional_spacing)
        y_intersect, y_offset, meet_track_centre_y = calc_meeting_y(segment_number, connection_number, closest_centre_x_connection, m, track_centre_x, 0, total_additional_spacing)
    else:
        y_intersect, y_offset, meet_pad_centre_y = calc_meeting_y(segment_number, connection_number, closest_centre_x_connection+1, m, pad_centre_x, 0, total_additional_spacing)
        y_intersect, y_offset, meet_track_centre_y = calc_meeting_y(segment_number, connection_number, closest_centre_x_connection+1, m, track_centre_x, 0, total_additional_spacing)

    override_inter_track_spacing_angle = 0

    draw_wire_transform(segment_number,str(connection_number),top_layer_number,track_widths[connection_number], (pad_centre_x, pad_start_y+(pad_length/2)), (pad_centre_x, meet_pad_centre_y))
    draw_wire_transform(segment_number,str(connection_number),top_layer_number,track_widths[connection_number], (pad_centre_x, meet_pad_centre_y), (track_centre_x, meet_track_centre_y))
    draw_wire_transform(segment_number,str(connection_number),top_layer_number,track_widths[connection_number], (track_centre_x, meet_track_centre_y), (track_centre_x, 0))

#   draws the outer cuts for the end sections and the reinforcement layers
def draw_outer_cut(segment_number, closest_centre_x_connection):

    symmetrical_edge_offset_y = calc_symmetrical_offset(segment_number, closest_centre_x_connection)

    # left hand side
    pad_start_x, pad_start_y, pad_finish_x, pad_finish_y, pad_centre_x, pad_width, pad_length = calc_pad_coordinates(segment_number,0)
    track_centre_x = calc_track_centre_x(0)

    outline_first_pad_x = pad_start_x - track_to_edge_spacing
    outline_first_track_x = track_centre_x - (track_widths[0]/2) - track_to_edge_spacing

    c = 0
    if (symmetrical_edge_offset_y > 0):             # to make the whole thing exactly symmetrical
        c += symmetrical_edge_offset_y

    left_outline_pad_intersect_y = calc_meeting_y(segment_number, 0, closest_centre_x_connection, -gradient_of_taper, outline_first_pad_x, track_to_edge_spacing+(track_widths[0]/2), find_max_overshoot(segment_number,closest_centre_x_connection)+c )[2]
    left_outline_track_intersect_y = calc_meeting_y(segment_number, 0, closest_centre_x_connection, -gradient_of_taper, outline_first_track_x, track_to_edge_spacing+(track_widths[0]/2), find_max_overshoot(segment_number,closest_centre_x_connection)+c )[2]

    # right hand side
    pad_start_x, pad_start_y, pad_finish_x, pad_finish_y, pad_centre_x, pad_width, pad_length = calc_pad_coordinates(segment_number, len(track_widths)-1)
    track_centre_x = calc_track_centre_x(len(track_widths)-1)

    outline_last_pad_x = pad_finish_x + track_to_edge_spacing
    outline_last_track_x = track_centre_x + (track_widths[len(track_widths)-1]/2) + track_to_edge_spacing

    c = 0
    if (symmetrical_edge_offset_y < 0):             # to make the whole thing exactly symmetrical
        c += -(symmetrical_edge_offset_y)

    right_outline_pad_intersect_y = calc_meeting_y(segment_number, len(track_widths)-1, closest_centre_x_connection+1, gradient_of_taper, outline_last_pad_x, track_to_edge_spacing+(track_widths[len(track_widths)-1]/2), find_max_overshoot(segment_number,closest_centre_x_connection)+c )[2]
    right_outline_track_intersect_y = calc_meeting_y(segment_number, len(track_widths)-1, closest_centre_x_connection+1, gradient_of_taper, outline_last_track_x, track_to_edge_spacing+(track_widths[len(track_widths)-1]/2), find_max_overshoot(segment_number,closest_centre_x_connection)+c )[2]

    # draw outline
    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_first_pad_x, segment_length[segment_number]), (outline_last_pad_x, segment_length[segment_number]))    # top line

    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_first_pad_x, segment_length[segment_number]), (outline_first_pad_x, left_outline_pad_intersect_y))     # left upper
    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_first_pad_x, left_outline_pad_intersect_y), (outline_first_track_x, left_outline_track_intersect_y))   # left angle
    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_first_track_x, left_outline_track_intersect_y), (outline_first_track_x, 0))                            # left lower

    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_last_pad_x, segment_length[segment_number]), (outline_last_pad_x, right_outline_pad_intersect_y))      # right upper
    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_last_pad_x, right_outline_pad_intersect_y), (outline_last_track_x, right_outline_track_intersect_y))   # right angle
    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_last_track_x, right_outline_track_intersect_y), (outline_last_track_x, 0))                             # right lower

    # miter the edges
    mitre_point_transform(segment_number, outline_corner_radius, (outline_first_pad_x, segment_length[segment_number]))     #top left
    mitre_point_transform(segment_number, outline_angle_radius, (outline_first_pad_x, left_outline_pad_intersect_y))        #left first angle
    mitre_point_transform(segment_number, outline_angle_radius, (outline_first_track_x, left_outline_track_intersect_y))    #left second angle

    mitre_point_transform(segment_number, outline_corner_radius, (outline_last_pad_x, segment_length[segment_number]))      #top right
    mitre_point_transform(segment_number, outline_angle_radius, (outline_last_pad_x, right_outline_pad_intersect_y))        #right first angle
    mitre_point_transform(segment_number, outline_angle_radius, (outline_last_track_x, right_outline_track_intersect_y))    #right second angle

    # draw the reinforcement layer

    draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, outline_first_pad_x, segment_length[segment_number], 0, 0)   # draw the first point

    for i in range (0,len(track_widths)):   # draw the arc shaped fingers around each pad

        pad_start_x, pad_start_y, pad_finish_x, pad_finish_y, pad_centre_x, pad_width, pad_length = calc_pad_coordinates(segment_number,i)                      # calculate the relevant pad dimensions

        draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, pad_start_x, segment_length[segment_number], 0, 1)
        # to calculate the height of the arc, use intersecting chord theorum R = (H/2) + ((W^2)/(8*H))
        draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, pad_start_x, segment_length[segment_number]-distance_arc_from_edge, (1 if (segment_number > 1) else -1) * (((pad_arc_height/2)+((pad_width*pad_width)/(8*pad_arc_height)))*2), 1)
        draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, pad_finish_x, segment_length[segment_number]-distance_arc_from_edge, 0, 1)
        draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, pad_finish_x, segment_length[segment_number], 0, 1)

    pad_start_x, pad_start_y, pad_finish_x, pad_finish_y, pad_centre_x, pad_width, pad_length = calc_pad_coordinates(segment_number, len(track_widths)-1)
    draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, outline_last_pad_x, segment_length[segment_number], 0, 1)

    draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, outline_last_pad_x, segment_length[segment_number]-taper_distance_from_edge, 0, 1)

    for i in range (0,triangles_across_width):  # draw the triangular tapered stress relief
        draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, outline_last_pad_x-(((abs(outline_first_pad_x)+outline_last_pad_x)/(triangles_across_width))*(i+1))+(((abs(outline_first_pad_x)+outline_last_pad_x)/(triangles_across_width))/2), segment_length[segment_number]-taper_distance_from_edge-triangle_height, 0, 1)
        draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, outline_last_pad_x-(((abs(outline_first_pad_x)+outline_last_pad_x)/(triangles_across_width))*(i+1)), segment_length[segment_number]-taper_distance_from_edge, 0, 1)

    draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, outline_first_pad_x, segment_length[segment_number]-taper_distance_from_edge, 0, 1)
    draw_part_poly_transform(segment_number, "reinforcement", reinforcement_layer_number, polygon_draw_width, outline_first_pad_x, segment_length[segment_number], 0, 2)

def draw_vias_all(segment_number):

    for connection_number in range (0,len(track_widths)):
        pad_width = calc_pad_coordinates(segment_number, connection_number)[5]
        # set the via size
        if ((preferred_via_drill_size+(via_annular_ring*2)+(minimum_via_to_pad_edge*2)) > pad_width):
            via_drill_size = pad_width-(via_annular_ring*2)-(minimum_via_to_pad_edge*2)
        else:
            via_drill_size = preferred_via_drill_size
        # draw the castellation ends
        draw_via_transform(segment_number, str(connection_number), via_drill_size+(via_annular_ring*2), via_drill_size, "1-16", calc_pad_coordinates(segment_number,connection_number)[4], segment_length[segment_number])
        # draw the centre via
        draw_via_transform(segment_number, str(connection_number), via_drill_size+(via_annular_ring*2), via_drill_size, "1-16", calc_pad_coordinates(segment_number,connection_number)[4], calc_pad_coordinates(segment_number,connection_number)[1]+(calc_pad_coordinates(segment_number,connection_number)[6]/2))

# calculate the point at which the segment should pivot around, assuming all segments are straight together
def calc_segment_rotation_origin(segment_number):

    # calaculate the X
    if (segment_angle[segment_number-1] < 0):           # if negative rotation
        origin_x = calc_track_centre_x(0) - segment_inner_radius[segment_number-1]
    else:                                               # if positive (clockwise rotation)
        origin_x = calc_track_centre_x(len(track_widths)-1) + segment_inner_radius[segment_number-1]

    origin_y = 0

    # calculate the Y
    for i in range (1,segment_number):
        origin_y += segment_length[i]

    return origin_x, origin_y

# calculate the absolute point at which the segment should pivot around, assuming they are angled at specified angles up to that point
def calc_abs_segment_origin_recursive(segment_number, count):

    if (count == 0):
        return calc_segment_rotation_origin(segment_number)
    else:
        return rotate_2d(segment_angle[count-1],(calc_abs_segment_origin_recursive(segment_number, count-1)), (calc_abs_segment_origin_recursive(segment_number-(segment_number-count), segment_number-(segment_number-count)-1)))

# calculate the new point location after passing the current point tuple (x,y) you need and the segment it is in
def calc_new_point(segment_number, point):

    new_x = point[0]
    new_y = point[1]

    if (segment_number == 0):                               # if its the first segment (segment 0) (i.e it's just mirroring it)
        new_x = point[0]
        new_y = -point[1]
    else:
        delta_y = 0

        for i in range (1,segment_number):                  # add on the correct length to the Y axis, assuming that all segments are positioned in a straight line
            delta_y += segment_length[i]

        new_y += delta_y

        for i in range (1,segment_number+1):    # loop through and run the recursive operation to calculate new coordinates
            new_x, new_y = rotate_2d(segment_angle[i-1],(new_x, new_y),(calc_abs_segment_origin_recursive(i, i-1)))    # rotate the point around the necessary origin

    return new_x, new_y

# draw the curved section
def draw_next_connection(angle_number):

    for connection_number in range (0,len(track_widths)):
        if (segment_angle[angle_number] != 0):          # if there is a curve
            if (segment_angle[angle_number] < 0):     # if negative rotation
                arc_diameter_x = calc_track_centre_x(connection_number) - ((calc_track_centre_x(connection_number) - calc_track_centre_x(0) + segment_inner_radius[angle_number])*2)
                clockwise = False
            else:                                   # if positive (clockwise rotation)
                arc_diameter_x = calc_track_centre_x(connection_number) + ((calc_track_centre_x(len(track_widths)-1) - calc_track_centre_x(connection_number) + segment_inner_radius[angle_number])*2)
                clockwise = True

            arc_track_diameter_x, arc_track_diameter_y = calc_new_point(angle_number,(arc_diameter_x,segment_length[angle_number]*int(angle_number != 0)))
            arc_track_start_x, arc_track_start_y = calc_new_point(angle_number,(calc_track_centre_x(connection_number),segment_length[angle_number]*int(angle_number != 0)))
            arc_track_finish_x, arc_track_finish_y = calc_new_point(angle_number+1,(calc_track_centre_x(connection_number),0))

            #draw_wire(str(connection_number), top_layer_number,track_widths[connection_number], arc_track_start_x, arc_track_start_y, arc_track_finish_x, arc_track_finish_y) # if a straight line was required, useful for testing
            draw_arc(str(connection_number), top_layer_number,track_widths[connection_number], clockwise, arc_track_start_x, arc_track_start_y, arc_track_diameter_x, arc_track_diameter_y, arc_track_finish_x, arc_track_finish_y)

            # draw the outline
            if (connection_number == 0) or (connection_number == len(track_widths)-1):    # if the connection number is 0, then draw the left hand outline ... using abs(y)/y to get multiplier 1 or -1
                arc_outline_diameter_x = arc_diameter_x + ((track_to_edge_spacing + (track_widths[connection_number]/2)) * ((abs(calc_track_centre_x(connection_number))/calc_track_centre_x(connection_number))*-1))
                arc_outline_diameter_y = segment_length[angle_number]*int(angle_number != 0)
                arc_outline_diameter_x,arc_outline_diameter_y = calc_new_point(angle_number,(arc_outline_diameter_x,arc_outline_diameter_y))
                arc_outline_start_x = calc_track_centre_x(connection_number) - ((track_to_edge_spacing + (track_widths[connection_number]/2)) * ((abs(calc_track_centre_x(connection_number))/calc_track_centre_x(connection_number))*-1))
                arc_outline_start_y = (segment_length[angle_number]*int(angle_number != 0))         # calculate the standard track position
                arc_outline_finish_x, arc_outline_finish_y = calc_new_point(angle_number+1,(arc_outline_start_x,0))
                arc_outline_start_x, arc_outline_start_y = calc_new_point(angle_number,(arc_outline_start_x,arc_outline_start_y))

                draw_arc("outline",outline_layer_number,outline_draw_width, clockwise, arc_outline_start_x, arc_outline_start_y, arc_outline_diameter_x, arc_outline_diameter_y, arc_outline_finish_x, arc_outline_finish_y)

def draw_inner(segment_number):

    for connection_number in range (0,len(track_widths)):
        draw_wire_transform(segment_number, str(connection_number),top_layer_number,track_widths[connection_number],(calc_track_centre_x(connection_number), 0), (calc_track_centre_x(connection_number), segment_length[segment_number]))

    #draw the outline for the inner section too
    outline_first_track_x = calc_track_centre_x(0) - (track_widths[0]/2) - track_to_edge_spacing
    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_first_track_x, 0), (outline_first_track_x, segment_length[segment_number]))                    # left lower

    outline_last_track_x = calc_track_centre_x(len(track_widths)-1) + (track_widths[len(track_widths)-1]/2) + track_to_edge_spacing
    draw_wire_transform(segment_number, "outline",outline_layer_number,outline_draw_width, (outline_last_track_x, 0), (outline_last_track_x, segment_length[segment_number]))                      # right lower

# segment number needs to be 0 (starting end) or 2 (finishing end)
def draw_end(segment_number):

    # find the point at which the angled part goes from -ve gradient to a +ve gradient
    for connection_number in range (0,len(track_widths)):
        if calc_track_centre_x(connection_number) > calc_pad_coordinates(0, connection_number)[4]:
                closest_centre_x_connection = connection_number

    # draw each of the pads, with the centre being at x = 0
    for connection_number in range (0,len(track_widths)):
        pad_start_x, pad_start_y, pad_finish_x, pad_finish_y, pad_centre_x, pad_width, pad_length = calc_pad_coordinates(segment_number, connection_number)
        draw_rect_poly_transform(segment_number, str(connection_number),top_layer_number,polygon_draw_width, pad_start_x, pad_start_y, pad_finish_x, pad_finish_y)   # top layer
        #draw_rect_poly_transform(segment_number, str(connection_number),bottom_layer_number,polygon_draw_width, pad_start_x, pad_start_y, pad_finish_x, pad_finish_y)   # bottom layer

    # now complete the tracks
    for connection_number in range (0,len(track_widths)):
        draw_connection(segment_number, connection_number, closest_centre_x_connection)

    # draw the outline
    draw_outer_cut(segment_number, closest_centre_x_connection)

    # draw on castellation vias and centre vias
    draw_vias_all(segment_number)

def output_eagle_script():

    global additional_track_from_pad_length

    # convert any int values to float in list
    for index, item in enumerate(track_widths):
        track_widths[index] = float(item)

# set the additional_track_from_pad_length to half of the widest track, OR leave if
#    if ((max(track_widths)/2) > additional_track_from_pad_length):
#        additional_track_from_pad_length = max(track_widths)/2

    for segment_number in range (0,len(segment_length)):
         if (segment_number == 0):                           # if it needs to draw the first end
             draw_end(segment_number)
         elif (segment_number == len(segment_length)-1):     # if it needs to draw the last end
             draw_next_connection(segment_number-1)
             draw_end(segment_number)
         else:                                               # otherwise draw a connecting curve and next inner segment
             draw_next_connection(segment_number-1)
             draw_inner(segment_number)


    for connection_number in range (0,len(track_widths)):
        text_file.write("RATSNEST {0:s}{1:d};\n" .format(net_name_prefix, connection_number))




# remove all zero values from length list (in case 0 has been passed to this)
#filter(lambda a: a != 0, track_lengths)

print('Creating new Eagle Script')

text_file = open(working_path + filename + ".scr", "w")
text_file.write("#Draws the outline of the flexible connector system;\n")
text_file.write("Grid mm 1 off;\n")
text_file.write("DRC LOAD " + drc_path + ";\n")
text_file.write("SET WIRE_BEND 2;\n")
text_file.write("SET PALETTE WHITE;\n") # set background colour

text_file.write("SET PALETTE 16 0xff297995;\n")     # set colour 16 non-highlighted colour aRGB
text_file.write("SET PALETTE 24 0xFF2A597A;\n")     # set colour 24 highlighted colour aRGB
text_file.write("SET COLOR_LAYER 1 16;\n")          # set top layer colour 16

text_file.write("SET PALETTE 17 0xffffad22;\n")     # set colour 17 non-highlighted colour aRGB
text_file.write("SET PALETTE 25 0xFF00FCFF;\n")     # set colour 25 highlighted colour aRGB
text_file.write("SET COLOR_LAYER 16 17;\n")         # set bottom layer colour 17

text_file.write("SET PALETTE 18 0xFFFF2323;\n")     # set colour 18 non-highlighted colour aRGB
text_file.write("SET PALETTE 26 0xCCFF2323;\n")     # set colour 26 highlighted colour aRGB
text_file.write("SET COLOR_LAYER 18 18;\n")         # set via colour 18

text_file.write("SET PALETTE 19 0xFF466f8c;\n")     # set colour 19 non-highlighted colour aRGB
text_file.write("SET PALETTE 27 0xCCff6833;\n")     # set colour 27 highlighted colour aRGB
text_file.write("SET COLOR_LAYER 20 19;\n")         # set colour 19


text_file.write("WINDOW;\n")

output_eagle_script()

text_file.write("RIPUP net_reinforcement;\n")
text_file.write("WINDOW FIT;\n")
text_file.write("EXPORT IMAGE " + working_path + filename + ".png 600;\n")
text_file.write("WRITE;\n")
#text_file.write("QUIT;\n")

text_file.close()

p = subprocess.Popen(eagle_path + " -S " + working_path + filename + ".scr " + working_path + filename + ".brd",shell=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
