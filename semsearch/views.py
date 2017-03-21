from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from models import Document, Index
from forms import DocumentForm
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
# from shutil import copyfile
from os.path import dirname, realpath
import sys
import subprocess
import re
import json
import operator
import cv2
import math
from time import time
import json,os


def calctime(num):
    if not os.path.exists("data.txt"):
        one_file = "--input_files=" + str(cwd) + "/media/frames/frame"+num+".jpg"
        no_file = "--input_files=" + str(cwd) + "/media/frames/"
        code = "bazel-bin/im2txt/run_inference "
        checkpoint_path = "--checkpoint_path=" + str(cwd) + "/im2txt/model/train "
        vocab_file = "--vocab_file=" + str(cwd) + "/im2txt/data/mscoco/word_counts.txt "
        input_files = "--input_files=" + str(cwd) + "/media/frames/frame*.jpg"

        t0 = time()
        a = subprocess.check_output(code + checkpoint_path + vocab_file + no_file, cwd=str(cwd) + "/im2txt/",
                                    shell=True)
        t1 = time()
        a = subprocess.check_output(code + checkpoint_path + vocab_file + one_file, cwd=str(cwd) + "/im2txt/",
                                    shell=True)
        t2 = time()
        ltime = t1-t0
        ptime = t2-t1 - ltime
        print (ltime,ptime)    
        data = [ltime,ptime]
        with open('data.txt', 'w') as outfile:
            json.dump(data, outfile)
        return ltime,ptime
    else:
        x =0
        with open('data.txt', 'r') as outfile:
            x = json.load(outfile)
        return x[0],x[1]





cwd = dirname(dirname(realpath(__file__)))
def home(request):
    tag = "hello"
    video = "hello"
    context = {
        "tag": tag,
        "video": video
    }
    
    return render(request, "videotube.html", context)

def video(request, video_id):
    a = Index.objects.get(video_id=video_id)

    name = a.name
    jsonDec = json.decoder.JSONDecoder()
    sorted_inverted = jsonDec.decode(a.invertedIndex)
    images_captured = jsonDec.decode(a.images)
    print sorted_inverted
    location = "../../media/uploads/" + name
    context = {
        "video_id":video_id,
        "name" : name,
        "location": location,
        "sorted_inverted": sorted_inverted,
    }
    if request.GET.get('position', "") != "":
        position = request.GET.get('position', "")
        context["img_loc"] = "../../media/frames/frame%s.jpg" % position
        context["position"] = convertMillis(position)
        context["img_desc"] = images_captured[position]
        return render(request, 'videotube.html', context)

    if request.POST.get('search',"") == "":
        return render(request, 'videotube.html', context)

    if request.method == 'POST' and request.POST.get('search',"") != "":
        if "after" in request.POST.get('search',"") or "before" in request.POST.get("search",""):
            res = temporal_modality(request.POST.get("search",""), video_id)
            if res == -1:
                context["not_valid"] = "the input string was not found in the semantic words"
            else:
                context["search_result"] = res
        else:
            res = boolean_modality(request.POST.get("search",""), video_id)
            print res
            if res == -1:
                context["not_valid"] = "the input string was not found in the semantic words"
            elif res == 0 :
                context["not_valid"] = "there was two NOT's present. Only a boolean query allowed."
            else:
                context["search_result"] = res
        return render(request, 'videotube.html', context)

def upload(request):
    name = ""
    if request.method == 'POST' and request.POST.get('search',"") == "":
        context = {}
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            newDoc = Document(docfile=request.FILES.get('docfile',""))
            name = form.cleaned_data['docfile'].name
            newDoc.save()
        documents = Document.objects.all()
        if name != "":
            location = "../media/uploads/"+ name
            s = convert_video_to_frame(cwd+ "/media/uploads/"+ name)
            sorted_inverted = model_to_inverted_index(s)
            print sorted_inverted
            convert_from_mili(sorted_inverted)
            val = 1
            if len(Index.objects.filter()) > 0:
                val = len(Index.objects.filter()) + 1
            b = Index(invertedIndex=json.dumps(sorted_inverted),name=name,video_id=val,images=json.dumps(s))
            vid_id = b.video_id
            b.save()
            return redirect("/video/%s" % vid_id)
        return render(request, 'home.html', context)

    if request.method == 'GET':
        return render(request, 'upload.html')

def convert_from_mili(index):
    for i, (key, value) in enumerate(index):
        a = []
        for j in xrange(len(value)):
            a.append(value[j])
            value[j] = convertMillis(value[j])
        index[i] = (key, zip(value, a))


