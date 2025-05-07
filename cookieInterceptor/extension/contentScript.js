// const script = document.createElement('script');
// script.src = chrome.runtime.getURL('injectedScript.js');
// (document.head || document.documentElement).appendChild(script);

const inject = (scriptName) => {
  const script = document.createElement('script');
  script.src = chrome.runtime.getURL(scriptName);
  (document.head || document.documentElement).appendChild(script);
};

inject('injectedScript.js');
inject('cookieStoreMonitor.js');

// Listen for messages from the injected script and forward them to the background
window.addEventListener('message', event => {
  if (event.source === window && event.data.type === 'cookieAccess') {
    chrome.runtime.sendMessage(event.data);
  }
});