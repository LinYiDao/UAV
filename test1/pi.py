#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative
from pymavlink import mavutil  # Needed for command message definitions
import time
import math
import socket
import threading
import json
import queue
# Set up option parsing to get connection string
import argparse

#######################################################################
#
#   树莓派的反馈的协议 ：
#   [ {'Header':'RE','type':'0'},
#     {'lat':'','lon':'','version':'','battery':'','mode':'','status':''} ]
#
#   [{'Header':'CMD','type':'0'},{'msg':'msg'}]
#
#
#
#
host='192.168.84.129'
host_port=9991
cilent='223.3.69.213'
cilent_port=8888
#默认的type类型是 ’0‘ 。

connect_string='tcp:127.0.0.1:5760'
#goto里的速度
SPEED=4
#起飞的高度
ALT=3
global TYPE

global vehicle

def jsonmake(header,type,lat=None,lon=None,battery=None,current =  None,mode=None,status=None,version=None,msg=None):
    return json.dumps([{'Header':header,'type':type},
                       {'lat':lat,'lon':lon,'version':str(version),'battery':battery,'current':current,
                        'mode':mode,'status':status,
                        'msg':msg}])

#通过tcp接收到的消息。
recv_queue=queue.Queue()
#udp的消息发送队列
send_queue=queue.Queue()

