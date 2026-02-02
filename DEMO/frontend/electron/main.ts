import { app, BrowserWindow } from 'electron';
import path from 'path';

function createWindow() {
    const win = new BrowserWindow({
        width: 1400,
        height: 900,
        titleBarStyle: 'hiddenInset', // Apple-like
        trafficLightPosition: { x: 20, y: 20 },
        vibrancy: 'under-window', // Mac blur effect
        visualEffectState: 'active',
        backgroundColor: '#1e1e1e', // Match body bg
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
        },
    });

    // In dev, load Vite server
    const isDev = !app.isPackaged;
    if (isDev) {
        win.loadURL('http://localhost:5173');
        win.webContents.openDevTools();
    } else {
        win.loadFile(path.join(__dirname, '../dist/index.html'));
    }
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
