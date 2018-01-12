# -*- coding: utf-8 -*-

"""=================================================="""
"""                Hashcode Battler                  """
""" ハッシュコードで戦うバーコードバトラー的なゲーム """
"""                                 2017,2018 7M4MON """
"""=================================================="""

import hashlib
import sys
import random
import RPi.GPIO as GPIO
import time

''' Credit Info '''
app_name = "Hashcode Battler"
version  = "1.01"
author   = "7M4MON"
year     = "2018"
url      = "nomulabo.com"

''' define the pins '''
PIN_BTN_A = 4
PIN_BTN_B = 17
PIN_LED_1 = 27
PIN_LED_2 = 22
PIN_LED_3 = 23
PIN_LED_4 = 24
PIN_LED_5 = 25

led_pin = [PIN_LED_1, PIN_LED_2, PIN_LED_3, PIN_LED_4, PIN_LED_5]

''' LED Status '''
LED_OFF    = 0
LED_TURN_A = 1
LED_TURN_B = 2
LED_ATK_A  = 3
LED_ATK_B  = 4
LED_POW_A  = 5
LED_POW_B  = 6
LED_BLINK  = 7

''' Command Type '''
CMD_NONE    = 0
CMD_ATTACK  = 1
CMD_RECOVER = 2

''' Card Info '''
class CardInfo:
    def __init__(self):
        self.hp = 0
        self.hp_max = 0
        self.attack = 0
        self.defence = 0
        self.speed = 0

''' Global Variables '''
card_a = CardInfo()
card_b = CardInfo()
battle_loop = 0
battle_turn = 0
lcd_buffer = ["","","","",""]
exe = 0

''' The Main Function '''
def main():
    SetupPin()
    OutputLed(LED_BLINK)
    SetCreditLcd()
    DisplayConsole()
    DisplayOled()
    exe = 1
    while exe:
        InputButton()
        
        # カードの初期化
        InitCardInfo(card_a)
        InitCardInfo(card_b)
        SetCardStatusLcd(card_a, card_b)
        
        # A側 入力
        SetInfoLcd ("Swipe Card for A")
        OutputLed(LED_TURN_A)
        DisplayConsole()
        DisplayOled()
        cardString = InputString()
        ManageCard(cardString, card_a)
        SetCardStatusLcd(card_a, card_b)
        
        # B側 入力
        SetInfoLcd ("Swipe Card for B")
        OutputLed(LED_TURN_B)
        DisplayConsole()
        DisplayOled()
        cardString = InputString()
        ManageCard(cardString, card_b)
        SetCardStatusLcd(card_a, card_b)
        
        SetInfoLcd ("Battle Start!")
        OutputLed(LED_BLINK)
        DisplayConsole()
        DisplayOled()
        
        battle_loop = 1
        
        # 初回のターンは SPEEDで決める
        if card_a.speed < card_b.speed :
            battle_turn = 1
        else :
            battle_turn = 0
        
        while battle_loop == 1 :
        
            ''' BATTLE '''
            # Bのターン
            if battle_turn :
                print ("Turn B")
                OutputLed(LED_TURN_B)
                battleCmd = InputButton()
                
                # Recover or Attack
                if battleCmd == CMD_ATTACK :
                    OutputLed(LED_ATK_B)
                    battle_loop = Attack(card_b, card_a)
                else :
                    OutputLed(LED_POW_B)
                    Recover(card_b)
                    
                battle_turn = 0
            
            # Aのターン
            else :
                print ("Turn A")
                OutputLed(LED_TURN_A)
                battleCmd = InputButton()
                
                # Recover or Attack
                if battleCmd == CMD_ATTACK :
                    OutputLed(LED_ATK_A)
                    battle_loop = Attack(card_a, card_b)
                else :
                    OutputLed(LED_POW_A)
                    Recover(card_a)
                    
                battle_turn = 1
            
            # 結果を表示
            SetCardStatusLcd(card_a, card_b)
            DisplayConsole()
            DisplayOled()
            # 次のターンへ
        
        # 勝負あり
        SetResultLcd(battle_turn)
        OutputLed(LED_BLINK)
        DisplayConsole()
        DisplayOled()
        
    # exe == 0
    TerminateApp()

''' HP,HP_MAX,ATTACK,DEFENCE,SPEED計算 '''
def ManageCard(inputString, cardInfo):
    # ハッシュ計算
    hash = hashlib.sha256(inputString.encode('utf-8')).hexdigest()
    cardInfo.hp = int(hash[0:4], 16) + 34464                # MAX:99999
    cardInfo.hp_max = cardInfo.hp
    cardInfo.attack = int(hash[4:8], 16) + 34464            # MAX:99999
    cardInfo.defence = int(hash[8:12], 16) + 34464          # MAX:99999
    cardInfo.speed = int(hash[12:16], 16) + 34464           # MAX:99999
    

