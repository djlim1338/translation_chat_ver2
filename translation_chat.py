#!/bin/bash
"""

translation_chat.py
djlim

translation_chat

"""

import base64
import json
import os
import threading
import websockets
import asyncio
import time
import logging
import pymysql
from googletrans import Translator
import copy


log_file_dir = f"./log"
log_file_index = 1
log_file_path = f"{log_file_dir}/translation_chat_{log_file_index}.log"

data_dir = f"./data"
data_pic_dir = f"{data_dir}/pic"

dir_list = [log_file_dir, data_dir, data_pic_dir]
for dir_path in dir_list: # 사용하는 디렉토리 없으면 생성
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)

while os.path.isfile(log_file_path):  # 서버 재시작시 로그파일 새로 생성
    log_file_index += 1
    log_file_path = f"{log_file_dir}/translation_chat_{log_file_index}.log"

logging.basicConfig(  # 로그파일 생성
    filename=log_file_path,
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    encoding="UTF-8")  # 한글로 쓸거임  CP949 -> UTF-8


KEYBOARD_COMMAND = {
    'exit': {"EXIT", "QUIT", "E", "Q"}
}

tl = Translator()  # 구글 번역기


class ChatRoom:  # 채팅방
    # 채팅방 목록 및 정보
    chat_room_all = {}
    """
    채팅방ID를 key로 두고 리스트에는 채팅방에 참여중인 사용자ID값이 있음
    chat_room_all = {
        {chat room1 ID}: [{user1 ID}, {user2 ID} ...],
        {chat room2 ID}: [{user1 ID}, {user2 ID} ...],
        ...
    }
    """
    # 채팅방 사용자 객체 목록
    chat_user_all = {}
    """
    사용자ID를 key로 두고 그 유저에 해당하는 객체가 있음.
    chat_user_all = {
        {user1 ID}: {user1 object},
        {user2 ID}: {user2 object},
        ...
    }
    """
    # 채팅방 메시지 번호
    chat_room_dnum = {}  # dnum = data number 채팅방 메시지 번호
    """
    chat_room_dnum = {
        {chat room1 ID}: {data number}
    }
    """
    @classmethod
    def set_msg_num(cls, chat_id):
        db = DB()
        sql_str = f"SELECT MAX(chatNumber) FROM chatData WHERE roomId='{chat_id}'"  # 채팅방의 가장 큰 번호 불러옴
        max_msg_num = db.output(sql_str)
        msg_num = max_msg_num[0][0]
        if not msg_num:  # 새로 만들어진 방이라 번호가 없으면 0으로 초기화
            msg_num = 0
        log_str = f"chat room[{chat_id}] max number[{msg_num}]"
        logging.info(log_str)  # 로그 생성
        cls.chat_room_dnum[chat_id] = msg_num
        db.close()

    @classmethod
    def get_msg_num(cls, chat_id):
        cls.chat_room_dnum[chat_id] += 1
        return cls.chat_room_dnum[chat_id]


class ChatUser:  # 채팅방 사용자
    def __init__(self, user_id, chat_id, web_socket):
        self.user_id = user_id  # 사용자 ID
        self.chat_id = chat_id  # 채팅방 ID
        self.web_socket = web_socket  # 웹소켓 객체
        self.user_info = self.web_socket.remote_address  # 웹소켓 (IP, PORT)
        self.user_index = f"{user_id}:{self.user_info[1]}"  # 채팅 사용자 식별 인덱스 사용자ID:접속포트

    def get_user_id(self):
        return self.user_id

    def get_chat_id(self):
        return self.chat_id

    def get_user_info(self):
        return self.user_info

    def get_user_index(self):
        return self.user_index


class DB:  # 데이터베이스
    def __init__(self):
        self.db = pymysql.connect(
            host='localhost',
            user='djlim',
            password='12341324',
            db='translation_chat_web',
            charset='utf8')

    def input(self, sql_str):
        try:
            with self.db.cursor() as cursor:
                cursor.execute(sql_str)
            self.db.commit()
            log_str = f"DB : {sql_str}"
            logging.info(log_str)  # 로그 생성
        except Exception as e:
            log_str = f"DB ERROR: {sql_str} \n => {e} "
            logging.error(log_str)  # 로그 생성
            self.db.rollback()
        finally:
            self.db.close()

    def output(self, sql_str):
        result = None
        try:
            with self.db.cursor() as cursor:
                # SQL 문 실행
                cursor.execute(sql_str)
                result = cursor.fetchall()
            log_str = f"DB : {sql_str}"
            logging.info(log_str)  # 로그 생성
        except Exception as e:
            log_str = f"DB ERROR: {sql_str} \n => {e} "
            logging.error(log_str)  # 로그 생성
            self.db.rollback()
        finally:
            return result

    def close(self):
        if self.db:
            self.db.close()


