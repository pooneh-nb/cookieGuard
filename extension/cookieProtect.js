(function() {
    // Helper function to extract hostname from URL
    function getHost(url) {
        var a = document.createElement('a');
        a.href = url;
        return a.hostname;
    }

    // Function to analyze the stack trace and extract the last caller's URL
    function getLastCallerUrl() {
        var regex = /(https?:\/\/[^\s]+)/g;
        var stack = new Error().stack;
        var urls = stack.match(regex);
        return urls ? urls[urls.length - 1] : null;
    }

    window.addEventListener('message', function(event) {
        if (event.data.type === 'cookieDatasetResponse') {
            console.log("Cookie dataset:", event.data.cookieDataset);
        }
    });

    // Override document.cookie getter
    const originalGet = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').get;
    const originalSet = Object.getOwnPropertyDescriptor(Document.prototype, 'cookie').set;

    Object.defineProperty(document, 'cookie', {
        get: function() {
            console.log("GET REQUEST");
            window.postMessage({ type: 'getCookieDataset' }, '*');
            // return originalGet.call(this);
        },
        set: function(value) {
            const callerUrl = getLastCallerUrl();
            const callerDomain = callerUrl ? getHost(callerUrl) : document.domain;
            window.postMessage({ 
                type: 'setCookie',
                cookieName: value.split('=')[0].trim(),
                setterDomain: callerDomain // Send document's domain as the setter
            }, "*");
            originalSet.apply(this, [value]);
        },
        configurable: true
    });    
})();

