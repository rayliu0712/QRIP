import os
import wx
import socket
import psutil
import qrcode
import ipaddress
import webbrowser
from io import BytesIO
from typing import NamedTuple

V4_BLACKLIST = [
    '127.0.0.0/8',
    '169.254.0.0/16'  # link-local address
]
V6_BLACKLIST = [
    '::1',
    'fe80::/10'  # link-local address
]


class NameAddr(NamedTuple):
    name: str
    addr: str


class AddrsKit(NamedTuple):
    addrs: list[NameAddr]
    choice: wx.Choice
    prompt: wx.StaticText
    qr: wx.StaticBitmap


class AppFrame(wx.Frame):
    def __init__(self):
        min_size = wx.Size(600, 600)
        super().__init__(None, title='QRIP', size=min_size)
        self.SetMinSize(min_size)

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        #
        # notebook

        notebook = wx.Notebook(panel)
        sizer.Add(notebook, proportion=1, flag=wx.EXPAND)

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

        self.kits = (
            AddrsKit([], v4_choice, v4_prompt, v4_qr),
            AddrsKit([], v6_choice, v6_prompt, v6_qr),
        )
        self.make_addr_page(0, v4_panel)
        self.make_addr_page(1, v6_panel)
        self.refresh_interfaces()

        #
        # refresh button

        refresh_button = wx.Button(panel, label='Refresh (F5)')
        sizer.Add(refresh_button, flag=wx.ALIGN_RIGHT | wx.ALL, border=10)
        refresh_button.Bind(wx.EVT_BUTTON, lambda _: self.refresh_interfaces())

        #
        # status bar

        status_bar = self.CreateStatusBar()
        status_bar.SetStatusText(' © 2025 Ray Liu')

        #
        # 無論 focus 在哪個子元件，都能捕捉到 refresh hotkey
        # accelerator 其實是模擬觸發 EVT_MENU 事件
        self.Bind(wx.EVT_MENU, lambda _: self.refresh_interfaces())
        accel_table = wx.AcceleratorTable([
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F5)
        ])
        self.SetAcceleratorTable(accel_table)

    def make_addr_page(self, whichKit: int, panel: wx.Panel):
        _, choice, prompt, qr = self.kits[whichKit]

        vsizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vsizer)

        # top_hsizer start

        top_hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(top_hsizer, flag=wx.EXPAND | wx.ALL, border=10)

        choice.Bind(
            wx.EVT_CHOICE,
            lambda _: self.make_addr_qr(whichKit)
        )
        top_hsizer.Add(choice, proportion=1, flag=wx.RIGHT, border=10)

        prompt.SetForegroundColour(wx.Colour(255, 255, 255))
        top_hsizer.Add(prompt)

        # top_hsizer end

        vsizer.Add(qr, proportion=1)

    def make_addr_qr(self, whichKit: int):
        addrs, choice, _, qr = self.kits[whichKit]

        selection = choice.GetSelection()

        if selection == wx.NOT_FOUND:
            qr.SetBitmap(wx.NullBitmap)
        else:
            addr = addrs[selection].addr

            # IPv6
            if whichKit == 1:
                addr = f'[{addr}]'

            buffer = BytesIO()
            qrcode.make(f'QRIP {addr}').save(buffer)
            buffer.seek(0)

            image = wx.Image(buffer)
            bitmap = wx.Bitmap(image)
            qr.SetBitmap(bitmap)

    def refresh_interfaces(self):
        new_v4_v6_addrs = get_v4_v6_addrs()

        for i in range(2):
            addrs, choice, prompt, _ = self.kits[i]

            addrs.clear()
            addrs.extend(new_v4_v6_addrs[i])

            choice.Clear()
            choice.Append([
                f'{name} [{addr}]' for name, addr in addrs
            ])
            choice.SetSelection(0)

            match len(addrs):
                case 0:
                    prompt.SetLabel('   NULL   ')
                    prompt.SetBackgroundColour(wx.Colour(0, 0, 0))
                case 1:
                    prompt.SetLabel('   ONLY   ')
                    prompt.SetBackgroundColour(wx.Colour(0, 180, 0))
                case _:
                    prompt.SetLabel('   MANY   ')
                    prompt.SetBackgroundColour(wx.Colour(180, 0, 0))

            prompt.Refresh()
            prompt.Update()

            self.make_addr_qr(i)


def is_ip_in_network(ip_str: str, network_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    network = ipaddress.ip_network(network_str)

    return ip in network


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
                # case psutil.AF_LINK:
                #     pass

                case socket.AF_INET:
                    if all(not is_ip_in_network(addr, network) for network in V4_BLACKLIST):
                        v4_addrs.append(NameAddr(name, addr))

                case socket.AF_INET6:
                    if all(not is_ip_in_network(addr, network) for network in V6_BLACKLIST):
                        v6_addrs.append(NameAddr(name, addr))

    return v4_addrs, v6_addrs


def start_QRIP():
    if os.name == 'nt':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(True)

    app = wx.App()
    appFrame = AppFrame()
    appFrame.Show()
    app.MainLoop()


if __name__ == '__main__':
    start_QRIP()
