import pytest
import random
import kro  


class FakeUser:
    def __init__(self, id, first_name):
        self.id = id
        self.first_name = first_name

class FakeChat:
    def __init__(self, id):
        self.id = id

class FakeMessage:
    def __init__(self, text, chat_id, user_id, first_name):
        self.text = text
        self.chat = FakeChat(chat_id)
        self.from_user = FakeUser(user_id, first_name)

class FakeChatMember:
    def __init__(self, user_id, first_name):
        self.user = FakeUser(user_id, first_name)

class FakeChatInstance:
    
    def __init__(self, members_dict):
        self.members = members_dict

    def get_member(self, user_id):
        return self.members.get(user_id)


@pytest.fixture(autouse=True)
def reset_globals():
    kro.current_word = ""
    kro.current_leader = None
    kro.players_scores = {}


@pytest.fixture
def fake_send_messages():
    messages = []

    def fake_send_message(chat_id, text):
        messages.append((chat_id, text))
    return messages, fake_send_message

@pytest.fixture
def fake_reply_messages():
    messages = []

    def fake_reply_to(message, text):
        messages.append((message.from_user.id, text))
    return messages, fake_reply_to


def test_start_game(monkeypatch, fake_send_messages, fake_reply_messages):
    send_messages_list, fake_send_message = fake_send_messages
    reply_messages_list, fake_reply_to = fake_reply_messages


    fake_admins = [FakeChatMember(101, "Alice"), FakeChatMember(102, "Bob")]
    monkeypatch.setattr(kro.bot, "get_chat_administrators", lambda chat_id: fake_admins)
    monkeypatch.setattr(kro.bot, "send_message", fake_send_message)
    monkeypatch.setattr(kro.bot, "reply_to", fake_reply_to)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    
    fake_msg = FakeMessage("/start", chat_id=1, user_id=101, first_name="Alice")
    kro.start_game(fake_msg)


    assert kro.current_leader == 101
    assert kro.current_word == kro.words_pool[0]  

    
    assert send_messages_list == [
        (101, f"Twoje słowo: {kro.current_word}")
    ]
   
    expected_reply = "Gra rozpoczęta! Prowadzący: Alice. Pozostali gracze zgadują słowo."
    assert reply_messages_list == [(101, expected_reply)]


def test_guess_word_correct(monkeypatch, fake_send_messages, fake_reply_messages):
    send_messages_list, fake_send_message = fake_send_messages
    reply_messages_list, fake_reply_to = fake_reply_messages

  
    kro.current_word = "egzamin"
    kro.current_leader = 101  

 
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    
    fake_msg = FakeMessage("egzamin", chat_id=1, user_id=102, first_name="Bob")
    monkeypatch.setattr(kro.bot, "send_message", fake_send_message)
    monkeypatch.setattr(kro.bot, "reply_to", fake_reply_to)

    kro.guess_word(fake_msg)

    
    assert kro.players_scores.get(102) == 1
    assert kro.current_leader == 102
    assert kro.current_word == kro.words_pool[0]
    assert send_messages_list == [
        (102, f"Twoje nowe słowo: {kro.current_word}")
    ]
    expected_reply = "Brawo, Bob! Odgadłeś/łaś słowo! Zostałeś/łaś nowym prowadzącym."
    assert reply_messages_list == [(102, expected_reply)]


def test_guess_word_leader(monkeypatch, fake_send_messages, fake_reply_messages):
    send_messages_list, fake_send_message = fake_send_messages
    reply_messages_list, fake_reply_to = fake_reply_messages


    kro.current_word = "egzamin"
    kro.current_leader = 101  

    monkeypatch.setattr(random, "choice", lambda seq: seq[0])

    fake_msg = FakeMessage("egzamin", chat_id=1, user_id=101, first_name="Alice")
    monkeypatch.setattr(kro.bot, "send_message", fake_send_message)
    monkeypatch.setattr(kro.bot, "reply_to", fake_reply_to)

    kro.guess_word(fake_msg)

    
    assert kro.players_scores.get(101) is None
    assert kro.current_leader == 101
    assert kro.current_word == kro.words_pool[0]
    expected_message = f"Napisałeś/łaś słowo, które miałeś wyjaśnić! Twoje nowe słowo to: {kro.current_word}"
    assert send_messages_list == [(101, expected_message)]
    assert reply_messages_list == []


def test_stop_game(monkeypatch, fake_reply_messages):
    reply_messages_list, fake_reply_to = fake_reply_messages


    kro.current_word = "egzamin"
    kro.current_leader = 101

    monkeypatch.setattr(kro.bot, "reply_to", fake_reply_to)

    fake_msg = FakeMessage("/stop", chat_id=1, user_id=101, first_name="Alice")
    kro.stop_game(fake_msg)


    assert kro.current_word == ""
    assert kro.current_leader is None
    assert reply_messages_list == [(101, "Gra została zakończona.")]


def test_show_score(monkeypatch, fake_reply_messages):
    reply_messages_list, fake_reply_to = fake_reply_messages


    kro.players_scores = {101: 1, 102: 2}


    fake_member_101 = FakeChatMember(101, "Alice")
    fake_member_102 = FakeChatMember(102, "Bob")
    fake_chat_instance = FakeChatInstance({101: fake_member_101, 102: fake_member_102})
    monkeypatch.setattr(kro.bot, "get_chat", lambda chat_id: fake_chat_instance)
    monkeypatch.setattr(kro.bot, "reply_to", fake_reply_to)

    fake_msg = FakeMessage("/score", chat_id=1, user_id=101, first_name="Alice")
    kro.show_score(fake_msg)


    expected_text = "Wyniki:\nAlice: 1\nBob: 2"
    assert reply_messages_list == [(101, expected_text)]
