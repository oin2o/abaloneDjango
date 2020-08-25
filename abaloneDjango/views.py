from random import random, randint

from django.db.models import Q, Max
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from rest_framework.authtoken.models import Token
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .forms import UserLoginForm, KnightSelectForm, KnightElectionForm
from .models import Board, Knight, User, SelectKnight, Game, Election, Expedition
from .serializers import RegistrationUserSerializer


def knight_select_view(request, username):
    template_name = 'abaloneDjango/knight_select.html'
    #print('11111')
    if request.method == 'POST':
        form = KnightSelectForm(request.POST)
        #print ('2222')

        username = request.POST.get('username')

        user, created = User.objects.get_or_create(
            username=username
        )

        user.username = username
        user.readyYn = 'Y'
        user.joinYn = 'Y'

        user.save()

        delSelectKnightList = SelectKnight.objects.filter(username=username)

        delSelectKnightList.delete()

        knightliststr = request.POST.get('knightliststr')

        #print('2222'+knightliststr+'2222')

        knightlist = knightliststr.split(';')

        for knightId in knightlist :
            #print(knightId)
            if knightId == '':
                break

            selectKnight, created = SelectKnight.objects.get_or_create(
                username=username,
                knightId=knightId
            )
            selectKnight.save()

        return HttpResponseRedirect(
            '/mycard/%s' % username
        )

    else:
        form = KnightSelectForm()
        form.fields['username'].initial = username
        knightlist = Knight.objects.filter(~Q(knightId=9)).order_by('knightId')
        context = {
            'form': form,
            'username':username,
            'knightlist': knightlist,
        }

    return render(request, template_name, context)


def base_view(request):
    template_name = 'abaloneDjango/base.html'
    return render(request, template_name)


def knight_login_view(request):

    template_name = 'abaloneDjango/knight_login.html'

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():

            user, created = User.objects.get_or_create(
                username=form.cleaned_data['username']
            )

            user.username = form.cleaned_data['username']
            user.joinYn = 'Y'
            user.readyYn = 'N'

            user.save()

            return HttpResponseRedirect(
                '/knight_select/%s' % form.cleaned_data['username']
            )
    else:
        form = UserLoginForm()

    context = {
        'form': form
    }
    return render(request, template_name, context)


def knight_auto_view(request,username):
    user, created = User.objects.get_or_create(
        username=username
    )

    user.username = username
    user.joinYn = 'Y'
    user.readyYn = 'N'

    user.save()

    return HttpResponseRedirect(
        '/knight_select/%s' % username
    )


def mycard_view(request,username):

    template_name = 'abaloneDjango/mycard.html'

    user = get_object_or_404(User, username=username)

    if user.assinKnightId == 0:  # 미배정
        template_name = 'abaloneDjango/wait.html'

    joinusercnt = User.objects.filter(joinYn='Y').count()
    readyusercnt = User.objects.filter(readyYn='Y').count()

    cardinfo = ''
    cardinfostr = ''
    if user.assinKnightId == 1 : # 멀린

        userlist = User.objects.filter(assinKnightId__in=[6,7,10])

        for userinfo in userlist:
            cardinfostr = cardinfostr + '['+userinfo.username + '] '

        cardinfo = '모드레드를 제외한 악 : ' + cardinfostr
    elif user.assinKnightId == 2: # 퍼시발
        userlist = User.objects.filter(assinKnightId__in=[1,6])

        for userinfo in userlist:
            cardinfostr = cardinfostr + '[' + userinfo.username + '] '

        cardinfo = '멀린 or 모르가나 : '+ cardinfostr

    elif user.assinKnightId in [5,6,7]: # 모드레드
        userlist = User.objects.filter(assinKnightId__in=[5,6,7])

        for userinfo in userlist:
            cardinfostr = cardinfostr + '[' + userinfo.username + '] '

        cardinfo = '악의 하수인들 : '+ cardinfostr


    context = {
        'username': username,  # 추가
        'assinknightid': user.assinKnightId,  # 추가
        'cardinfo': cardinfo,  # 추가
        'joinusercnt': joinusercnt,  # 추가
        'readyusercnt': readyusercnt,  # 추가
    }

    return render(request, template_name, context)