#创建连接monitor的socket-udp
s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """
    global vehicle
    print("Basic pre-arm checks")
    send_queue.put(jsonmake('CMD', TYPE,msg='Basic pre-arm checks').encode('utf-8'))
    # Don't let the user try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        send_queue.put(jsonmake('CMD', TYPE, msg='Waiting for vehicle to initialise...').encode('utf-8'))
        time.sleep(1)

    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        send_queue.put(jsonmake('CMD', TYPE, msg='Waiting for arming...').encode('utf-8'))
        time.sleep(1)

    print("Taking off!")
    send_queue.put(jsonmake('CMD', TYPE, msg='Taking off!').encode('utf-8'))
    vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        send_queue.put(jsonmake('CMD', TYPE,
                                msg="Altitude:%s"%vehicle.location.global_relative_frame.alt).encode('utf-8'))
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude * 0.95:  # Trigger just below target alt.
            print("Reached target altitude")
            send_queue.put(jsonmake('CMD', TYPE, msg='Reached target altitude').encode('utf-8'))
            break
        time.sleep(1)


def condition_yaw(heading, relative=False):
    global vehicle
    if relative:
        is_relative = 1  # yaw relative to direction of travel
    else:
        is_relative = 0  # yaw is an absolute angle
    # create the CONDITION_YAW command using command_long_encode()
    msg = vehicle.message_factory.command_long_encode(
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
        0,  # confirmation
        heading,  # param 1, yaw in degrees
        0,  # param 2, yaw speed deg/s
        1,  # param 3, direction -1 ccw, 1 cw
        is_relative,  # param 4, relative offset 1, absolute angle 0
        0, 0, 0)  # param 5 ~ 7 not used
    # send command to vehicle
    vehicle.send_mavlink(msg)


def set_roi(location):
    global vehicle
    # create the MAV_CMD_DO_SET_ROI command
    msg = vehicle.message_factory.command_long_encode(
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_CMD_DO_SET_ROI,  # command
        0,  # confirmation
        0, 0, 0, 0,  # params 1-4
        location.lat,
        location.lon,
        location.alt
    )
    # send command to vehicle
    vehicle.send_mavlink(msg)

def get_location_metres(original_location, dNorth, dEast):
    """
    Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the
    specified `original_location`. The returned LocationGlobal has the same `alt` value
    as `original_location`.

    The function is useful when you want to move the vehicle around specifying locations relative to
    the current vehicle position.

    The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.

    For more information see:
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    """
    global vehicle
    earth_radius = 6378137.0  # Radius of "spherical" earth
    # Coordinate offsets in radians
    dLat = dNorth / earth_radius
    dLon = dEast / (earth_radius * math.cos(math.pi * original_location.lat / 180))

    # New position in decimal degrees
    newlat = original_location.lat + (dLat * 180 / math.pi)
    newlon = original_location.lon + (dLon * 180 / math.pi)
    if type(original_location) is LocationGlobal:
        targetlocation = LocationGlobal(newlat, newlon, original_location.alt)
    elif type(original_location) is LocationGlobalRelative:
        targetlocation = LocationGlobalRelative(newlat, newlon, original_location.alt)
    else:
        raise Exception("Invalid Location object passed")

    return targetlocation;


def get_distance_metres(aLocation1, aLocation2):
    global vehicle
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat * dlat) + (dlong * dlong)) * 1.113195e5


def get_bearing(aLocation1, aLocation2):
    global vehicle
    off_x = aLocation2.lon - aLocation1.lon
    off_y = aLocation2.lat - aLocation1.lat
    bearing = 90.00 + math.atan2(-off_y, off_x) * 57.2957795
    if bearing < 0:
        bearing += 360.00
    return bearing;



def goto_position_target_global_int(aLocation):
    """
    Send SET_POSITION_TARGET_GLOBAL_INT command to request the vehicle fly to a specified LocationGlobal.

    For more information see: https://pixhawk.ethz.ch/mavlink/#SET_POSITION_TARGET_GLOBAL_INT

    See the above link for information on the type_mask (0=enable, 1=ignore).
    At time of writing, acceleration and yaw bits are ignored.
    """
    global vehicle
    msg = vehicle.message_factory.set_position_target_global_int_encode(
        0,  # time_boot_ms (not used)
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
        0b0000111111111000,  # type_mask (only speeds enabled)
        aLocation.lat * 1e7,  # lat_int - X Position in WGS84 frame in 1e7 * meters
        aLocation.lon * 1e7,  # lon_int - Y Position in WGS84 frame in 1e7 * meters
        aLocation.alt,
        # alt - Altitude in meters in AMSL altitude, not WGS84 if absolute or relative, above terrain if GLOBAL_TERRAIN_ALT_INT
        0,  # X velocity in NED frame in m/s
        0,  # Y velocity in NED frame in m/s
        0,  # Z velocity in NED frame in m/s
        0, 0, 0,  # afx, afy, afz acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)
    # send command to vehicle
    vehicle.send_mavlink(msg)


def goto_position_target_local_ned(north, east, down):
    """
    Send SET_POSITION_TARGET_LOCAL_NED command to request the vehicle fly to a specified
    location in the North, East, Down frame.

    It is important to remember that in this frame, positive altitudes are entered as negative
    "Down" values. So if down is "10", this will be 10 metres below the home altitude.

    Starting from AC3.3 the method respects the frame setting. Prior to that the frame was
    ignored. For more information see:
    http://dev.ardupilot.com/wiki/copter-commands-in-guided-mode/#set_position_target_local_ned

    See the above link for information on the type_mask (0=enable, 1=ignore).
    At time of writing, acceleration and yaw bits are ignored.

    """
    global vehicle
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,  # time_boot_ms (not used)
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
        0b0000111111111000,  # type_mask (only positions enabled)
        north, east, down,  # x, y, z positions (or North, East, Down in the MAV_FRAME_BODY_NED frame
        0, 0, 0,  # x, y, z velocity in m/s  (not used)
        0, 0, 0,  # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)
    # send command to vehicle
    vehicle.send_mavlink(msg)


def goto(dNorth, dEast):
    global vehicle
    gotoFunction = vehicle.simple_goto
    currentLocation = vehicle.location.global_relative_frame
    targetLocation = get_location_metres(currentLocation, dNorth, dEast)
    targetDistance = get_distance_metres(currentLocation, targetLocation)
    gotoFunction(targetLocation)

    # print "DEBUG: targetLocation: %s" % targetLocation
    # print "DEBUG: targetLocation: %s" % targetDistance

    while vehicle.mode.name == "GUIDED":  # Stop action if we are no longer in guided mode.
        # print "DEBUG: mode: %s" % vehicle.mode.name
        remainingDistance = get_distance_metres(vehicle.location.global_relative_frame, targetLocation)
        print("Distance to target: ", remainingDistance)
        send_queue.put(jsonmake('RE', TYPE, vehicle.location.global_relative_frame.lat,
                                vehicle.location.global_relative_frame.lon,
                                vehicle.battery.voltage, vehicle.battery.current,
                                vehicle.mode.name,
                                vehicle.system_status.state, vehicle.version).encode('utf-8'))
        if remainingDistance <= 1:  # Just below target, in case of undershoot.
            print("Reached target")
            break
        time.sleep(0.5)


def send_ned_velocity(velocity_x, velocity_y, velocity_z, duration):
    global vehicle
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0,  # time_boot_ms (not used)
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_FRAME_LOCAL_NED,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0, 0, 0,  # x, y, z positions (not used)
        velocity_x, velocity_y, velocity_z,  # x, y, z velocity in m/s
        0, 0, 0,  # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # send command to vehicle on 1 Hz cycle
    for x in range(0, duration):
        vehicle.send_mavlink(msg)
        for x in range(2):
            print(vehicle.location.global_relative_frame)
            #添加发送的消息。
            send_queue.put(jsonmake('RE',TYPE,vehicle.location.global_relative_frame.lat,
                                    vehicle.location.global_relative_frame.lon,
                                    vehicle.battery.voltage,vehicle.battery.current,vehicle.mode.name,
                                    vehicle.system_status.state,vehicle.version).encode('utf-8'))
            time.sleep(0.5)


def send_global_velocity(velocity_x, velocity_y, velocity_z, duration):
    """
    Move vehicle in direction based on specified velocity vectors.

    This uses the SET_POSITION_TARGET_GLOBAL_INT command with type mask enabling only
    velocity components
    (http://dev.ardupilot.com/wiki/copter-commands-in-guided-mode/#set_position_target_global_int).

    Note that from AC3.3 the message should be re-sent every second (after about 3 seconds
    with no message the velocity will drop back to zero). In AC3.2.1 and earlier the specified
    velocity persists until it is canceled. The code below should work on either version
    (sending the message multiple times does not cause problems).

    See the above link for information on the type_mask (0=enable, 1=ignore).
    At time of writing, acceleration and yaw bits are ignored.
    """
    global vehicle
    msg = vehicle.message_factory.set_position_target_global_int_encode(
        0,  # time_boot_ms (not used)
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,  # frame
        0b0000111111000111,  # type_mask (only speeds enabled)
        0,  # lat_int - X Position in WGS84 frame in 1e7 * meters
        0,  # lon_int - Y Position in WGS84 frame in 1e7 * meters
        0,  # alt - Altitude in meters in AMSL altitude(not WGS84 if absolute or relative)
        # altitude above terrain if GLOBAL_TERRAIN_ALT_INT
        velocity_x,  # X velocity in NED frame in m/s
        velocity_y,  # Y velocity in NED frame in m/s
        velocity_z,  # Z velocity in NED frame in m/s
        0, 0, 0,  # afx, afy, afz acceleration (not supported yet, ignored in GCS_Mavlink)
        0, 0)  # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink)

    # send command to vehicle on 1 Hz cycle
    for x in range(0, duration):
        vehicle.send_mavlink(msg)
        time.sleep(1)

#执行接收队列中的消息的线程
def taketask():
    global TYPE
    while True:
        if (recv_queue.qsize() != 0):
            task=recv_queue.get()
            time.sleep(0.5)
            #如果是连接指令，那么就连接无人机飞控.
            if(task[0]['Header']=='CONN'):
                global vehicle
                TYPE=task[0]['type']
                vehicle = connect(connect_string, wait_ready=True)
                # 添加发送的消息。
                send_queue.put(jsonmake('RE', TYPE, vehicle.location.global_relative_frame.lat,
                                        vehicle.location.global_relative_frame.lon,
                                        vehicle.battery.voltage, vehicle.battery.current,vehicle.mode.name,
                                        vehicle.system_status.state, vehicle.version).encode('utf-8'))
                continue
            #如果是RC指令，那么就分析是什么指令。
            elif(task[0]['Header']=='RC'):
                if(task[1]['cmd']=='1'):
                    arm_and_takeoff(ALT)
                    vehicle.groundspeed=SPEED
                    continue
                elif(task[1]['cmd']=='2'):
                    vehicle.mode=VehicleMode("LAND")
                    send_queue.put(jsonmake('RE', TYPE, vehicle.location.global_relative_frame.lat,
                                            vehicle.location.global_relative_frame.lon,
                                            vehicle.battery.voltage,vehicle.battery.current, vehicle.mode.name,
                                            vehicle.system_status.state, vehicle.version).encode('utf-8'))
                    continue
                elif (task[1]['cmd'] == '3'):
                    send_ned_velocity(1,0,0,1)
                    send_ned_velocity(0,0,0,1)
                    continue
                elif (task[1]['cmd'] == '4'):
                    send_ned_velocity(-1,0,0,1)
                    send_ned_velocity(0,0,0,1)
                    continue
                elif (task[1]['cmd'] == '5'):
                    send_ned_velocity(0,1,0,1)
                    send_ned_velocity(0,0,0,1)
                    continue
                elif (task[1]['cmd'] == '6'):
                    send_ned_velocity(0,-1,0,1)
                    send_ned_velocity(0,0,0,1)
                    continue
            elif(task[0]['Header']=='GU'):
                goto(int(task[1]['content'][0]),int(task[1]['content'][1]))
        time.sleep(0.5)

def sendmsg():
    while True:
        if (send_queue.qsize() != 0):
#            print(send_queue)
            port=cilent_port+int(TYPE)
            s1.sendto(send_queue.get(),(cilent,port))
        time.sleep(0.5)


def recvPC(sock, addr):
    print('Accept new connection from %s:%s...' % addr)
    #    sock.send(b'Welcome!')
    #开启一个辅助线程。用于执行指令。
    t1 = threading.Thread(target=taketask)
    t1.start()
    #开启线程2 ，用于传输消息。
    t2 = threading.Thread(target=sendmsg)
    t2.start()
    while True:
        data = sock.recv(1024)
        time.sleep(0.5)
        print(data.decode('utf-8'))
        if not data or data.decode('utf-8') == 'exit':
            break
        #消息队列中加消息
        recv_queue.put(json.loads(data.decode('utf-8')))
    sock.close()
    print('Connection from %s:%s closed.' % addr)


#主线程 ，监听TCP消息。
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((host, host_port))
s.listen(5)
print('Waiting for connection...')
while True:
    # 接受一个新连接:
    sock, addr = s.accept()
    # 创建新线程来处理TCP连接:
    t = threading.Thread(target=recvPC, args=(sock, addr))
    t.start()


