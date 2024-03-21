(function() {
    let cookieDataset = {}; 
    // Helper function to extract hostname from URL
    function getHost(url) {
        if (typeof url !== 'string') return '';
        var a = document.createElement('a');
        a.href = url;
        return a.hostname || '';
    }

    // Function to analyze the stack trace and extract the last caller's URL
    function getLastCallerUrl() {
        var regex = /(https?:\/\/[^\s]+)/g;
        var stack = new Error().stack;
        var urls = stack.match(regex);
        return urls && urls.length ? urls[urls.length - 1] : '';
    }

    function getBaseDomain(url) {
        if (typeof url !== 'string') return '';
        var hostname = getHost(url);
        if (!hostname) return ''; 

        var parts = hostname.split('.');
        var partsLength = parts.length;

        // Check if the hostname could be an IP address or a local hostname
        if (partsLength <=2 || parts.every(part => !isNaN(parseInt(part, 10)))) {
            return hostname;
        }
        // Attempt to construct the base domain by excluding common subdomains
        if (partsLength > 2) {
            // Join the last two parts
            hostname = parts.slice(-2).join('.');
        }
        return hostname;
    }

    window.addEventListener('message', function(event) {
        if (event.data.type === 'cookieDatasetResponse') {
            // const originalGet = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').get;
            // console.log("original", originalGet.call(this.document).split('; ')); 
            cookieDataset = event.data.cookieDataset; 
            // console.log("Cookie dataset:", cookieDataset);
        }
    });

    // Function to preload or update the cookie dataset
    function updateCookieDataset() {
        window.postMessage({ type: 'getCookieDataset' }, '*');
    }

    // Override document.cookie getter
    const originalGet = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').get;
    const originalSet = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').set;

    Object.defineProperty(document, 'cookie', {
        get: function() {
            // console.log("GET REQUEST");
            const callerUrl = getLastCallerUrl();
            const callerDomain = callerUrl ? getBaseDomain(callerUrl) : getBaseDomain(document.domain);
            console.log(callerDomain, "calls getter");
            // console.log("Cookie dataset currently available:", cookieDataset);

            // Use originalGet to get all cookies
            const allCookies = originalGet.call(document).split('; ');
            const filteredCookies = allCookies.filter(cookie => {
                const cookieName = cookie.split('=')[0];
                // Check if the cookie's setter domain matches the caller's domain
                return cookieDataset[cookieName] === callerDomain;
            });
           //  
        //    console.log(allCookies.join('; '));
        //    return allCookies.join('; ');
            // filtered
            console.log(filteredCookies.join('; '));
            return filteredCookies.join('; ');
           
        },
        set: function(value) {
            const callerUrl = getLastCallerUrl();
            // console.log("Caller raw url:", callerUrl);
            const callerDomain = callerUrl ? getBaseDomain(callerUrl) : getBaseDomain(document.domain);
            // console.log(callerDomain, "calls setter");
            window.postMessage({ 
                type: 'setCookie',
                cookieName: value.split('=')[0].trim(),
                setterDomain: callerDomain // Send document's domain as the setter
            }, "*");
            updateCookieDataset();
            originalSet.apply(this, [value]);
        },
        configurable: true
    });    
})();