def start_view(request):
    template_name = 'abaloneDjango/start.html'

    userlist = User.objects.all().order_by('-joinYn')  # 추가

    joinusercnt = User.objects.filter(joinYn='Y').count()

    readyusercnt = User.objects.filter(readyYn='Y').count()

    # 하나임
    gamelist = Game.objects.filter(completeYn='N')  # 추가

    context = {
        'userlist': userlist,  # 추가
        'joinusercnt': joinusercnt,  # 추가
        'readyusercnt': readyusercnt,  # 추가
        'gamelist':gamelist,
    }
    return render(request, template_name, context)


def assin_view(request):
    template_name = 'abaloneDjango/start.html'
    weight = 5
    assinnum = 0

    #참여 유저수
    joinusercnt = User.objects.filter(joinYn='Y').count()

    # 게임 setting
    gamecnt = Game.objects.filter(completeYn='N').count()
    #print('gamecnt:' + gamecnt.__str__())

    if gamecnt > 0 :
        return render(request, 'abaloneDjango/error.html', {'errstr': '아직 진행중인 게임이 있습니다. 게임을 취소하고 다시 시도하십시오'} )

    gameIdObj = Game.objects.all().order_by('-gameId')

    if gameIdObj :
        print('gameId:' + gameIdObj[0].gameId.__str__())
        gameId = gameIdObj[0].gameId + 1
    else:
        print('gameId is null:')
        gameId= 1

    game = Game.objects.create()

    game.gameId = gameId
    game.joinUserCnt = joinusercnt

    game.save()


    # 카드 세팅 초기화
    userlist = User.objects.filter(joinYn='Y')

    for user in userlist:
        user.assinKnightId = 0
        user.save()


    # 카드 지정 완료 유저 Q
    assineduserq = Q()
    for i in range(1,joinusercnt+1):

        q = Q(knightId=i)
        q.add(~assineduserq ,q.AND)
        #print('index::::' + i.__str__()+ '::'+ q.__str__())

        selectknightlist = SelectKnight.objects.filter(q)

        #for selectknight in selectknightlist:
            #print(selectknight.username + selectknight.knightId.__str__() )

        selectknightcnt = weight * selectknightlist.count()

        assinnum = randint(1,joinusercnt + selectknightcnt +1 - i)
        #print('index::::' + i.__str__() + '::assinnum:'+ assinnum.__str__()+ '::selectknightcnt:'+ selectknightcnt.__str__()+ '::joinusercnt:'+ joinusercnt.__str__()+ ':::'+ ( ((assinnum-1)/3).__int__()+1).__str__())

        if assinnum <= selectknightcnt:
            #print('111::(assinnum - selectknightcnt-1):' + ( (assinnum-1)/weight).__int__().__str__())
            assinedusername = selectknightlist[ ( (assinnum-1)/weight).__int__()].username
            #print('111:' + selectknightlist.__str__())

        else:
            unassineduserlist = User.objects.filter(Q(joinYn='Y') & Q(assinKnightId=0))
            #print('222::(assinnum - selectknightcnt-1):' + (
            #            assinnum - selectknightcnt - 1).__str__())
            assinedusername = unassineduserlist[(assinnum - selectknightcnt-1)].username
            #print('222:' + assinedusername)

        user = get_object_or_404(User, username=assinedusername)
        user.assinKnightId = i
        user.save()

        assineduserq.add( Q(username=assinedusername) , assineduserq.OR)
        #print(assineduserq.__str__())

    return HttpResponseRedirect('/start/' )


def delete_view(request,username):
    template_name = 'abaloneDjango/start.html'

    user = get_object_or_404(User, username=username)

    user.delete()

    return HttpResponseRedirect('/start/' )


