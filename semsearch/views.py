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
    location = "../../media/uploads/" + name
    context = {
        "sorted_inverted" : sorted_inverted,
        "name" : name,
        "location": location
    }
    if request.POST.get('search',"") == "":
        return render(request, 'home.html', context)

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
        return render(request, 'home.html', context)

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
            sorted_inverted = model_to_inverted_index(cwd+ "/static/media_root/uploads/"+ name)
            print sorted_inverted
            convert_from_mili(sorted_inverted)
            val = 1
            if len(Index.objects.filter()) > 0:
                val = len(Index.objects.filter()) + 1
            b = Index(invertedIndex=json.dumps(sorted_inverted),name=name,video_id=val)
            vid_id = b.video_id
            b.save()
            return redirect("/video/%s" % vid_id)
        return render(request, 'home.html', context)

    if request.method == 'GET':
        return render(request, 'upload.html')

def convert_from_mili(index):
    for i, (key, value) in enumerate(index):
        for j in xrange(len(value)):
            value[j] = convertMillis(value[j])
            print value[j]
        index[i] = (key, value)
    print index

def start_i2t(name):
    subprocess.check_output("python video_to_frame.py %s" % name,cwd= str(cwd) + "/neuraltalk2/" , shell=True)
    a = subprocess.check_output(
        "th eval.lua -model checkpoint_v1_cpu/model_id1-501-1448236541.t7_cpu.t7  -image_folder frames/ -num_images -1 -gpuid -1",
        cwd= str(cwd) + "/neuraltalk2/", shell=True)
    print a
    content = a.split("\n")
    number_of_images = re.search('[0-9]+', content[2]).group()
    s = {}
    for i in xrange(5, len(content) - 1, 3):  # 5,8,11
        milisec_of_frame = re.search('[0-9]+', content[i - 1].split('"')[1]).group()
        s[milisec_of_frame] = content[i][9:]
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
_STOP_WORDS = ["that", "were"]


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
        locations = inverted.setdefault(word,
                                        [])  # returns value to the key "word" and if word doesn't exist then [] returned
        locations.append(index)


def model_to_inverted_index(file):
    inverted = {}
    s = start_i2t(file)
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
        text[not_index:not_index + 2] = [' '.join(text[not_index:not_index + 2])]
    except ValueError:
        pass

    try:
        print text.index("NOT")
        print "2 NOT is not allowed"
        return 0
    except ValueError:
        pass

    if text[1] == 'AND':
        if avoid_elements == -1:
            if not_index > 1:
                return sorted_inverted_index_bsearch(sorted_inverted, text[0])[1]
            else:
                return sorted_inverted_index_bsearch(sorted_inverted, text[2])[1]
        elif any(avoid_elements):
            if not_index > 1:
                A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
                if A == -1:
                    return -1
            else:
                A = sorted_inverted_index_bsearch(sorted_inverted, text[2])
                if A == -1:
                    return -1
            print list(set(set(A[1]) - set(avoid_elements[1])))

        else:
            A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
            B = sorted_inverted_index_bsearch(sorted_inverted, text[2])
            if A == -1 or B == -1:
                return -1
            return list(set(A[1]) & set(B[1]))

    if text[1] == 'OR':
        if avoid_elements == -1:
            if not_index > 1:
                return sorted_inverted_index_bsearch(sorted_inverted, text[0])[1]
            else:
                return sorted_inverted_index_bsearch(sorted_inverted, text[2])[1]
        elif any(avoid_elements):
            if not_index > 1:
                A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
                if A == -1 :
                    return -1
            else:
                A = sorted_inverted_index_bsearch(sorted_inverted, text[2])
                if A == -1 :
                    return -1
            return list(set(A[1]) - set(avoid_elements[1]))

        else:
            A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
            B = sorted_inverted_index_bsearch(sorted_inverted, text[2])
            if A == -1 or B == -1:
                return -1
            s = set(A[1]) | set(B[1])
            return list(s)


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
        for a in A[1]:
            for b in B[1]:
                if a < b:
                    temporal.append((a, b))
        return temporal

    if text[1] == "after":
        A = sorted_inverted_index_bsearch(sorted_inverted, text[0])
        B = sorted_inverted_index_bsearch(sorted_inverted, text[2])
        if A == -1 or B == -1:
            return -1
        temporal = []
        for a in A[1]:
            for b in B[1]:
                if a > b:
                    temporal.append((a, b))
        return temporal

#
# if __name__ == "__main__":
#     sorted_inverted = model_to_inverted_index()
#     print sorted_inverted
#     # boolean_modality(u' '.join(sys.argv[1:]))
#     temporal_modality(u' '.join(sys.argv[1:]))