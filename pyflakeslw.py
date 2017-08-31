import sublime, sublime_plugin
import subprocess
from threading import Timer

# class PyFlakesLwCommand(sublime_plugin.WindowCommand):

#     def run(self):
#         pass

class PyFlakesLwListener(sublime_plugin.EventListener):
    REGION_KEY = 'pyflakeslw_errors'
    STATUS_KEY = 'pyflakeslw_status'

    def __init__(self):
        self.notify = Timer(0.3, lambda: self.update())
        self.notify.start()
        self.errors={}
        self.view = None

    def on_modified(self, view):
        print("Restarting timer!")
        self.notify.cancel()
        self.notify = Timer(0.3, lambda: self.update())
        self.view = view
        self.notify.start()

    def on_activated(self, view):
        self.on_modified(view)

    def on_load(self, view):
        self.on_modified(view)

    def on_selection_modified(self, view):
        sel = view.sel()
        if not sel:
            return
        point=sel[0].end()
        row, _ = view.rowcol(point)
        row+=1
        if row in self.errors:
            view.set_status(self.STATUS_KEY, self.errors[row])
        else:
            view.erase_status(self.STATUS_KEY)


    def update(self):
        proc = subprocess.Popen(['pyflakes'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        inpipe = bytes(self.view.substr(sublime.Region(0, self.view.size())), 'UTF-8')
        output, _ = proc.communicate(input=inpipe)
        output = output.decode()
        lines = output.split('\n')

        self.errors={}
        regions=[]
        for line in lines: 
            if line[0:8] == "<stdin>:":
                filename, lineno, msg = line.split(':', 2)
                lineno = int(lineno)
                self.errors[lineno] = msg
                point = self.view.text_point(lineno-1, 0)
                regions.append(self.view.line(point))
        self.view.erase_regions(self.REGION_KEY)
        self.view.add_regions(self.REGION_KEY, regions, 'invalid', 'circle')
        self.on_selection_modified(self.view)

