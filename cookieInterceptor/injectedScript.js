(function() {
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
        if (partsLength <= 2 || parts.every(part => !isNaN(parseInt(part, 10)))) {
            return hostname;
        }
        if (partsLength > 2) {
            return parts.slice(-2).join('.');
        }
    }

    const originalGet = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').get;
    const originalSet = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').set;

    Object.defineProperty(document, 'cookie', {
        get: function() {
            const originalGet = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').get;
            const allCookies = originalGet.call(document); // Get all cookies as a string
            const cookieArray = allCookies.split('; '); // Split into individual cookies
            const cookies = cookieArray.map(cookie => {
                const parts = cookie.split('=');
                return {name: parts[0], value: parts.slice(1).join('=')}; // Handle cookies with '=' in their value
            });

            const callerUrl = getLastCallerUrl();
            const callerURL = callerUrl ? callerUrl : document.location.href;
            const visitingSiteDomain = window.location.hostname;
            window.postMessage({
                type: 'cookieAccess',
                action: 'get',
                accessType: 'script',
                cookieData: cookies, // Send all current cookies
                accessorURL: callerURL,
                visitingDomain: visitingSiteDomain
            }, "*");
            return originalGet.call(this);
        },
        set: function(value) {
            const callerUrl = getLastCallerUrl();
            const callerURL = callerUrl ? callerUrl : document.location.href;
            const  visitingSiteDomain = window.location.hostname;
            window.postMessage({
                type: 'cookieAccess',
                cookieName: value.split('=')[0].trim(),
                cookieValue: value.split('=')[1] || '',
                accessorURL: callerURL,
                visitingDomain: visitingSiteDomain,
                action: 'set',
                accessType: 'script',
            }, "*");
            originalSet.apply(this, [value]);
        },
        configurable: true
    });
})();