/**
 * Jest Test Setup
 * Global test configuration and mocks
 */

// Mock Electron modules
jest.mock('electron', () => ({
  app: {
    getPath: jest.fn((name) => {
      const paths = {
        userData: '/tmp/test-user-data',
        appData: '/tmp/test-app-data',
        temp: '/tmp'
      };
      return paths[name] || '/tmp';
    }),
    getVersion: jest.fn(() => '1.0.0'),
    getName: jest.fn(() => 'happy-place-pos'),
    getAppPath: jest.fn(() => '/app'),
    on: jest.fn(),
    whenReady: jest.fn(() => Promise.resolve()),
    quit: jest.fn(),
    exit: jest.fn()
  },
  ipcMain: {
    handle: jest.fn(),
    on: jest.fn(),
    removeHandler: jest.fn(),
    removeAllListeners: jest.fn()
  },
  ipcRenderer: {
    invoke: jest.fn(),
    on: jest.fn(),
    send: jest.fn(),
    removeListener: jest.fn()
  },
  BrowserWindow: jest.fn(() => ({
    loadURL: jest.fn(),
    on: jest.fn(),
    webContents: {
      send: jest.fn(),
      on: jest.fn(),
      openDevTools: jest.fn(),
      setWindowOpenHandler: jest.fn()
    }
  })),
  session: {
    defaultSession: {
      webRequest: {
        onHeadersReceived: jest.fn(),
        onBeforeRequest: jest.fn(),
        onBeforeSendHeaders: jest.fn()
      },
      setPermissionRequestHandler: jest.fn(),
      setPermissionCheckHandler: jest.fn(),
      protocol: {
        interceptFileProtocol: jest.fn()
      }
    }
  },
  shell: {
    openExternal: jest.fn()
  },
  screen: {
    getPrimaryDisplay: jest.fn(() => ({
      workAreaSize: { width: 1920, height: 1080 }
    }))
  },
  crashReporter: {
    start: jest.fn()
  },
  contextBridge: {
    exposeInMainWorld: jest.fn()
  }
}));

// Mock electron-log
jest.mock('electron-log', () => ({
  transports: {
    file: {
      resolvePathFn: null,
      level: 'info',
      maxSize: 5 * 1024 * 1024,
      format: '[{y}-{m}-{d} {h}:{i}:{s}.{ms}] [{level}] {text}',
      getFile: jest.fn(() => ({ path: '/tmp/test.log' }))
    },
    console: {
      level: 'debug',
      format: '[{h}:{i}:{s}] [{level}] {text}',
      useStyles: true
    }
  },
  info: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  debug: jest.fn()
}));

// Mock electron-updater
jest.mock('electron-updater', () => ({
  autoUpdater: {
    autoDownload: false,
    autoInstallOnAppQuit: true,
    autoRunAppAfterInstall: true,
    channel: 'stable',
    allowDowngrade: false,
    on: jest.fn(),
    checkForUpdates: jest.fn(() => Promise.resolve()),
    downloadUpdate: jest.fn(() => Promise.resolve()),
    quitAndInstall: jest.fn()
  }
}));

// Mock better-sqlite3
jest.mock('better-sqlite3', () => {
  return jest.fn(() => ({
    prepare: jest.fn(() => ({
      run: jest.fn(),
      get: jest.fn(),
      all: jest.fn(() => [])
    })),
    exec: jest.fn(),
    close: jest.fn(),
    transaction: jest.fn((fn) => fn)
  }));
});

// Global test timeout
jest.setTimeout(10000);

// Console suppression for cleaner test output
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn()
};
