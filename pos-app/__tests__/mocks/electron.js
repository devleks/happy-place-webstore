/**
 * Electron Mock for Jest Tests
 * Provides mock implementations of Electron APIs
 */

const electron = {
  app: {
    getPath: jest.fn((name) => {
      if (name === 'userData') return '/mock/user/data';
      return `/mock/${name}`;
    }),
    quit: jest.fn(),
    on: jest.fn(),
  },

  ipcMain: {
    on: jest.fn(),
    handle: jest.fn(),
    removeHandler: jest.fn(),
  },

  ipcRenderer: {
    send: jest.fn(),
    on: jest.fn(),
    invoke: jest.fn(),
    removeAllListeners: jest.fn(),
  },

  BrowserWindow: jest.fn(() => ({
    loadURL: jest.fn(),
    webContents: {
      openDevTools: jest.fn(),
      send: jest.fn(),
    },
    on: jest.fn(),
    show: jest.fn(),
    hide: jest.fn(),
  })),
};

module.exports = electron;