def join_view(request,username):
    template_name = 'abaloneDjango/start.html'

    user = get_object_or_404(User, username=username)

    user.username = username
    user.joinYn = 'Y'

    user.save()

    return HttpResponseRedirect('/start/' )


def init_view(request):
    template_name = 'abaloneDjango/start.html'

    userlist = User.objects.all()

    for user in userlist:
        user.joinYn = 'N'
        user.readyYn = 'N'
        user.assinKnightId = 0
        user.save()

    selectknightlist = SelectKnight.objects.all()

    for selectknight in selectknightlist:
        selectknight.delete()


    return HttpResponseRedirect('/start/')


def game_complete_view(request,gameid):
    template_name = 'abaloneDjango/start.html'

    userlist = User.objects.all()

    # 유저 지정카드 초기화
    for user in userlist:
        user.assinKnightId = 0
        user.save()

    game = get_object_or_404(Game, gameId=gameid)

    game.completeYn = 'Y'

    game.save()

    return HttpResponseRedirect('/start/' )


def expeditionSeq_ini_view(request,gameid):
    template_name = 'abaloneDjango/start.html'

    game = get_object_or_404(Game, gameId=gameid)
    expeditionSeq = game.expeditionSeq - 1
    if expeditionSeq < 1:
        expeditionSeq = 1

    game.expeditionSeq = expeditionSeq
    game.save()

    expedition = Expedition.objects.filter(gameId=gameid,expeditionSeq__gte=expeditionSeq)
    print(" expedition :" + expedition.count().__str__() )
    expedition.delete()

    election = Election.objects.filter(gameId=gameid, expeditionSeq__gte=expeditionSeq)
    print(" election :" + election.count().__str__())
    election.delete()

    return HttpResponseRedirect('/start/' )



def knight_election_view(request, username):
    template_name = 'abaloneDjango/knight_election.html'

    gamemap = [
        [2, 3, 3, 4, 4],
        [3, 4, 4, 5, 5],
        [3, 4, 4, 5, 5],
        [3, 4, 4, 5, 5],
    ]

    if request.method == 'POST':
        form = KnightElectionForm(request.POST)

        username = request.POST.get('username')
        gameid = request.POST.get('gameid')
        succyn = request.POST.get('succyn')
        expeditionseq = request.POST.get('expeditionseq')

        print(" gameid :"+gameid+" expeditionseq :" + expeditionseq+" succyn :"+succyn)

        # 게임 및 회차 valid
        game = get_object_or_404(Game, gameId=gameid)
        if game.expeditionSeq.__str__()  != expeditionseq:
            return render(request, 'abaloneDjango/knight_error.html', {'username': username, 'errstr': '회차 오류/ 새로고침후 다시 투표'})
        if game.completeYn != 'N':
            return render(request, 'abaloneDjango/knight_error.html', {'username': username, 'errstr': '종료된 게임/ 새로고침후 다시 투표'})

        # 투표여부확인
        electioncnt = Election.objects.filter(gameId=gameid, expeditionSeq=expeditionseq, username=username).count()

        if electioncnt > 0:
            return render(request, 'abaloneDjango/knight_error.html', {'username':username,'errstr': '이미 투표하셨습니다.'})

        election = Election.objects.create()

        election.gameId = gameid
        election.succYn = succyn
        election.expeditionSeq = expeditionseq
        election.username = username

        election.save()
        maxelectioncnt = gamemap[game.joinUserCnt-7][int(expeditionseq)-1]
        print(" maxelectioncnt :" + maxelectioncnt.__str__()  + " game.joinUserCnt :" + game.joinUserCnt.__str__() + " expeditionseq :" + expeditionseq)

        # 최종결과 저장
        electioncnt = Election.objects.filter(gameId=gameid,expeditionSeq=expeditionseq).count()
        if electioncnt >= maxelectioncnt:
            usernamelist = ''
            succcnt = Election.objects.filter(gameId=gameid, expeditionSeq=expeditionseq,succYn='Y').count()
            electionlist = Election.objects.filter(gameId=gameid, expeditionSeq=expeditionseq)

            for election in electionlist:
                usernamelist = usernamelist + '[' + election.username + ']'
            offset = 0
            
            # 4회차는 봐준다
            if expeditionseq == '4' :
                offset = 1

            if succcnt >= electioncnt - offset:
                expeditionsuccyn = 'Y'
            else:
                expeditionsuccyn = 'N'

            expedition = Expedition.objects.create()

            expedition.gameId = gameid
            expedition.expeditionSeq = expeditionseq
            expedition.succYn = expeditionsuccyn
            expedition.expeditionUserCnt = electioncnt
            expedition.succUserCnt = succcnt
            expedition.completeYn = 'Y'
            expedition.usernamelist = usernamelist

            expedition.save()

            # 진행회차 증가
            game.expeditionSeq = int(expeditionseq) + 1
            game.save()

        return HttpResponseRedirect(
            '/knight_expedition/%s' % username
        )

    else:
        form = KnightElectionForm()

        game = Game.objects.get(completeYn='N')

        if not game:  # 미배정
            return HttpResponseRedirect(
                '/mycard/%s' % username
            )
        form.fields['gameid'].initial = game.gameId
        form.fields['expeditionseq'].initial = game.expeditionSeq
        form.fields['username'].initial = username

        expeditionlist = Expedition.objects.filter(gameId=game.gameId).order_by('expeditionSeq')

        context = {
            'form': form,
            'username':username,
            'gameid': game.gameId,
            'joinusercnt': game.joinUserCnt,
            'expeditionseq': game.expeditionSeq,
            'expeditionlist': expeditionlist,
        }

    return render(request, template_name, context)