async def send_chunk(chat_user, data):
    chunk_size = 1024
    send_data = str(len(data)) + ',' + data
    #send_data = data
    log_str = f"data send length: {send_data}"
    logging.debug(log_str)  # 로그 생성
    offset = 0
    chunk = None
    while offset < len(send_data):
        if len(send_data) <= chunk_size:
            chunk_size = len(send_data)
        chunk = send_data[offset:offset+chunk_size]
        await chat_user.web_socket.send(chunk)
        offset += chunk_size


async def msg_process(chat_user, data):  # 채팅 데이터 처리. 번역 및 채팅방 전송 등
    data_header = None
    #send_data = ""  # 다시 보낼 데이터
    if data.startswith('data:'):  # 파일
        data_header = data.split(',')[0]  # data:{데이터유형}/{확장자?};{encoding},{데이터}
        data_format = data_header.split(';')[0]
        data_format = data_format.split('/')[1]

        if data.startswith('data:image/'):
            data_type = "image"
            image_data = data.split(',')[1]
            index_num = 1
            file_path = f"{data_pic_dir}/image_{chat_user.get_chat_id()}_{chat_user.get_user_id()}_{index_num}.{data_format}"
            while os.path.isfile(file_path):  # 이름 중복 방지
                index_num += 1
                file_path = f"{data_pic_dir}/image_{chat_user.get_user_id()}_{chat_user.get_chat_id()}_{index_num}.{data_format}"

            with open(file_path, 'wb') as img_file:  # 이미지 저장
                image_data = base64.b64decode(image_data)
                img_file.write(image_data)
            send_data = data  # 다시 보낼 데이터
            lang_code = "ko"
    else:  # 문자
        data_type = "text"
        send_data = data  # 다시 보낼 데이터
        lang_code = "ko"

    db = DB()
    chat_id = chat_user.get_chat_id()
    user_id = chat_user.get_user_id()
    current_time = time.localtime()
    formatted_time = time.strftime("%Y-%m-%d %H-%M-%S", current_time)
    sql_str = f"INSERT INTO chatData VALUES('{chat_id}', '{user_id}', {ChatRoom.get_msg_num(chat_id)}, '{data_type}', {True}, '{send_data}', '{lang_code}', '{formatted_time}')"
    db.input(sql_str)

    log_str = f"{chat_user.get_user_id()}_{data_header}"
    logging.info(log_str)  # 로그 생성

    data_json_dic = {
        "user_id": chat_user.get_user_id(),
        "data_type": data_type,
        "data": send_data
    }

    #logging.info(data_json_dic)  # 로그 생성
    for user in ChatRoom.chat_room_all[chat_user.get_chat_id()]:
        sql_str = f"SELECT langCode FROM user WHERE id='{ChatRoom.chat_user_all[user].get_user_id()}'"
        result = db.output(sql_str)
        user_lang = result[0]  # 사용자 언어
        if user_lang != lang_code:  # 사용자 언어와 메시지의 언어가 다른 종류라면
            data_json_dic_tmp = copy.deepcopy(data_json_dic)
            data_json_dic_tmp['data'] = f"번역해야함... 일단 테스트"
            # todo 번역한 메시지도 DB에 넣어야함. 일단 다른 언어인지 파악하는거 만드는중
            data_json = json.dumps(data_json_dic_tmp)
        else:
            data_json = json.dumps(data_json_dic)
        await send_chunk(ChatRoom.chat_user_all[user], data_json)
        #await ChatRoom.chat_user_all[user].web_socket.send(data_json)  # 여기 자꾸 버그나는듯
    # await chat_user.websocket.send(f"ws_srv send data = {data}")
    db.close()


