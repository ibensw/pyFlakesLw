import sublime, sublime_plugin
import subprocess
from threading import Timer

# class PyFlakesLwCommand(sublime_plugin.WindowCommand):

#     def run(self):
#         pass

class PyFlakesLwListener(sublime_plugin.EventListener):
    REGION_KEY = 'pyflakeslw_errors'
    STATUS_KEY = 'pyflakeslw_status'
    SETTINGS_KEY = 'pyflakeslw_errors'
    current_errors = {}

    def __init__(self):
        self.errors={}
        self.view = None
        self.notify = Timer(0.3, lambda: self.update())

    def on_modified(self, view):
        if not view.sel():
            return
        lang, _ = view.scope_name(view.sel()[0].begin()).split(' ', 1)
        if not lang == "source.python":
            self.view.settings().erase(self.SETTINGS_KEY)
            return
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
        PyFlakesLwListener.current_errors = self.errors
        self.view.settings().set(self.SETTINGS_KEY, "True")

class PyFlakesLwCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.active_view()
        if not view.settings().get(PyFlakesLwListener.SETTINGS_KEY):
            return
        if not view.sel():
            return
        lang, _ = view.scope_name(view.sel()[0].begin()).split(' ', 1)
        if not lang == "source.python":
            self.view.settings().erase(self.SETTINGS_KEY)
            return
        self.keys = list(PyFlakesLwListener.current_errors.keys())
        if not self.keys:
            return
        self.keys.sort()
        items = ["L{}: {}".format(lineno, PyFlakesLwListener.current_errors[lineno]) for lineno in self.keys]
        self.window.show_quick_panel(items, self.go)

    def go(self, i):
        view = self.window.active_view()
        lineno = self.keys[i]
        point = view.text_point(lineno-1, 0)
        r = view.line(point)
        view.show_at_center(r)
        view.sel().clear()
        view.sel().add(r.end())
