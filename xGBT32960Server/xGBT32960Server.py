#!/usr/bin/env python3
# -*- coding: utf8 -*-
# bluphy@163.com

# 2018-12-03 15:26:33 by xw: v0.4.3 Fix some bug if the received VIN is not ASCII character
# 2018-10-31 16:28:08 by xw: v0.4.2 Rename the advisor register/unregister function to bindVhl and unbindVhl, fix a bug when unbind vehicle
# 2018-10-31 16:38:49 by xw: v0.4.1 Update version number
# 2018-10-31 15:19:23 by xw: v0.4 更新xGBT32960ServerCore，支持回复Advisor的请求消息
# 2018-10-29 11:20:58 by xw: v0.3.1 更新xGBT32960ServerCore，处理advisor interface接收消息格式错误"
# 2018-10-26 17:08:06 by xw: v0.3 更新Vehicle类，简化server架构，使vehicle interface和advisor interface结构统一
# 2018-10-17 11:32:06 by xw: v0.2 拆分应用层部分到单独文件，增加应用层日志功能
# 2018-05-24 16:52 by xw: new created.

# TODO: 
# 

str_version = 'v0.4.3'

#### BEGIN Calibration

# DBHOST = '127.0.0.1'
# DBPORT = 5432
# DBNAME = 'bw_GBDirect_db'
# DBUSERNAME = 'bw_tester_admin'
# DBPASSWORD = '123456'

DBHOST = '10.40.166.7'
DBPORT = 5432
DBNAME = 'borgward_db'
DBUSERNAME = 'borgward'
DBPASSWORD = '123456'

TIMER_OTA_MSG_TIMEOUT = 30
LISTENING_VHL_PORT = 9201
LISTENING_ADVISOR_PORT = 31029
#### END Calibration

# BEGIN debug


# END debug 

# BEGIN xTSPSimulator_TOP
import argparse
import sys
import asyncio
# import functools
import time
import json
import socket
from async_timeout import timeout

from xGBT32960ServerCore.xDBService import connectdb
from xGBT32960ServerCore.xGBT32960ServerCore import Vehicle,Advisor,xDEBUG
from xGBT32960ServerCore.xOTAGBT32960 import timestamp

gDBhdl = None

async def handle_vehicle_connection(reader, writer):
    global gDBhdl
    vhl = Vehicle(reader,writer,gDBhdl)
    await vhl.startloop()
    print('Close the connection with vehicle VIN={0}'.format(vhl.VIN))
    vhl.destroy()
    vhl = None


async def handle_advisor_connection(reader:asyncio.StreamReader, writer:asyncio.StreamWriter):
    advisor = Advisor(reader,writer)
    await advisor.startloop()
    print('Close the connection with advisor:{0}'.format(advisor.username))
    advisor.destroy()
    advisor = None
    
# END xTSPSimulator_TOP

# BEGIN xTSPSimulator_MAIN
def main(args, dbName=DBNAME, dbUserName=DBUSERNAME, dbPassword=DBPASSWORD, dbHost=DBHOST, dbPort=DBPORT):
    if args.address:
        address = args.address
    else:
        try:
            address = socket.gethostbyname(socket.gethostname())
        except:
            print('use default address 127.0.0.1')
            address = '127.0.0.1'

    if args.vhlport:   
        port2vhl = args.vhlport
    else:
        port2vhl = LISTENING_VHL_PORT

    if args.advport:
        port2advisor = args.advport
    else:
        port2advisor = LISTENING_ADVISOR_PORT

    global gDBhdl
    gDBhdl = connectdb(dbName,dbUserName,dbPassword,dbHost,dbPort)

    loop = asyncio.get_event_loop()

    server2vhl_coro = asyncio.start_server(handle_vehicle_connection, address, port2vhl, loop=loop)
    server2advisor_coro = asyncio.start_server(handle_advisor_connection, address, port2advisor, loop=loop)

    task = asyncio.gather(server2vhl_coro,server2advisor_coro)
    servers = loop.run_until_complete(task)

    print('{0}\tVehicle interface serving on {1}'.format(timestamp(),servers[0].sockets[0].getsockname()))
    print('{0}\tAdvisor interface serving on {1}'.format(timestamp(),servers[1].sockets[0].getsockname()))

    try:
        print('run loop')
        loop.run_forever()
    finally:
        loop.close()

    for server in servers:
        server.close()
    gDBhdl['cursor'].close()
    gDBhdl['connection'].close()
    print('Server shut down.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", help='serving IP address', type=str)
    parser.add_argument("--vhlport", type=int, help="the tcp port number for vehicle connection", default=9201)
    parser.add_argument("--advport", type=int, help="the tcp port number for advisor client connection", default=31029)
    args = parser.parse_args()

    main(args)
# END xTSPSimulator_MAIN