def convert_video_to_frame(name):
    subprocess.check_output("rm -rf ./media/frames/*",shell=True)
    vidCap = cv2.VideoCapture(name)
    frameRate = vidCap.get(cv2.cv.CV_CAP_PROP_FPS)
    captureIntervals = 5
    s = {}
    count = 0
    m = 0
    while (vidCap.isOpened()):
        frameId = vidCap.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)  # starting position is 0.. returns current frame position
        success, image = vidCap.read()
        if (success != True):
            break
        if ((frameId % math.floor(captureIntervals * frameRate)) == 0):  # 1 frame in 1 sec
            millisec = vidCap.get(cv2.cv.CV_CAP_PROP_POS_MSEC)
            count+=1
            print 'Read a new frame : id ',frameId,"milli", str(millisec),"num :",str(count)
            
            m = millisec
            cv2.imwrite("./media/frames/frame%d.jpg" % int(millisec), image)  # save frame as JPEG file
    vidCap.release()
    
    loadtime,dt = calctime(str(int(m)))
    print "\n\nEstimated time :",loadtime + count*dt,'\n'    
    
    return caption_image()

#
# (0,1,4,5,8,9) 0: image file name 1: best caption
def caption_image():


    code = "bazel-bin/im2txt/run_inference "
    checkpoint_path = "--checkpoint_path=" + str(cwd) + "/im2txt/model/train "
    vocab_file = "--vocab_file=" + str(cwd) + "/im2txt/data/mscoco/word_counts.txt "
    input_files = "--input_files=" + str(cwd) + "/media/frames/frame*.jpg"
    
    t0 = time()
    a = subprocess.check_output(code + checkpoint_path + vocab_file + input_files, cwd=str(cwd) + "/im2txt/",
                                shell=True)
    t1 = time()
    print "\n\nActual time :",t1-t0,'\n\n'
    b = a.split("\n")
    s = {}

    for i in range(0,len(b)-1,4):
        if (b[i] != ''):
            millisec = int(re.search(r'\d+', b[i]).group())
            result = re.search('0\) (.*) \(', b[i+1])
            s[str(millisec)] = result.group(1)

    # result = re.search('0\) (.*) \(', a.split("\n")[1])
    # print result.group(1)
    # s[str(millisec)] = result.group(1)
    print s
    return s

def word_split(text, frameno):
    print text
    word_list = []
    wcurrent = []

    for i, c in enumerate(text):
        if c.isalnum():
            wcurrent.append(c)
        elif wcurrent:
            word = u''.join(wcurrent)
            word_list.append((frameno, word))  # location of the word in the document
            wcurrent = []

    if wcurrent:
        word = u''.join(wcurrent)
        word_list.append((frameno, word))
    return word_list


_WORD_MIN_LENGTH = 2
_STOP_WORDS = ["that", "were","and"]


def words_cleanup(words):
    cleaned_words = []
    for index, word in words:
        if len(word) < _WORD_MIN_LENGTH or word in _STOP_WORDS:
            continue
        cleaned_words.append((index, word))
    return cleaned_words


def words_normalize(words):
    normalized_words = []
    for index, word in words:
        wnormalized = word.lower()
        normalized_words.append((index, wnormalized))
    return normalized_words


def word_index(text, frameno):
    words = word_split(text, frameno)
    words = words_normalize(words)
    words = words_cleanup(words)
    return words


def inverted_index(text, frameno,inverted):
    for index, word in word_index(text, frameno):
        locations = inverted.setdefault(word,[])  # returns value to the key "word" and if word doesn't exist then [] returned
        locations.append(index)


def model_to_inverted_index(s):
    inverted = {}
    for key, value in s.iteritems():
        inverted_index(value, key,inverted)
    return sorted(inverted.items(), key=operator.itemgetter(0))


def sorted_inverted_index_bsearch(alist, item):
    first = 0
    last = len(alist) - 1
    found = False
    while first <= last and not found:
        midpoint = (first + last) // 2
        if alist[midpoint][0] == item:
            found = True
        else:
            if item < alist[midpoint][0]:
                last = midpoint - 1
            else:
                first = midpoint + 1

    if found:
        return alist[midpoint]
    else:
        return -1


