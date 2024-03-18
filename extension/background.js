// listen to http responses
chrome.webRequest.onHeadersReceived.addListener(
  function(details) {
    const firstPartyDomain = new URL(details.url).hostname;
    let isThirdParty = false;
    if (details.initiator) {
        const initiatorDomain = new URL(details.initiator).hostname;
        isThirdParty = initiatorDomain !== firstPartyDomain;
    }

    // Only proceed for first-party responses
    if (!isThirdParty) {
      details.responseHeaders.forEach(header => {
        if (header.name.toLowerCase() === "set-cookie" && !header.value.toLowerCase().includes("httponly")) {
          const cookieName = header.value.split('=')[0].trim();
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
  if (request.action === "updateCookieDictionary" && request.cookieName && request.setterDomain, request.visitingDomain) {
    const setterDomain = request.setterDomain;
    // console.log(request.cookieName, setterDomain, )
    updateCookieDictionary(request.cookieName, setterDomain, request.visitingDomain);
  }

  if (request.type === "getCookieDataset"  && request.visitingDomain) {
    // Fetch and return the entire cookie dataset from storage
    chrome.storage.local.get({cookieDictionary: {}}, function(result) {
      const domainCookies = result.cookieDictionary[request.visitingDomain] || {};
      // console.log(domainCookies);
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
    }
  });
}