async def accept(websocket, path):  # 채팅방 웹소켓
    logging.info(f"클라이언트 접속. {websocket.remote_address}")  # 로그 생성
    data = await websocket.recv()  # 첫번째로 사용자 정보를 받기위해 연결 후 한번만 실행하는 코드
    data_arr = data.split(',')  # 처음으로 받은 데이터 사용자ID, 채팅방ID
    if len(data_arr) != 2:
        log_str = f"잘못된 접근.{websocket.remote_address}"
        print(log_str)
        logging.error(log_str)
        await websocket.send(f"ws_srv send data = {log_str}")
        return
    chat_user = ChatUser(data_arr[0], data_arr[1], websocket)  # 사용자 객체 생성. 사용자ID, 채팅방ID, 웹소켓 객체
    if chat_user.get_user_index() in ChatRoom.chat_user_all:
        log_str = f"이미 존재하는 식별 인덱스.{chat_user.get_user_index()}"
        print(log_str)
        logging.error(log_str)
    ChatRoom.chat_user_all[chat_user.get_user_index()] = chat_user  # 식별 인덱스를 키로 가지는 딕셔너리에 채팅 사용자 객체 저장
    if chat_user.get_chat_id() in ChatRoom.chat_room_all:  # 채팅방이 생성되어 있다면 추가
        ChatRoom.chat_room_all[chat_user.get_chat_id()].append(chat_user.get_user_index())  # 채팅방 id를 키로 가지는 딕셔너리에 사용자 객체 식별인덱스 저장
        logging.info(f"채팅방[{chat_user.get_chat_id()}]에 사용자 객체 추가.[{chat_user.get_user_index()}].")  # 로그 생성
    else:  # 채팅방이 없다면 생성
        ChatRoom.chat_room_all[chat_user.get_chat_id()] = [chat_user.get_user_index()]
        ChatRoom.set_msg_num(chat_user.get_chat_id())  # 채팅방 메시지 번호 초기화
        logging.info(f"채팅방[{chat_user.get_chat_id()}] 생성, 사용자 객체 추가.[{chat_user.get_user_index()}].")  # 로그 생성

    #print(f"chat_room_all={ChatRoom.chat_room_all}")
    #print(f"chat_user_all={ChatRoom.chat_user_all}")

    # 입장한 채팅방 이전기록 불러오기
    db = DB()
    sql_str = f"SELECT * FROM chatData WHERE roomId='{chat_user.get_chat_id()}' ORDER BY chatNumber ASC"
    result = db.output(sql_str)
    # todo 유저에 해당하는 언어로 번역된 메시지를 불러오고 없으면 번역해서 DB에 넣고 유저에게도 뿌려주게 바꿔야함.
    for msg_data in result:
        data_json_dic = {
            "user_id": msg_data[1],
            "data_type": msg_data[3],
            "data": msg_data[5]
        }
        data_json = json.dumps(data_json_dic)
        await send_chunk(chat_user, data_json)
        #await chat_user.web_socket.send(data_json)
        #log_str = data_json_dic
        #logging.debug(log_str)
    db.close()

    while True:
        try:
            data = await websocket.recv()
            data_length = int(data.split(',')[0])
            send_data = data[len(data.split(',')[0])+1:]  # 데이터에 ','문자가 있을경우 잘리는 것을 방지하기 위함
            log_str = f"첫번째 데이터 {data}"
            logging.debug(log_str)
            while len(send_data) < data_length:
                send_data += await websocket.recv()
            await msg_process(chat_user, send_data)
        except websockets.exceptions.ConnectionClosedOK:
            #print(f"클라이언트 끊김 {chat_user.get_user_info()}")
            ChatRoom.chat_room_all[chat_user.get_chat_id()].remove(chat_user.get_user_index())  # 채팅방 리스트에 끊긴 클라이언트 인덱스 제거
            del ChatRoom.chat_user_all[chat_user.get_user_index()]  # 식별 인덱스를 키로 가지는 딕셔너리에 채팅 사용자 객체 제거
            #print(f"클라이언트 제거완료")
            logging.info(f"클라이언트의 접속 종료로 채팅방[{chat_user.get_chat_id()}]에서 사용자 객체가 제거.[{chat_user.get_user_index()}]")  # 로그 생성
            break


async def run_server():
    async with websockets.serve(accept, "192.168.0.8", 30088):
        await asyncio.Future()


if __name__ == "__main__":
    try:
        log_str = "서버 개방"
        logging.info(log_str)  # 로그 생성
        #print(log_str)
        asyncio.run(run_server())
    except KeyboardInterrupt:
        log_str = "종료 감지"
        logging.info(log_str)  # 로그 생성
        #print(log_str)
    finally:
        log_str = "종료"
        logging.info(log_str)  # 로그 생성
        #print(log_str)
