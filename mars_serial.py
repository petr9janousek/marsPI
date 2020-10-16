# coding UTF-8
import serial, queue, sys, logging

import mars_thread
from gi.repository import GLib

logger = logging.getLogger("log.serial")

class UART:
    def __init__(self, manager):
        self.serial = serial.Serial()
        self.serial.baudrate = 115200
        self.serial.timeout = 1 #s

        self.manager = manager

        self.serialthread = mars_thread.Job(target=self.read_thread, daemon=True)
        self.serialthread.start()

    def read_thread(self):
        if self.serial.in_waiting > 0:
            self.read_queue(self.manager.data_que)
        if not self.manager.data_que.empty():
            GLib.idle_add(self.manager.manage_info)
    

    def connect(self, port):
        self.serial.port = port

        if self.serial.isOpen():
            logger.warning('Port %s je jiz pripojen', port)
        else:
            self.serial.open()
            logger.info('Pripojeno na portu %s', port)

    def disconnect(self):
        if self.serial.isOpen():
            self.serial.close()
            logger.info("Port odpojen")

    def list_ports(self):
        ports = []
        if sys.platform.startswith('linux'):
            ports = ['/dev/ttyS0', '/dev/ttyAMA0', '/dev/ttyUSB0']
        elif sys.platform.startswith('win' or 'msys'):
            options = ['COM%s' % (i + 1) for i in range(32)]
            for port in options:
                try:
                    s = serial.Serial(port)
                    s.close()
                    ports.append(port)
                except (OSError, serial.SerialException):
                    pass
        else:
            #logger.error("Nepodporovana platforma")
            print("Nepodporovana platforma")
        return ports

    def uart_code(self, data):
        result, element = [], int(data)
        #for element in val:
        nibbleA = (element & 0xF0) >> 4   # high nibble
        nibbleB = (element & 0x0F)        # low nibble
        # 0-F, if 0-9 + '0' else A-F 'A'
        result.append((nibbleA + 0x30) if (nibbleA < 0x0A) else (nibbleA + 0x37))
        result.append((nibbleB + 0x30) if (nibbleB < 0x0A) else (nibbleB + 0x37))
        return result

    def uart_decode(self, data):
        pass

    def read_bytes(self, count = 1):
        if self.serial.isOpen():
            data = self.serial.read(count)
            data = data.decode()
            if data:
                #logger.debug("Prijato: %s", data)
                print("Prijato: %s" % data)
                return data

    def read_queue(self, queue, eol='!'):
        if self.serial.isOpen():
            line = self.serial.read_until(eol.encode())  # to pass as number
            line = line.decode()
            if line.strip(): #contains data
                line = line.split(',')
                queue.put(line) # to pass as string
        #return [1,2,3,4,5,6,7,8]

    def write(self, data_list):
        if self.serial.isOpen():
            #[0ADR, 1CMD, 2VAL, 3BIT] into ints
            data_list = [int(e) for e in data_list]
            #VAL into 2 bytes
            item = data_list[2]
            data_list[2] = (item >> 8) & 0xFF #high byte
            data_list.insert(3, item & 0xFF)  #low byte
            #calculate checksum
            data_list.append(sum(data_list))
            logger.info("Odesilam: %s", data_list)
            #create encoding
            data_list = [self.uart_code(e) for e in data_list]
            flat_list = [item for sublist in data_list for item in sublist]
            #insert flow control characters
            flat_list.insert(0, 42)
            flat_list.append(33)
            self.serial.write(bytearray(flat_list))
            logger.debug("Odeslano: %s", flat_list)
            #print("Odeslano: %s" % flat_list)

if __name__ == "__main__":
    print("Testovaci rezim")
    sp = UART(lambda: None)
    q = queue.Queue()

    l = sp.list_ports()
    for i in range(len(l)):
        print(i, " ", l[i])
    v = int(input("Zadejte index portu: "))

    sp.connect(l[v])
    print("Pripojen port:", l[v], " baudrate:", sp.serial.baudrate)

    while True:
        dir = input("_Odeslat nebo _Prijmout data? (o/p) ")
        for i in range(10):
            if dir == "p":
                #sp.read_queue(q)
                #print(q.get())
                data = sp.read_bytes()
            elif dir == "o":
                d = input().encode()
                sp.serial.write(d)
            else:
                print("Neplatny vstup")