from cjtool.common import *
import signal

class Monitor:
    def __init__(self):
        signal.signal(signal.SIGINT, exit_gracefully)
        pid = getProcessByName("observer.exe")
        path = "E:/github/appknife/_build-x64/Release/observer.exe"
        self.t = Debugger(pid, path)
        self.t.setDaemon(True)

    def run(self):
        try:
            self.t.start()
            while self.t.is_alive():
                pass
        except Exception as errtxt:
            print_warning(errtxt)

    def add_breakpoints(self):
        t = self.t

        t.addBreakPoint("observer!Subject::detach")
        t.addBreakPoint("observer!Subject::notify")
        t.addBreakPoint("observer!ConcreteObeserver::*")
        t.addBreakPoint("observer!ConcreteSubject::*")

def main():
    monitor = Monitor()
    monitor.add_breakpoints()
    monitor.run()

if __name__ == "__main__":
    main()