def boolean_modality(text, video_id):
    text = text.split(" ")
    a = Index.objects.get(video_id=video_id)
    jsonDec = json.decoder.JSONDecoder()
    sorted_inverted = jsonDec.decode(a.invertedIndex)
    avoid_elements = ()
    not_index = -1
    try:
        not_index = text.index("NOT")
        avoid_elements = sorted_inverted_index_bsearch(sorted_inverted, text[not_index + 1])
        if avoid_elements != -1:
            print "Avoid Elements: "
            print avoid_elements
            avoid_elements = change(avoid_elements[1])
            print "after change() on avoid elements: "
            print avoid_elements
        print "old text \n"
        print text
        text[not_index:not_index + 2] = [' '.join(text[not_index:not_index + 2])]
        print text
    except ValueError:
        pass

    try:
        print text.index("NOT")
        print "2 NOT is not allowed"
        return 0
    except ValueError:
        pass

    if len(text) == 1:
        A = change(sorted_inverted_index_bsearch(sorted_inverted, text[0])[1])
        B = []
        for i in A:
            B.append(convertMillis(i))
        return B
    if text[1] == 'AND':
        if avoid_elements == -1:
            if not_index > 1:
                return change(sorted_inverted_index_bsearch(sorted_inverted, text[0])[1])
            else:
                return change(sorted_inverted_index_bsearch(sorted_inverted, text[2])[1])
        elif any(avoid_elements):
            if not_index > 1:
                A = change(sorted_inverted_index_bsearch(sorted_inverted, text[0])[1])
                if A == -1:
                    return -1
            else:
                A = change(sorted_inverted_index_bsearch(sorted_inverted, text[2])[1])
                if A == -1:
                    return -1
            list_in_mili = list(set(set(A) - set(avoid_elements)))
            d = []
            for i in list_in_mili:
                d.append(convertMillis(i))
            return d

        else:
            A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
            B = sorted_inverted_index_bsearch(sorted_inverted, text[2])
            if A == -1 or B == -1:
                return -1
            print "A:\n"
            print A
            A = change(A[1])
            print A
            B = change(B[1])
            s = list(set(A) & set(B))
            d = []
            for i in s:
                d.append(convertMillis(i))
            return d

    if text[1] == 'OR':
        if avoid_elements == -1:
            if not_index > 1:
                return change(sorted_inverted_index_bsearch(sorted_inverted, text[0])[1])
            else:
                return change(sorted_inverted_index_bsearch(sorted_inverted, text[2])[1])
        elif any(avoid_elements):
            if not_index > 1:
                A = change(sorted_inverted_index_bsearch(sorted_inverted, text[0])[1])
                if A == -1 :
                    return -1
            else:
                A = change(sorted_inverted_index_bsearch(sorted_inverted, text[2])[1])
                if A == -1 :
                    return -1
            list_in_mili_or = list(set(A) - set(avoid_elements))
            d = []
            for i in list_in_mili_or:
                d.append(convertMillis(i))
            return d

        else:
            A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
            B = sorted_inverted_index_bsearch(sorted_inverted, text[2])
            if A == -1 or B == -1:
                return -1
            A = change(A[1])
            B = change(B[1])
            s = list(set(A) | set(B))
            d = []
            for i in s:
                d.append(convertMillis(i))
            print d
            return d


def convertMillis(millis):
    millis = int(millis)
    seconds = (millis / 1000) % 60
    minutes = (millis / (1000 * 60)) % 60
    hours = (millis / (1000 * 60 * 60)) % 24
    return  str(hours) + " hours :" + str(minutes) + " mins :" + str(seconds) + " secs"


def temporal_modality(text, video_id):
    text = text.split(" ")
    a = Index.objects.get(video_id=video_id)
    jsonDec = json.decoder.JSONDecoder()
    sorted_inverted = jsonDec.decode(a.invertedIndex)
    if text[1] == "before":
        A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
        B = sorted_inverted_index_bsearch(sorted_inverted, text[2])
        if A == -1 or B == -1:
            return -1
        temporal = []
        for a in change(A[1]):
            for b in change(B[1]):
                if a < b:
                    temporal.append((convertMillis(a), convertMillis(b)))
        return temporal

    if text[1] == "after":
        A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
        B = sorted_inverted_index_bsearch(sorted_inverted, text[2])
        if A == -1 or B == -1:
            return -1
        temporal = []
        for a in change(A[1]):
            for b in change(B[1]):
                if a > b:
                    temporal.append((convertMillis(a), convertMillis(b)))
        return temporal

def change(a):
    b = []
    for i in a:
        b.append(int(i[1]))
    return b
#
# if __name__ == "__main__":
#     sorted_inverted = model_to_inverted_index()
#     print sorted_inverted
#     # boolean_modality(u' '.join(sys.argv[1:]))
#     temporal_modality(u' '.join(sys.argv[1:]))
