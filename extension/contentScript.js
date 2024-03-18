const scriptEl = document.createElement('script');
scriptEl.src = chrome.runtime.getURL('cookieProtect.js');
(document.head || document.documentElement).appendChild(scriptEl);

// Relay messages from the webpage to the background script
window.addEventListener('message', (event) => {
  if (event.source === window && event.data.type === 'setCookie') {
    chrome.runtime.sendMessage({
      action: "updateCookieDictionary",
      cookieName: event.data.cookieName,
      setterDomain: event.data.setterDomain
    });
  }
});


// Relay messages from the webpage to the background script
window.addEventListener('message', (event) => {
    if (event.source === window && event.data) {
        if(event.data.type === 'getCookieDataset') {
            // Fetch the cookie dataset from the background and send it back to the webpage
            chrome.runtime.sendMessage({type: 'getCookieDataset', visitingDomain: window.location.hostname}, (response) => {
                window.postMessage({type: 'cookieDatasetResponse', cookieDataset: response.cookieDataset}, '*');
            });
        }
    }
});