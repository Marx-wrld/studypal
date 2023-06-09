from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse 
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm

# Create your views here.

# rooms = [
#     {'id': 1, 'name' : 'Lets learn Python'},
#     {'id': 2, 'name' : 'Design and Code'},
#     {'id': 3, 'name' : 'Frontend Developers'},
#     {'id': 4, 'name' : 'Backend Developers'}
# ]

def loginPage(request):

    page = 'login'

    #Saving user details after they are already logged in
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email) #checking if this user exists if not we want to throw in an error
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, email=email, password=password) #authenticate either throws in an error or throws in a user object that matches these credentials.

        if user is not None:
            login(request, user) 
            return redirect('home')
            #login adds this session into our database and then inside our browser
        else:
            messages.error(request, 'Email OR Password does not exist')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')

def registerPage(request):
    form = MyUserCreationForm() 

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration!')
            
    return render(request, 'base/login_register.html', {'form': form})

def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else '' #q is going to be equal to whatever we passed in the url
    
    rooms = Room.objects.filter(
        Q(topic__name__icontains = q) |
        Q(name__icontains = q) |
            Q(description__icontains = q) 
        )
    #Dynamic searches
    #going to the model file and getting the topic, and querying upwards to the parent(__)
    #icontains will make sure that whatever value we have in our topic name atleast contains whats in here(topic)

    topics = Topic.objects.all()[0:5] #limits our home page so that we can only view 5 topics at a time

    room_count = rooms.count() #You can also use the python len() method
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q)) #grabbing all recent user messages

    context = {'rooms':rooms, 'topics': topics, 'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)#Passing in a dictionary and specifying the value names

def room(request, pk): #pk-primary key
    #In order to get the pk value, later on we'll use this primary key to query the database but for now we'll use the variable rooms to create some logic
    room = Room.objects.get(id=pk)
    room_messages = room.message_set.all() #Give me the set of messages related to this room
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user = request.user,
            room = room,
            body = request.POST.get('body') #passing the body from room.html in the authenticate section
        )
        room.participants.add(request.user) #adding participants to the room
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 'participants': participants}

    return render(request, 'base/room.html', context)

def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all() # getting all the children of a specific object by using '_set.all()' 
    room_messages = user.message_set.all() 
    topics = Topic.objects.all() # we need to access all Topics inside of our profile component
    context = {'user': user, 'rooms': rooms, 'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)

#restricting some pages regardless of whether they are logged in or logged out
@login_required(login_url='login')
def createRoom(request): 
    form = RoomForm()
    topics = Topic.objects.all()

    if request.method == 'POST':
        #if topic is present, the get function will be used else, the create function will be used and will update our db
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        
        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        return redirect('home')
 
    context = {'form': form, 'topics': topics} 
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id= pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()
    #We passed in the instance, so, this form will be prefilled with this room value
    #When the values don't match then this is not going to work
    
    if request.user != room.host:
        return HttpResponse('You are not allowed here!') 

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')     
        room.topic = topic    
        room.description = request.POST.get('description')     
        room.save()
        return redirect('home')#sends the user back to the home page

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)

@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowed here!') 

    if request.method == 'POST':
        room.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': room})

@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowed here!') 

    if request.method == 'POST':
        message.delete()
        return redirect('home')
    return render(request, 'base/delete.html', {'obj': message})

@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid:
            form.save()
        return redirect('user-profile', pk=user.id)
    return render(request, 'base/update-user.html', {'form': form})

def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q) #filtering the topics to show only 5 on the home page and to view others the user has to click more
    return render(request, 'base/topics.html', {'topics': topics})

def activityPage(request):
    room_messages = Message.objects.all()
    return render (request, 'base/activity.html', {'room_messages': room_messages})