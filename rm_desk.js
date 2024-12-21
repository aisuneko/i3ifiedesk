function closeEmptyDesktops() {
    var windows = workspace.windowList();
    var desktopWindowCount = {};

    windows.forEach(function (window) {
        window.desktops.forEach(function (desktop) {
            desktopNumber = desktop.x11DesktopNumber;
            if (desktopNumber in desktopWindowCount) {
                desktopWindowCount[desktopNumber] += 1;
            } else {
                desktopWindowCount[desktopNumber] = 1;
            }
        })
    });
    for (var num = 1; num <= workspace.desktops.length; num++) {
        if (!(num in desktopWindowCount)) {
            var desktop = workspace.desktops[num - 1];
            if (workspace.currentDesktop != desktop) {
                workspace.removeDesktop(desktop);
            }
        }
    }
}

registerShortcut(
    "Close Empty Desktops",
    "Close Empty Desktops",
    "",
    closeEmptyDesktops
);