def knight_expedition_view(request, username):
    template_name = 'abaloneDjango/knight_expedition.html'

    if request.method == 'POST':
        template_name  = 'abaloneDjango/knight_election.html'

        form = KnightElectionForm(request.POST)

        username = request.POST.get('username')
        gameid = request.POST.get('gameid')
        succyn = request.POST.get('succyn')
        expeditionseq = request.POST.get('expeditionseq')

        form.fields['gameid'].initial = gameid
        form.fields['expeditionseq'].initial = expeditionseq
        form.fields['username'].initial = username
        form.fields['succyn'].initial = succyn


        # 투표여부확인
        electioncnt = Election.objects.filter(gameId=gameid, expeditionSeq=expeditionseq, username=username).count()

        if electioncnt > 0:
            return render(request, 'abaloneDjango/knight_error.html', {'username':username,'errstr': '이미 투표하셨습니다.'})

        return HttpResponseRedirect(
            '/knight_election/%s' % username
        )

    else:
        form = KnightElectionForm()

        try:
            game = Game.objects.get(completeYn='N')
        except Game.DoesNotExist:
            return HttpResponseRedirect(  '/mycard/%s' % username )

        form.fields['gameid'].initial = game.gameId
        form.fields['expeditionseq'].initial = game.expeditionSeq
        form.fields['username'].initial = username

        expeditionlist = Expedition.objects.filter(gameId=game.gameId).order_by('expeditionSeq')

        failrangelist = {}
        succrangelist = {}
        for expedition in expeditionlist:
            failrangelist[expedition.expeditionSeq]= range(1, expedition.expeditionUserCnt - expedition.succUserCnt)
            succrangelist[expedition.expeditionSeq]  = range(1,expedition.succUserCnt)

        context = {
            'form': form,
            'username':username,
            'gameid': game.gameId,
            'joinusercnt': game.joinUserCnt,
            'expeditionseq': game.expeditionSeq,
            'expeditionlist': expeditionlist,
            'failrangelist':failrangelist,
            'succrangelist': succrangelist,
        }

    return render(request, template_name, context)