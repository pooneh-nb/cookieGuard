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

    var cookieGetter = document.__lookupGetter__("cookie").bind(document);
    var cookieSetter = document.__lookupSetter__("cookie").bind(document);

    Object.defineProperty(document, 'cookie', {
        get: function() {

            const callerUrl = getLastCallerUrl();
            const callerURL = callerUrl ? callerUrl : document.location.href;
            const visitingSiteDomain = getBaseDomain(window.location.hostname);
            var storedCookieStr = cookieGetter();
            fetch(`http://localhost:3000/cookieLogs`, {
                method: "POST",
                body: JSON.stringify({
                    "cookie": storedCookieStr,
                    "initiatorURL": callerURL,
                    "visitingDomain": visitingSiteDomain,
                    "action": 'get',
                    "accessType": 'script',
                    "timestamp": performance.now()
                }),
                mode: 'cors',
                headers: {
                    "Content-Type": "application/json"
                }
            }).then(res => {
                console.log("CookieStorage collected");
            });
            return cookieGetter();
        },
        set: function(cookieString) {
            const callerUrl = getLastCallerUrl();
            const callerURL = callerUrl ? callerUrl : document.location.href;
            const  visitingSiteDomain = getBaseDomain(window.location.hostname);
            fetch(`http://localhost:3000/cookieLogs`, {
                method: "POST",
                body: JSON.stringify({
                    "cookie": cookieString,
                    "initiatorURL": callerURL,
                    "visitingDomain": visitingSiteDomain,
                    "action": 'set',
                    "accessType": 'script',
                    "timestamp": performance.now()
                }),
                mode: 'cors',
                headers: {
                    "Content-Type": "application/json"
                }
            }).then(res => {
                console.log("CookieStorage collected");
            });
            return cookieSetter(cookieString);
        },
        configurable: true
    });
})();