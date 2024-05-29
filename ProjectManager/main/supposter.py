from datetime import timedelta
from unidecode import unidecode
import random, hashlib, PIL, os

def randomString(length):
    b = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    s = ""
    for length in range(0, length):
        s += random.choice(b)
    return s

def sha256_hash(data):
    sha256 = hashlib.sha256()
    sha256.update(data.encode('utf-8'))
    hashed_data = sha256.hexdigest()
    return hashed_data

def encodePassword(salt, password):
    data = salt + password
    return sha256_hash(data)

def remove_diacritics(text):
    return unidecode(text)

def is_image(file):
    try:
        PIL.Image.open(file)
        return True
    except Exception as e:
        return False
    
def is_pdf(file_path):
    if not file_path.lower().endswith('.pdf'):
        return False
    
    if not os.path.isfile(file_path):
        return False

    try:
        with open(file_path, 'rb') as file:
            header = file.read(5)
            if header == b'%PDF-':
                return True
            else:
                return False
    except IOError:
        return False
    
def sortChat(messages, images, files):
    messages = list(messages)
    images = list(images)
    files = list(files)
    chats = messages + images + files

    chats.sort(key=lambda x:x.Send_at, reverse=True)
    for c in chats:
        chats[chats.index(c)] = c.mark()
    return chats

def arrayDates(start_date, end_date):
    dates_list = []
    dates_list_limit = []

    while start_date <= end_date:
        dates_list.append(start_date.strftime("%Y-%m-%d"))
        dates_list_limit.append(start_date.strftime("%d/%m"))
        start_date += timedelta(days=1)

    return dates_list, dates_list_limit, len(dates_list)

def getStatus(today, beginDay, endDay, progress):
    if today < beginDay:
        return "Chưa tới"
    elif beginDay <= today <= endDay:
        if progress == 100:
            return "Hoàn thành"
        else:
            return "Đang thực hiện"
    elif today > endDay:
        if progress == 100:
            return "Hoàn thành"
        else:
            return "Chậm tiến độ"

def reorderTask(tasks):
    newTasks = []
    for t in tasks:
        if t["Status"] == "Chậm tiến độ":
            newTasks.append(t)
    for t in tasks:
        if t["Status"] == "Đang thực hiện":
            t["Status"] = "Chưa hoàn thành"
            newTasks.append(t)
    return newTasks