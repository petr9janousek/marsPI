import time, threading

#pausable thread
class Job (threading. Thread):
    def __init__ (self, *args, **kwargs):
        super(Job, self).__init__(*args, **kwargs)
        #private
        self.__active = threading.Event()   # is used to suspend the thread's identity
        self.__active.clear()    # set to True
        self.__alive = threading.Event()   # to stop the thread's identity
        self.__alive.set()   # Set to True
        self.__target = kwargs['target']
        self.__args = kwargs['args']
        #public
        self.speed = 0.1

    def run(self):
        while self.__alive.is_set():
            self.__active.wait()   # returns immediately when false, blocking until the internal identity bit is true to return
            self.__target(*self.__args)   #calls the target, unpacks the tuple
            time.sleep(self.speed)

    def pause(self):
        self.__active.clear()   # set to False to allow threads to block

    def resume(self):
        self.__active.set()  # set to True to allow thread to stop blocking

    def stop(self):
        self.__active.set()    # Restores a thread from a paused state. How to have paused
        self.__alive.clear()    # set to False

if __name__ == "__main__":
    def add(num1,num2):
        print('Testju: ', num1 + num2)
    j = Job(target=add, args=(1,1))
    j.start()
    time.sleep(1)
    j.pause()
    time.sleep(1)
    j.resume()
    time.sleep(1)
    j.pause()
    time.sleep(1)
    j.stop()