import os
import wx
import socket
import psutil
import qrcode
from io import BytesIO
from ipaddress import IPv4Interface, IPv6Interface, IPv4Network, IPv6Network

V4_BLACKLIST = [
    '127.0.0.0/8',
    '169.254.0.0/16'  # link-local address
]

V6_BLACKLIST = [
    '::1',
    'fe80::/10'  # link-local address
]


class AppFrame(wx.Frame):
    def __init__(self):
        min_size = wx.Size(650, 650)
        super().__init__(None, title='QRIP', size=min_size)
        self.SetMinSize(min_size)

        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(sizer)

        notebook = wx.Notebook(panel)
        notebook.AddPage(self.make_v4_page(notebook), 'IPv4')
        notebook.AddPage(self.make_v6_page(notebook), 'IPv6')
        sizer.Add(notebook, proportion=1, flag=wx.EXPAND | wx.ALL, border=10)

        button = wx.Button(panel, label='Refresh (F5)')
        button.Bind(wx.EVT_BUTTON, lambda _: self.refresh_ifs())
        sizer.Add(
            button,
            flag=wx.ALIGN_RIGHT | wx.LEFT | wx.RIGHT | wx.BOTTOM,
            border=10
        )

        #
        # 無論 focus 在哪個子元件，都能捕捉到 refresh hotkey
        # accelerator 其實是模擬觸發 EVT_MENU 事件
        self.Bind(wx.EVT_MENU, lambda _: self.refresh_ifs())
        accel_table = wx.AcceleratorTable([
            wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_F5)
        ])
        self.SetAcceleratorTable(accel_table)

        self.refresh_ifs()

    def make_bitmap(self, data: str) -> wx.Bitmap:
        buffer = BytesIO()
        qrcode.make(f'[QRIP] {data}').save(buffer)
        buffer.seek(0)

        image = wx.Image(buffer)
        return wx.Bitmap(image)

    def make_v4_page(self, notebook: wx.Notebook) -> wx.Panel:
        panel = wx.Panel(notebook)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vsizer)

        #
        # hsizer start

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer, flag=wx.EXPAND | wx.ALL, border=10)

        self.v4_choice = wx.Choice(panel)
        self.v4_choice.Bind(wx.EVT_CHOICE, lambda _: self.make_v4_qr_text())
        hsizer.Add(self.v4_choice, proportion=1)
        hsizer.AddStretchSpacer()

        # hsizer end
        #

        self.v4_qr = wx.StaticBitmap(panel)
        vsizer.Add(self.v4_qr, proportion=1, flag=wx.EXPAND)

        self.v4_text = wx.StaticText(panel)
        vsizer.Add(
            self.v4_text,
            flag=wx.ALIGN_LEFT | wx.LEFT,
            border=10
        )

        return panel

    def make_v6_page(self, notebook: wx.Notebook) -> wx.Panel:
        panel = wx.Panel(notebook)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        panel.SetSizer(vsizer)

        #
        # hsizer start

        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        vsizer.Add(hsizer, flag=wx.EXPAND | wx.ALL, border=10)

        self.v6_choice = wx.Choice(panel)
        self.v6_choice.Bind(wx.EVT_CHOICE, lambda _: self.make_v6_qr_text())
        hsizer.Add(self.v6_choice, proportion=1)
        hsizer.AddStretchSpacer()

        # hsizer end
        #

        self.v6_qr = wx.StaticBitmap(panel)
        vsizer.Add(self.v6_qr, proportion=1, flag=wx.EXPAND)

        self.v6_text = wx.StaticText(panel)
        vsizer.Add(
            self.v6_text,
            flag=wx.ALIGN_LEFT | wx.LEFT,
            border=10
        )

        return panel

    def make_v4_qr_text(self):
        selection = self.v4_choice.GetStringSelection()

        if selection == '':
            self.v4_qr.SetBitmap(wx.NullBitmap)
            self.v4_text.SetLabel('')
        else:
            v4if = self.v4_ifs[selection]
            self.v4_text.SetLabel(str(v4if))

            bitmap = self.make_bitmap(str(v4if.ip))
            self.v4_qr.SetBitmap(bitmap)

    def make_v6_qr_text(self):
        selection = self.v6_choice.GetStringSelection()

        if selection == '':
            self.v6_qr.SetBitmap(wx.NullBitmap)
            self.v6_text.SetLabel('')
        else:
            v6if = self.v6_ifs[selection]
            self.v6_text.SetLabel(str(v6if))

            bitmap = self.make_bitmap(str(v6if.ip))
            self.v6_qr.SetBitmap(bitmap)

    def refresh_ifs(self):
        self.v4_ifs, self.v6_ifs = get_v4_v6_ifs()

        self.v4_choice.Clear()
        self.v4_choice.Append(list(self.v4_ifs.keys()))
        self.v4_choice.SetSelection(0)
        self.make_v4_qr_text()

        self.v6_choice.Clear()
        self.v6_choice.Append(list(self.v6_ifs.keys()))
        self.v6_choice.SetSelection(0)
        self.make_v6_qr_text()


def is_allowed_v4(v4if: IPv4Interface) -> bool:
    return all(not v4if in IPv4Network(addr) for addr in V4_BLACKLIST)


def is_allowed_v6(v6if: IPv6Interface) -> bool:
    return all(not v6if in IPv6Network(addr) for addr in V6_BLACKLIST)


def get_v4_v6_ifs() -> tuple[dict[str, IPv4Interface], dict[str, IPv6Interface]]:
    v4_ifs = {}
    v6_ifs = {}

    net_addrs = psutil.net_if_addrs()
    net_stats = psutil.net_if_stats()

    for name, snicaddr_list in net_addrs.items():

        # disabled
        if not net_stats[name].isup:
            continue

        this_v4s = []
        this_v6s = []

        for family, addr, mask, _, _ in snicaddr_list:

            match family:
                # MAC address
                # case psutil.AF_LINK:
                #     pass

                case socket.AF_INET:
                    v4if = IPv4Interface(f'{addr}/{mask}')
                    if is_allowed_v4(v4if):
                        this_v4s.append(v4if)

                case socket.AF_INET6:
                    v6if = IPv6Interface(f'{addr}/64')
                    if is_allowed_v6(v6if):
                        this_v6s.append(v6if)

        this_v4s_len = len(this_v4s)
        if this_v4s_len == 1:
            v4_ifs[name] = this_v4s[0]
        elif this_v4s_len > 1:
            v4_ifs.update({
                f'{name} ({i+1})': this_v4s[i] for i in range(this_v4s_len)
            })

        this_v6s_len = len(this_v6s)
        if this_v6s_len == 1:
            v6_ifs[name] = this_v6s[0]
        elif this_v6s_len > 1:
            v6_ifs.update({
                f'{name} ({i+1})': this_v6s[i] for i in range(this_v6s_len)
            })

    return v4_ifs, v6_ifs


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
