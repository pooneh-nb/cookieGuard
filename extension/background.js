function getBaseDomain(url) {
  const hostname = new URL(url).hostname;
  const parts = hostname.split('.').reverse();
  if (parts.length > 2) {
    if (parts[1].length ===2 && parts[0].length ===2) {
      return `${parts[2]}.${parts[1]}.${parts[0]}`;
    } else {
      return `${parts[1]}.${parts[0]}`;
    }
  }
  return hostname;
}

// chrome.webRequest.sender
// listen to http responses
chrome.webRequest.onHeadersReceived.addListener(
  function(details) {
    const firstPartyDomain = getBaseDomain(details.url);
    let isThirdParty = false;
    if (details.initiator) {
        const initiatorDomain = getBaseDomain(details.initiator);
        isThirdParty = initiatorDomain !== firstPartyDomain;
    }

    // Only proceed for first-party responses
    if (!isThirdParty) {
      details.responseHeaders.forEach(header => {
        if (header.name.toLowerCase() === "set-cookie" && !header.value.toLowerCase().includes("HttpOnly")) {
          const cookieName = header.value.split('=')[0].trim();
          // console.log("http", details.url, "calls setter to set", cookieName);
          updateCookieDictionary(cookieName, firstPartyDomain, firstPartyDomain);
        }
      });
    }
  },
  { urls: ["<all_urls>"] },
  ["responseHeaders", "extraHeaders"]
);


// Listener for document.cookie from content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "updateCookieDictionary") {
    // console.log('Received message:', request);
    updateCookieDictionary(request.cookieName, request.setterDomain, request.visitingDomain);
  } else if (request.type === "getCookieDataset") {
    // Fetch and return the entire cookie dataset from storage
    chrome.storage.local.get({cookieDictionary: {}}, function(result) {
      const domainCookies = result.cookieDictionary[request.visitingDomain] || {};
      sendResponse({cookieDataset: domainCookies});
    });
    return true; // Return true to indicate an asynchronous response
}
});


function updateCookieDictionary(cookieName, setterDomain, visitingDomain) {
  // console.log(visitingDomain);
  chrome.storage.local.get({cookieDictionary: {}}, function(data) {
    if (!data.cookieDictionary[visitingDomain]) {
      data.cookieDictionary[visitingDomain] = {}; // Initialize if the domain doesn't exist
    }

    if (!data.cookieDictionary[visitingDomain][cookieName]) {
      // Update only if the cookie name doesn't exist under this domain
      data.cookieDictionary[visitingDomain][cookieName] = setterDomain;
      chrome.storage.local.set({cookieDictionary: data.cookieDictionary});
    } else {
      if (setterDomain != data.cookieDictionary[visitingDomain][cookieName]){
        // console.log(setterDomain, ' attempt overwriting ', cookieName, 'owned by', data.cookieDictionary[visitingDomain][cookieName]);
      }
    }
  });
}



