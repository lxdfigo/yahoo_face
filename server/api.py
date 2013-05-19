import Image
import urllib2
from facepp import API, File
import os
import flickr_api
from config import *


def getFaceBox(face, img_width, img_height) :
    border = 5
    x = face['position']['center']['x']
    y = face['position']['center']['y']
    x = img_width * 0.01 * x
    y = img_height * 0.01 * y
    
    width = face['position']['width'] * img_width * 0.01
    height = face['position']['height'] * img_height * 0.01
    
    x1 = int(x-width/2) - border
    y1 = int(y-height/2) - border
    
    x2 = int(x+width/2) + border
    y2 = int(y+width/2) + border
    
    box = (x1,y1,x2,y2)
    return box
def flickrSaveInfo(token, secret, username):
    text = '%s\n%s\n%s\n%s'%(flickr_key, flickr_secret, token, secret)
    path = './verifiers/%s.verifier'%username
    f = open(path, 'w')
    f.write(text)
    f.close()
    return True


def flickrLoadInfo(username):
    return './verifiers/%s.verifier'%username

def fOauth(username):
    flickr_api.set_keys(api_key = flickr_key, api_secret = flickr_secret)
    a = flickr_api.auth.AuthHandler.load(flickrLoadInfo(username))
    flickr_api.set_auth_handler(a)


def Oauth():   
    return API(API_KEY, API_SECRET)

face_api = Oauth() 


def get_photo_files(username = 'YahooHack2013') :
    fOauth(username)
    user = flickr_api.Person.findByUserName(username)
    photos = user.getPhotos()
    photo_files = []
    for photo in photos :
        photo_files.append(photo.getPhotoFile())
    return photo_files


def getsmallFace(detect_res, pic_path, border = 10, default_size = (150,150)) :
    x = detect_res['face'][0]['position']['center']['x']
    y = detect_res['face'][0]['position']['center']['y']
    x = detect_res['img_width'] * 0.01 * x
    y = detect_res['img_height'] * 0.01 * y
    
    width = detect_res['face'][0]['position']['width'] * detect_res['img_width'] * 0.01
    height = detect_res['face'][0]['position']['height'] * detect_res['img_height'] * 0.01
    
    x1 = int(x-width/2) - border
    y1 = int(y-height/2) - border
    
    x2 = int(x+width/2) + border
    y2 = int(y+width/2) + border
    
    box = (x1,y1,x2,y2)
    
    #Download picture file from flickr
    filename = pic_path[pic_path.rfind('/')+1:]
    if not os.path.isfile(filename):
        print pic_path
        req = urllib2.Request(pic_path)
        response = urllib2.urlopen(req)
        pic = response.read()
        f = file(filename,'w')
        f.write(pic)
        f.close()
        print 'download ',pic_path
    im = Image.open(filename)
    xim = im.crop(box)
    p = xim.resize(default_size)
    # save as XXXX.(picture format)
    path = './static/avatars/'+detect_res['face'][0]['face_id'] + pic_path[pic_path.rfind('.'):]
    p.save(path)

def cut_faces(photo_files = []) :
    if len(photo_files) <= 0 : return []
    face_ids = []
    for f in photo_files :
        res = face_api.detection.detect(url = f)
        if len(res['face']) == 0 :
            continue
        face_ids.append('/static/avatars/'+res['face'][0]['face_id'] + f[f.rfind('.'):])
        getsmallFace(res,f)
    return face_ids 


def add_faces_to_person (username = 'YahooHack2013', face_id_list = [], defaultGroupName = 'yahoohack', defaultFaceSetName = 'yahoohack_faceset') :
    try :
        person = face_api.person.get_info(person_name = username)
        person_id = person['person_id']
    except Exception,ex :
        person = face_api.person.create(person_name = username, group_name = defaultGroupName)
        person_id = person['person_id']
    if len(face_id_list) <= 0 :
        print 'Warning,face_id_list empty'
        return
    face_ids_str = ','.join(face_id_list)
    res_person_add_face = face_api.person.add_face(person_id = person_id, face_id = face_ids_str)
    res_faceset_add_face = face_api.faceset.add_face(faceset_name = defaultFaceSetName, face_id = face_ids_str)
    
    if not res_person_add_face.get('success',False) or not res_faceset_add_face.get('success',False) :
        return False
    return True

