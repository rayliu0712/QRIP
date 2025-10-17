import os
import wx
import socket
import psutil
import qrcode
import webbrowser
from io import BytesIO
from typing import NamedTuple


class NameAddr(NamedTuple):
    name: str
    addr: str


class AddrsKit(NamedTuple):
    addrs: list[NameAddr]
    choice: wx.Choice
    prompt: wx.StaticText
    qr: wx.StaticBitmap


def start_QRIP():
    if os.name == 'nt':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(True)

    app = wx.App()
    appFrame = AppFrame()
    appFrame.Show()
    app.MainLoop()


def get_v4_v6_addrs() -> tuple[list[NameAddr], list[NameAddr]]:
    v4_addrs = []
    v6_addrs = []

    stats = psutil.net_if_stats()

    for name, snicaddrs in psutil.net_if_addrs().items():
        # disabled
        if not stats[name].isup:
            continue

        for snicaddr in snicaddrs:
            family = snicaddr.family
            addr = snicaddr.address

            match family:
                # MAC address
                case psutil.AF_LINK:
                    pass

                case socket.AF_INET:
                    if addr != '127.0.0.1':
                        v4_addrs.append(NameAddr(name, addr))

                case socket.AF_INET6:
                    if addr != '::1':
                        v6_addrs.append(NameAddr(name, addr))

    return v4_addrs, v6_addrs


class AppFrame(wx.Frame):
    def __init__(self):
        min_size = wx.Size(600, 600)
        super().__init__(None, title='QRIP', size=min_size)
        self.SetMinSize(min_size)

        notebook = wx.Notebook(self)

        v4_panel = wx.Panel(notebook)
        notebook.AddPage(v4_panel, 'IPv4')
        v4_choice = wx.Choice(v4_panel)
        v4_prompt = wx.StaticText(v4_panel)
        v4_qr = wx.StaticBitmap(v4_panel)

        v6_panel = wx.Panel(notebook)
        notebook.AddPage(v6_panel, 'IPv6')
        v6_choice = wx.Choice(v6_panel)
        v6_prompt = wx.StaticText(v6_panel)
        v6_qr = wx.StaticBitmap(v6_panel)

        about_panel = wx.Panel(notebook)
        notebook.AddPage(about_panel, 'About')

        self.kits = (
            AddrsKit([], v4_choice, v4_prompt, v4_qr),
            AddrsKit([], v6_choice, v6_prompt, v6_qr),
        )
        self.make_addr_page(0, v4_panel)
        self.make_addr_page(1, v6_panel)
        self.make_about_page(about_panel)
        self.refresh_addr()

        # 無論 focus 在哪個子元件，都能捕捉到 refresh hotkey
        # accelerator 其實是模擬觸發 EVT_MENU 事件
        self.Bind(wx.EVT_MENU, lambda _: self.refresh_addr())
        accel_table = wx.AcceleratorTable([
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F5)
        ])
        self.SetAcceleratorTable(accel_table)

    def make_addr_page(self, whichKit: int, panel: wx.Panel):
        _, choice, prompt, qr = self.kits[whichKit]

        vsizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vsizer)

        # hsizer start

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer, flag=wx.EXPAND | wx.ALL, border=10)

        choice.Bind(
            wx.EVT_CHOICE,
            lambda _: self.make_addr_qr(whichKit)
        )
        hsizer.Add(choice, proportion=1, flag=wx.RIGHT, border=10)

        prompt.SetForegroundColour(wx.Colour(255, 255, 255))
        hsizer.Add(prompt)

        # hsizer end

        vsizer.Add(qr, proportion=1)

        refresh_button = wx.Button(panel, label='Refresh (F5)')
        refresh_button.Bind(wx.EVT_BUTTON, lambda _: self.refresh_addr())
        vsizer.Add(refresh_button, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)

    def make_about_page(self, panel: wx.Panel):
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        button = wx.Button(panel, label='GitHub Repo')
        button.Bind(
            wx.EVT_BUTTON,
            lambda _: webbrowser.open('https://github.com/rayliu0712/QRIP')
        )
        sizer.AddStretchSpacer()
        sizer.Add(button, flag=wx.ALIGN_CENTER_HORIZONTAL)
        sizer.AddStretchSpacer()

    def make_addr_qr(self, whichKit: int):
        addrs, choice, _, qr = self.kits[whichKit]

        selection = choice.GetSelection()

        if selection == wx.NOT_FOUND:
            qr.SetBitmap(wx.NullBitmap)
        else:
            buffer = BytesIO()
            qrcode.make(f'QRIP {addrs[selection].addr}').save(buffer)
            buffer.seek(0)
            
            image = wx.Image(buffer)
            bitmap = wx.Bitmap(image)
            qr.SetBitmap(bitmap)

    def refresh_addr(self):
        new_v4_v6_addrs = get_v4_v6_addrs()

        for i in range(2):
            addrs, choice, prompt, _ = self.kits[i]

            addrs.clear()
            addrs.extend(new_v4_v6_addrs[i])

            choice.Clear()
            choice.Append([
                f'{name} ({addr})' for name, addr in addrs
            ])
            choice.SetSelection(0)

            match len(addrs):
                case 0:
                    prompt.SetLabel('   NULL   ')
                    prompt.SetBackgroundColour(wx.Colour(0, 0, 0))
                case 1:
                    prompt.SetLabel('   ONE   ')
                    prompt.SetBackgroundColour(wx.Colour(0, 180, 0))
                case _:
                    prompt.SetLabel('   MANY   ')
                    prompt.SetBackgroundColour(wx.Colour(180, 0, 0))

            prompt.Refresh()
            prompt.Update()

            self.make_addr_qr(i)


if __name__ == '__main__':
    start_QRIP()
