import ledUDP
from time import sleep

LedStrip = ledUDP.Led("192.168.0.207", 8899, "Mis nuevos Leds", 4)

if __name__ == "__main__":
    print "Bienvenido al taller de HirikiLed"
    
    while 1:
        print "Rojo!"
        LedStrip.set_red(100)
        sleep(1)
        LedStrip.set_black()
        sleep(1)

        print "Verde!"
        LedStrip.set_green(100)
        sleep(1)
        LedStrip.set_black()
        sleep(1)

        print "Azul!"
        LedStrip.set_blue(100)
        sleep(1)
        LedStrip.set_black()
        sleep(1)
        
        
        