def train(defaultGroupName = 'yahoohack', defaultFaceSetName = 'yahoohack_faceset') :
    # asynchronous
    identify_session_id = face_api.train.identify(group_name = defaultGroupName)
    search_session_id = face_api.train.search(faceset_name = defaultFaceSetName)
    return identify_session_id, search_session_id

def get_Train_Result(identify_session_id, search_session_id) :
    identify_res = face_api.info.get_session(session_id = identify_session_id)
    search_res = face_api.info.get_session(session_id = search_session_id)
    print 'identify\t%s\t\tsearch\t%s' % (identify_res['status'], search_res['status'])
    return identify_res['result'], search_res['result']



def face_search(photo_url = '', photo_img = '', defaultFaceSetName = 'yahoohack_faceset') :
    if photo_url == '' and photo_img == '':
        print 'photo is empty!'    
        return
    if photo_img != '' :
        res = face_api.detection.detect(img = File(photo_img))
    if photo_url != '' :
        res = face_api.detection.detect(url = photo_url)
    if not res['face']: return []
    face_id = res['face'][0]['face_id']
    search_res = face_api.recognition.search(key_face_id = face_id, faceset_name = defaultFaceSetName, count = 10)
    faces_res = search_res['candidate']
    face_ids = [face['face_id'] for face in faces_res]
    face_ids_str = ','.join(face_ids)

    face_info = face_api.info.get_face(face_id = face_ids_str)['face_info']

    person_names = {} 
    for face in face_info :
        if len(face['person']) > 0 :
            person_names[face['face_id']] = face['person'][0]['person_name']

    person_name_list = []
    for face_id in face_ids :
        if person_names.get(face_id,None) != None :
            person_name_list.append(person_names[face_id])
    print person_name_list
    return person_name_list


def add_people2flickrPhoto(photo_img = '', photo_title = '', defaultFaceSetName = 'yahoohack_faceset', username2user_id = {}, username='') :
    '''
    1.upload a photo to flickr
    2.get faces box
    3.add face to photo
    '''
    fOauth(username)
    upload_photo = flickr_api.upload(photo_file = photo_img, title = photo_title)
    photo_id = upload_photo['id']
    add_geo2photo(upload_photo, 20.1345,31.214)
    faces_box = face_identify(photo_img = photo_img)
    face2user_id = {}
    '''
    for face_id in faces_box :
        person_name = face_api.info.get_face(face_id = face_id)
        #['face_info'][0]['person'][0]['person_name']
        print person_name
    '''
    person_seen = {}
    for face_id in faces_box :
        person_name, box = faces_box[face_id]
        x,y,w,h = box[0], box[1], box[2] - box[0], box[3] - box[1]
        print x,y,w,h
        print person_name
        if person_seen.get(person_name,False) == False :
            print username2user_id[person_name]
            try :
                upload_photo.addPerson(user_id = username2user_id[person_name], person_x = x,person_y = y,person_w = w, person_h = h)
            except Exception,ex :
                print username2user_id[person_name]
                print ex
            person_seen[person_name] = True
    #return photo_id
def add_geo2photo(photo, lat, lon) :
    photo.setLocation(lat = lat,lon = lon)



def face_identify(photo_url = '', photo_img = '', defaultGroupName = 'yahoohack') :
    if photo_url == '' and photo_img == '':
        print 'photo is empty!'    
        return
    if photo_img != '' :
        res = face_api.recognition.identify(group_name = defaultGroupName, img = File(photo_img))
        img = Image.open(photo_img)
        img_width, img_height = img.size
    if photo_url != '' :
        #???
        res = face_api.recognition.identify(group_name = defaultGroupName, url = photo_url)
    
    faces = res['face']
    faces_confidence = [ (face['candidate'][0]['confidence'],face) for face in faces]
    sorted(faces_confidence, key=lambda q: -q[0])
    faces = [item[1] for item in faces_confidence]
    #print faces
    faces_box = {}
    for face in faces :
        print face
        person_name = face['candidate'][0]['person_name']
        box = getFaceBox(face,img_width,img_height)
        if faces_box.get(face['face_id'],None) == None :
            faces_box[face['face_id']] = person_name, box
    return faces_box
