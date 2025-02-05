// function to clear cookies and cache
function clearBrowserData(callback) {
    const millisecondsPerWeek = 1000 * 60 * 60 * 24 * 7;  // 1 week
    const oneWeekAgo = (new Date()).getTime() - millisecondsPerWeek;

    // clear cookies
    chrome.browsingData.removeCookies({
        "since": oneWeekAgo
      }, () => {
        console.log('Cookies have been cleared.');
    
        // Clear cache
        chrome.browsingData.removeCache({
          "since": oneWeekAgo
        }, () => {
          console.log('Cache has been cleared.');
          callback();  // Callback after cleaning
        });
      });
    }

    // Listen for when the extension is installed
chrome.runtime.onInstalled.addListener(() => {
    clearBrowserData(() => {
      console.log('Browser data cleared, extension starting its operations.');
    });
});

// Listen for when the browser starts up
chrome.runtime.onStartup.addListener(() => {
    clearBrowserData(() => {
      console.log('Browser data cleared on startup.');
    });
  });

function getBaseDomain(url) {
    try {
        const hostname = new URL(url).hostname;
        const parts = hostname.split('.').reverse();
        if (parts.length > 2) {
            if (parts[1].length === 2 && parts[0].length === 2) {
                return `${parts[2]}.${parts[1]}.${parts[0]}`;
            } else {
                return `${parts[1]}.${parts[0]}`;
            }
        }
        return hostname;
    } catch(e) {
        console.error('Failed to extract base domain:', e.message);
        return '';
    }
}


function parseCookieValue(headerValue) {
    const parts = headerValue.split(';');
    const firstPart = parts.shift();
    const splitValue = firstPart.split('=');
    return {
        name: splitValue[0],
        value: splitValue[1] || '' // Default to empty string if no value
    };
}


function sendData(data) {
    fetch(`http://localhost:3000/cookieLogs`, {
        method: "POST",
        body: JSON.stringify(data),
        mode: 'cors',
        headers: {
            "Content-Type": "application/json"
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => console.log("Response from server:", data))
    .catch(error => console.error("Failed to send data:", error));
}

function logCookieData(data) {
    const logEntry = {
        "cookie": data.cookie,
        "accessorURL": data.accessorURL,
        "visitingDomain": data.visitingDomain,
        "action": data.action,
        "accessType": data.accessType,
        "timestamp": performance.now()
    };

    sendData(logEntry);
}

// Listen to HTTP responses
chrome.webRequest.onHeadersReceived.addListener(
    function(details) {
        // Only consider requests with a valid tab ID and not from service workers or internal chrome processes
        if (details.tabId < 0) return;

        chrome.tabs.get(details.tabId, function(tab) {
            if (chrome.runtime.lastError || !tab) {
                console.error('Error retrieving tab:', chrome.runtime.lastError ? chrome.runtime.lastError.message : 'Tab not found');
                return;
            }

            const visitingDomain = getBaseDomain(tab.url);
            const initiatorDomain = getBaseDomain(details.initiator)
            const responseDomain = getBaseDomain(details.url);

            let isThirdParty = initiatorDomain !== responseDomain;

            if (!isThirdParty) {
                details.responseHeaders.forEach(header => {
                    if (header.name.toLowerCase() === "set-cookie" && !header.value.toLowerCase().includes("httponly")) {
                        const cookieDetails = header.value.split(';')[0].split('='); // Simplified cookie parsing
                        const cookieName = cookieDetails[0];
                        const cookieValue = cookieDetails.slice(1).join('=');
                        
                        logCookieData({
                            cookie: header.value,
                            accessorURL: details.url,
                            visitingDomain: visitingDomain,
                            action: 'set',
                            accessType: 'http',
                        });
                    }
                });
            }
        });
    },
    { urls: ["<all_urls>"] },
    ["responseHeaders", "extraHeaders"]
);