''' ATTACK '''
def Attack(attackCard, defenceCard):
    # 命中したか回避したか計算
    hit = DetectHit(attackCard, defenceCard)
    
    # ダメージの計算
    damage = CalcDamage(attackCard, defenceCard) * hit
    
    if damage == 0 :
        SetInfoLcd ("Miss!")
        # MISS
    else :
        SetInfoLcd ("Damage : " + str(damage))
        # HIT
    
    defenceCard.hp = defenceCard.hp - damage
    
    battle_cont = 1
    
    # <0だったらEND
    if defenceCard.hp <= 0:
        defenceCard.hp = 0
        battle_cont = 0
    
    return battle_cont


''' 命中率の計算 '''
def DetectHit(attackCard, defenceCard):
    # 回避率の計算(30% to 3%)
    evasion_rate = (attackCard.speed / defenceCard.speed) * 10 - random.randint(0,100)
    
    hit = 1
    if evasion_rate > 0 :
        hit = 0
    
    return hit
    

''' ダメージ量の計算 '''
def CalcDamage(attackCard, defenceCard):
    # ダメージ値の計算 ( 3346 ～ 10000 ) + ( 3446 ～ 29015) = 6892 to 39015
    damage = attackCard.attack / 10 + (attackCard.attack / defenceCard.defence) * 10000
    damage = damage * (random.random() + 0.7) # ダメージ量0.7～1.7倍
    return int(damage)
    

''' 回復 '''
def Recover(card):
    hp_before = card.hp
    
    # 回復値の計算(10%～35%)
    value = int(card.hp_max * (random.random()/4 + 0.1 ))
    card.hp += value
    # 最大値以上だったら丸める
    if card.hp > card.hp_max:
        card.hp = card.hp_max
    
    # 差分の計算
    diff = card.hp - hp_before
    SetInfoLcd ("Recover : " + str(diff))
    

''' 入力待ちとexitチェック、改行の除去 '''
def InputString():
    # 入力待ち
    s = sys.stdin.readline()
    s = s.replace('\n', '')
    s = s.replace('\r', '')
    
    if s == 'q' :
        TerminateApp()
        
    return s
    

''' アプリケーション終了処理 '''
def TerminateApp():
    exe = 0
    GPIO.cleanup()
    exit()


''' Raspberry PiのGPIOの初期化 '''
def SetupPin():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN_BTN_A, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(PIN_BTN_B, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    for pin in led_pin :
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.LOW)


