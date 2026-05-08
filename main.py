import keyboard
import cv2
import face_recognition
from skimage import io
from scipy.spatial import distance
import os
import sys
import requests
import psutil
import win32gui
from datetime import datetime
import threading
import time
import socket

URL = "http://127.0.0.1:8000/"


def get_path(relative_path: str):
    """Получает абсолютный путь к файлу, учитывая режим EXE и разработки"""
    try:
        base_path = sys._MEIPASS  # type: ignore
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def upadate_info():
    global sp_anti_app, sp_anti_website, t1
    while t1:
        try:
            sp_anti_app = requests.get(
                URL + f"sp_anti_app/{socket.gethostname()}"
            ).json()
            sp_anti_website = requests.get(
                URL + f"sp_anti_website/{socket.gethostname()}"
            ).json()
            t1 = True
            time.sleep(60)
        except:
            t1 = False


def not_rasp_player(name_game):
    response = requests.post(
        URL + "not_rasp_player",
        json=[name_game, socket.gethostname()],
        headers={"Content-Type": "application/json"},
    )


def who_played(name_game: str, img):
    
    try:
        # face_recognition автоматически детектирует лица и возвращает список 128-D эмбеддингов
        face_encodings = face_recognition.face_encodings(img,model="hog")
        if len(face_encodings) == 0:
            face_encodings = face_recognition.face_encodings(img,model="cnn")
            if len(face_encodings) == 0:
                not_rasp_player(name_game)
                return None
        face1 = face_encodings[0]
    except Exception:
        not_rasp_player(name_game)
        return None
        
    data = requests.get(URL + "rasp_group").json()
    today = datetime.today()
    group_id = get_group_id() 

    if group_id == 0:
        not_rasp_player(name_game)
        return None
        
    print(group_id)
    data = requests.get(URL + f"student/{group_id}").json()
    
    for i in data:
        # Сравнение с сохранёнными эмбеддингами из БД (список float)
        a = distance.euclidean(face1, i[1])
        if a < 0.6:
            k = i[0]
            d = requests.get(URL + f"who_played/{k}/{name_game}").json()
            return d[0]
            
    not_rasp_player(name_game)
    return None


def close_app():
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            for name_app in sp_anti_app:
                if name_app.lower() in proc.info["name"].lower():
                    process = psutil.Process(proc.info["pid"])
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()
                    mes(name_app)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Ошибка при завершении процесса: {e}")
            continue


def get_active_window_title():
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())


def close_website():
    title = get_active_window_title().replace(" ", " ").lower()
    for name_website in sp_anti_website:
        if name_website.lower() in title:
            keyboard.press("ctrl")
            keyboard.press("w")
            keyboard.release("ctrl")
            keyboard.release("w")
            mes(name_website)
            break


def mes(name_game: str):
    ret, img = web_cam.read()
    if not ret:
        return -1
    who_played(name_game, img)


def get_group_id():
    data = requests.get(URL + "rasp_group").json()
    today = datetime.today()
    weekday_num = str(today.weekday())
    current_time = datetime.now().time()
    group_id = 0 
    for i in data:
        try:     
            if weekday_num in i[2].keys():
                r = i[2][weekday_num].replace("–","-")
                if(
                    r.split("-")[0].split(":")[0]
                    < str(current_time).split(":")[0]
                    < r.split("-")[1].split(":")[0]
                    or (
                        r.split("-")[0].split(":")[0]
                        == str(current_time).split(":")[0]
                        and r.split("-")[0].split(":")[1]
                        <= str(current_time).split(":")[1]
                    )
                    or (
                        r.split("-")[1].split(":")[0]
                        == str(current_time).split(":")[0]
                        and int(r.split("-")[0].split(":")[1])
                        <= int(str(current_time).split(":")[1])
                    )
                ):
                    group_id = i[0]
                    break
        except Exception as e:
            print(e)
    return group_id


def send_pris():
    ret, img = web_cam.read()

    try:
        face_encodings = face_recognition.face_encodings(img,model="hog")
        if len(face_encodings) == 0:
            face_encodings = face_recognition.face_encodings(img,model="cnn")
            if len(face_encodings) == 0:
                return True
        face1 = face_encodings[0]
    except Exception as e:
        print(e)
        return True
        
    data = requests.get(URL + "rasp_group").json()
    today = datetime.today()
    group_id = get_group_id()        
    
    if group_id == 0:
        return True

    data = requests.get(URL + f"student/{group_id}").json()
    for i in data:
        a = distance.euclidean(face1, i[1])
        if a < 0.6:
            mesag = i[0]
            requests.post(
                URL + "upload",
                json=mesag,
                headers={"Content-Type": "application/json"},
            )
            print(2)
            return False
    print(3)
    return True


""" Инициализация и главный цикл """
web_cam = cv2.VideoCapture(0)

# dlib инициализация удалена. face_recognition загружает модели автоматически при первом вызове.
t = True
t1 = True
sp_anti_app = []
sp_anti_website = []

thr1 = threading.Thread(target=upadate_info, daemon=True)
thr1.start()

while True:
    close_website()
    close_app()
    if t:
        print(1)
        t = send_pris()
    if not t1:
        thr1 = threading.Thread(target=upadate_info, daemon=True)
        thr1.start()
    time.sleep(1)