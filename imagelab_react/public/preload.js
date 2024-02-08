const { ipcRenderer } = require("electron");

process.once("loaded", () => {
  window.ipcRenderer = ipcRenderer;
});