''' 5つのLEDを特定のパターンで光らせる '''
def OutputLed(state):
    # 一旦消灯
    for pin in led_pin :
        GPIO.output(pin, GPIO.LOW)
        
    if state == LED_TURN_A:
        GPIO.output(PIN_LED_1, GPIO.HIGH)
        
    elif state == LED_TURN_B:
        GPIO.output(PIN_LED_5, GPIO.HIGH)
        
    elif state == LED_ATK_A:
        for i in range(5):
            GPIO.output(led_pin[i], GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(led_pin[i], GPIO.LOW)
        
    elif state == LED_ATK_B:
        for i in range(5):
            GPIO.output(led_pin[4-i], GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(led_pin[4-i], GPIO.LOW)
        
    elif state == LED_POW_A:
        for i in range(3):
            GPIO.output(led_pin[2-i], GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(led_pin[2-i], GPIO.LOW)
        
    elif state == LED_POW_B:
        for i in range(3):
            GPIO.output(led_pin[2+i], GPIO.HIGH)
            time.sleep(0.1)
            GPIO.output(led_pin[2+i], GPIO.LOW)
        
    elif state == LED_BLINK:
        for j in range(5):
            for i in range(5):
                GPIO.output(led_pin[i], GPIO.HIGH)
            time.sleep(0.1)
            for i in range(5):
                GPIO.output(led_pin[i], GPIO.LOW)
            time.sleep(0.1)
    else:
        # なにもしない。
        time.sleep(0.1)
    


''' ボタン入力を監視し、入力されたらコマンドを返す '''
def InputButton():
    cmd = 0
    while (cmd == 0):
        cmd = CheckButton()
        time.sleep(0.01)
    return cmd


''' ボタン入力検出処理 '''
def CheckButton():
    if(GPIO.input(PIN_BTN_A) == 0):
        time.sleep(0.1)                 # 押されたときチャタリングの防止
        while(GPIO.input(PIN_BTN_A) == 0):
            time.sleep(0.1)             # 離されるのを待つ
        time.sleep(0.1)                 # 離したときチャタリングの防止
        print ("Pressed PIN_BTN_A")
        return CMD_RECOVER
        
    elif(GPIO.input(PIN_BTN_B) == 0):
        time.sleep(0.1)                 # 押されたときチャタリングの防止
        while(GPIO.input(PIN_BTN_B) == 0):
            time.sleep(0.1)             # 離されるのを待つ
        time.sleep(0.1)                 # 離したときチャタリングの防止
        print ("Pressed PIN_BTN_B")
        return CMD_ATTACK
        
    else:
        time.sleep(0.01)
        return 0


''' カード情報の表示 '''
def PrintCardInfo(cardInfo):
    print ("cardInfo.hp : " + str(cardInfo.hp))
    print ("cardInfo.hp_max : " +  str(cardInfo.hp_max))
    print ("cardInfo.attack : " +  str(cardInfo.attack))
    print ("cardInfo.defence : " +  str(cardInfo.defence))
    print ("cardInfo.speed : " +  str(cardInfo.speed))

''' カード情報をディスプレイバッファにセットする '''
def SetCardStatusLcd(card_a, card_b):
    lcd_buffer[1] = '{:>5}'.format(str(card_a.hp)) + " HP " + '{:>5}'.format(str(card_b.hp))            # 5桁にパディング
    lcd_buffer[2] = '{:>5}'.format(str(card_a.attack)) + " AT " + '{:>5}'.format(str(card_b.attack))                            
    lcd_buffer[3] = '{:>5}'.format(str(card_a.defence)) + " DF " + '{:>5}'.format(str(card_b.defence)) 
    lcd_buffer[4] = '{:>5}'.format(str(card_a.speed)) + " SP " + '{:>5}'.format(str(card_b.speed)) 
    
''' 1行目に情報を表示する '''
def SetInfoLcd(info_str):
    lcd_buffer[0] = info_str

''' 表示 '''
def DisplayConsole():
    for line in lcd_buffer :
        print (line)
    
    # デバッグ用に区切り
    print ("----------------")
    
    

import Adafruit_SSD1306

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)

''' OLEDに表示する '''
def DisplayOled():
    # Load  font.
#    font_t = ImageFont.truetype('VCR_OSD_MONO_1.001.ttf', 12)
#    font_e = ImageFont.truetype('VCR_OSD_MONO_1.001.ttf', 10)
    font_t = ImageFont.truetype('Fipps-Regular.otf', 8)
    font_e = ImageFont.truetype('VCR_OSD_MONO_1.001.ttf', 12)

    # Initialize library.
    disp.begin()
     
    # Clear display.
    disp.clear()
    disp.display()
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height))
    
    # Get drawing object to draw on image.
    draw = ImageDraw.Draw(image)
    
    y = 0
    top = y
    draw.text((0, top),     lcd_buffer[0],  font=font_t, fill=255)
    draw.text((0, top+16),  lcd_buffer[1],  font=font_e, fill=255)
    draw.text((0, top+28),  lcd_buffer[2],  font=font_e, fill=255)
    draw.text((0, top+40),  lcd_buffer[3],  font=font_e, fill=255)
    draw.text((0, top+52),  lcd_buffer[4],  font=font_e, fill=255)
    
    # Display image.
    disp.image(image)
    disp.display()
    time.sleep(0.01)

''' カード情報の初期化 '''
def InitCardInfo(card):
    card.hp = 0
    card.hp_max = 0
    card.attack = 0
    card.defence = 0
    card.speed = 0
    
    
''' 結果の表示 '''
def SetResultLcd(winner):
    if winner == 1 :
        lcd_buffer[2] = " WIN " + "    " + "LOSE"
        lcd_buffer[3] = " WIN " + "    " + "LOSE"
    else :
        lcd_buffer[2] = " LOSE" + "    " + " WIN "
        lcd_buffer[3] = " LOSE" + "    " + " WIN "
        
    lcd_buffer[4] = "Press Button...."

''' クレジットの表示 '''
def SetCreditLcd():
    lcd_buffer[0] = app_name
    lcd_buffer[1] = "    Version " + version
    lcd_buffer[2] = "     " + year + " " + author
    lcd_buffer[3] = "    " + url
        
    lcd_buffer[4] = "Press Button...."

''' プログラムの開始 '''
main()


