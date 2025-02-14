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


// function parseCookieValue(headerValue) {
//     const parts = headerValue.split(';');
//     const firstPart = parts.shift();
//     const splitValue = firstPart.split('=');
//     return {
//         name: splitValue[0],
//         value: splitValue[1] || '' // Default to empty string if no value
//     };
// }


function sendCookieData(data) {
    fetch(`http://localhost:3000/cookieLogs`, {
        method: "POST",
        body: JSON.stringify(data),
        mode: 'cors',
        headers: {
            'Access-Control-Allow-Origin': '*',
            "Content-Type": "application/json"
        }
    }).then(res => {
        console.log("Request complete! response");
    });
    
}

function sendRequestData(data) {
    // console.log("sendRequestData");
    fetch(`http://localhost:3000/requestLogs`, {
        method: "POST",
        body: JSON.stringify(data),
        mode: 'cors',
        headers: {
            'Access-Control-Allow-Origin': '*',
            "Content-Type": "application/json"
        }
    }).then(res => {
        console.log("Request complete! response");
    });
    
}

function logCookieData(data) {
    const logEntry = {
        "cookie": data.cookie,
        "initiatorURL": data.initiatorURL,
        "visitingDomain": data.visitingDomain,
        "action": data.action,
        "accessType": data.accessType,
        "timestamp": performance.now()
    };

    sendCookieData(logEntry);
}

function logRequestData(data) {
    // console.log("logRequestData");
    const logEntry = {
        "initiatorURL": data.initiatorURL,
        "requestURL": data.requestURL,
        "visitingDomain": data.visitingDomain,
        "timestamp": data.timestamp
    };

    sendRequestData(logEntry);
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
                            initiatorURL: details.url,
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

// Listen to when a new tab is created or when a tab is updated
// chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
//     console.log("onUpdated");
//     console.log(changeInfo.url);
//     if (changeInfo.status === 'complete' && !changeInfo.url.startsWith('chrome://')) {
//         console.log("calling attachDebuggerAndLogRequests");
//         attachDebuggerAndLogRequests(tabId);
//     }
// });

chrome.webNavigation.onBeforeNavigate.addListener(function(details) {
    if (!details.url.startsWith('chrome://')) {  // Ensure it's not an internal Chrome page
        // console.log("Preparing to navigate to:", details.url, "with tabId:", details.tabId);
        attachDebuggerAndLogRequests(details.tabId);
    }
}, {url: [{urlMatches: 'https://*/*'}]});  // Optional: Adjust URL filtering as needed


async function attachDebuggerAndLogRequests(tabId) {
    const debuggee = { tabId: tabId };
    try {
        // First, fetch the tab to get the visiting URL
        const tab = await chrome.tabs.get(tabId);
        if (tab.url) {
            const visitingDomain = getBaseDomain(tab.url);
            console.log(visitingDomain);
            await chrome.debugger.attach(debuggee, '1.3');
            await chrome.debugger.sendCommand(debuggee, 'Network.enable', {});

            chrome.debugger.onEvent.addListener((source, method, params) => {
                if (source.tabId === tabId && method === 'Network.requestWillBeSent') {
                    if (params.initiator.type === 'script') {
                        if (params.initiator.stack && params.initiator.stack.callFrames.length > 0 && params.initiator.stack.callFrames[0].url) {
                            // console.log(`Initiator URL: ${params.initiator.stack.callFrames[0].url}`);
                            // console.log(`Initiator type: ${params.initiator.type}`);
                            // console.log(`Request URL: ${params.request.url}`);
                            // console.log(`timestamp: ${params.timestamp}`);
                            logRequestData({
                                initiatorURL: params.initiator.stack.callFrames[0].url,
                                requestURL: params.request.url,
                                visitingDomain: visitingDomain,
                                timestamp: params.timestamp
                            });
                        } else {
                            console.log("No stack trace or call frames available");
                        }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Failed to attach debugger:', error);
    }
}

// handle the debugger detachment, either when done or when the tab closes
chrome.tabs.onRemoved.addListener((tabId, removeInfo) => {
    chrome.debugger.detach({ tabId: tabId }, () => console.log(`Debugger detached from tab ${tabId}`));
});

